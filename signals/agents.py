"""多 agent 交易决策委员会 — 几个 agent 各看一个维度, 主席加权裁决。

agent 角色 (每个产出 方向 + 置信度 + 理由):
  - 技术面 (technical): 55 策略 + 共振引擎 ResonanceEngineV2
  - 因子面 (factor):   FactorAdvisor 对 alpha 因子建议
  - 机器学习 (ml):     特征管道 + MLSignalAdapter
  - 宏观消息 (macro):  RegimeAdapter 联动 + 新闻情绪 (按品种)
  - 缠论   (chan):     chan_bsp 专业买卖点

主席 (chairman): 把各 agent 意见归一化 (BUY=+1/SELL=-1/HOLD=0), 按权重加权,
得到综合方向 + 置信度 + 评星; 可选 LLM 生成自然语言裁决理由 (无 key 降级)。

设计: 复用全部已有部件, 不重写底层。每个 agent 容错独立, 单个失败不影响其他。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

# agent 权重 (主席加权用; 技术面/共振权重最高, 消息面辅助)
# 更新后: 基本面 agent 占 25% (与技术面对等权重)
AGENT_WEIGHTS = {
    "technical": 0.25,
    "factor": 0.10,
    "ml": 0.15,
    "chan": 0.10,
    "macro": 0.10,
    "fundamental": 0.25,  # 基本面 agent: 库存×成本链×季节性×需求
}
_DIR_VAL = {"BUY": 1.0, "SELL": -1.0, "HOLD": 0.0, "WATCH": 0.0}


@dataclass
class AgentOpinion:
    name: str            # technical/factor/ml/macro/chan
    name_cn: str
    direction: str       # BUY / SELL / HOLD / WATCH / N/A
    confidence: float    # 0~1
    reason: str
    detail: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"name": self.name, "name_cn": self.name_cn, "direction": self.direction,
                "confidence": round(self.confidence, 3), "reason": self.reason,
                "detail": self.detail}


class TradingCommittee:
    """多 agent 交易决策委员会。"""

    def __init__(self):
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from signals.engine import StrategyEngine
            eng = StrategyEngine()
            eng.load_all()
            self._engine = eng
        return self._engine

    # ---- 各 agent ----
    def _agent_technical(self, df: pd.DataFrame, contract: str) -> Optional[AgentOpinion]:
        """技术面: 55 策略 + 共振引擎。"""
        try:
            signals = self._get_engine().compute_all(df, symbol=contract)
            if not signals:
                return AgentOpinion("technical", "技术面", "HOLD", 0.0, "无策略信号触发")
            from core.resonance.engine_v2 import ResonanceEngineV2
            reso = ResonanceEngineV2().calculate(contract, signals, regime="RANGING")
            buys = sum(1 for s in signals if s.direction == "BUY")
            sells = sum(1 for s in signals if s.direction == "SELL")
            direction = reso.direction if reso.direction != "HOLD" else (
                "BUY" if buys > sells else "SELL" if sells > buys else "HOLD")
            return AgentOpinion(
                "technical", "技术面", direction, round(reso.confidence, 3),
                f"{len(signals)}个策略触发(多{buys}/空{sells}), 共振值{reso.final_score:.2f}",
                {"final_score": round(reso.final_score, 3),
                 "score_G": round(reso.score_G, 3), "score_C": round(reso.score_C, 3),
                 "score_T": round(reso.score_T, 3), "n_signals": len(signals)})
        except Exception as e:
            logger.warning(f"[committee] technical agent failed: {e}")
            return None

    def _agent_factor(self, df: pd.DataFrame, contract: str) -> Optional[AgentOpinion]:
        """因子面: 用近期收益代理因子信号, FactorAdvisor 裁决。"""
        try:
            from core.alpha.factor_advisor import FactorAdvisor
            # 用收益率序列作为 combined_signal 代理 (真实环境接因子库 combined signal)
            rets = df["close"].pct_change().dropna().tail(20)
            if rets.empty:
                return AgentOpinion("factor", "因子面", "HOLD", 0.0, "无足够数据")
            adv = FactorAdvisor().advise(
                symbol=contract, combined_signal=rets,
                icir=0.6, factor_count=10,
                top_factors=[], health_distribution={"healthy": 8, "warning": 2, "decayed": 0})
            return AgentOpinion(
                "factor", "因子面", adv.action, round(adv.confidence_score, 3),
                adv.reason or f"因子综合 {adv.action_cn}",
                {"action_cn": adv.action_cn, "signal_value": round(adv.signal_value, 4)})
        except Exception as e:
            logger.warning(f"[committee] factor agent failed: {e}")
            return None

    def _agent_ml(self, df: pd.DataFrame, contract: str) -> Optional[AgentOpinion]:
        """机器学习: 技术特征 → MLSignalAdapter 综合信号。"""
        try:
            if len(df) < 60:
                return AgentOpinion("ml", "机器学习", "HOLD", 0.0, "样本不足(<60)")
            from ml.features.pipeline import FeaturePipeline
            from ml.features.technical_features import TechnicalFeatureSet
            from ml.signal_adapter import MLSignalAdapter
            pipe = FeaturePipeline()
            pipe.register_module(TechnicalFeatureSet())
            X = pipe.compute_all(df)
            sig = MLSignalAdapter().to_combined_signal(X, symbol=contract)
            if sig is None:
                return AgentOpinion("ml", "机器学习", "HOLD", 0.0, "ML 信号弱(<阈值), 中性")
            return AgentOpinion(
                "ml", "机器学习", sig.direction.value, round(sig.confidence, 3),
                sig.reason or "ML 集成信号", {"score": round(sig.score, 4)})
        except Exception as e:
            logger.warning(f"[committee] ml agent failed: {e}")
            return None

    def _agent_chan(self, df: pd.DataFrame, contract: str) -> Optional[AgentOpinion]:
        """缠论: chan_pro 专业买卖点。"""
        try:
            from analysis.chan_pro import get_engine
            res = get_engine().latest_signal(df, contract)
            d = res.get("direction", "HOLD")
            conf = 0.7 if d in ("BUY", "SELL") else 0.0
            return AgentOpinion("chan", "缠论", d, conf, res.get("reason", "无买卖点"),
                                {"bsp_type": res.get("bsp_type"), "n_zs": res.get("n_zs")})
        except Exception as e:
            logger.warning(f"[committee] chan agent failed: {e}")
            return None

    def _agent_macro(self, product: str, news_items: Optional[List[Dict]]) -> Optional[AgentOpinion]:
        """宏观消息面: 该品种宏观倾向 + 新闻情绪。"""
        try:
            from core.config.watchlist import linkage_for_product
            link = linkage_for_product(product)  # {指标: 关联度}
            # 新闻情绪 (该品种)
            senti, n_news = 0.0, 0
            if news_items:
                hits = [n for n in news_items if product.upper() in n.get("products", [])]
                if hits:
                    senti = sum(n.get("sentiment_score", 0.0) for n in hits) / len(hits)
                    n_news = len(hits)
            # 综合: 新闻情绪为主导方向 (宏观关联度作背景, 不直接定方向)
            if senti > 0.15:
                direction, conf = "BUY", min(0.6, abs(senti))
            elif senti < -0.15:
                direction, conf = "SELL", min(0.6, abs(senti))
            else:
                direction, conf = "HOLD", 0.0
            reason = (f"{n_news}条相关新闻情绪{senti:+.2f}" if n_news
                      else "无相关新闻") + (f", 宏观敏感: {','.join(link.keys())}" if link else "")
            return AgentOpinion("macro", "宏观消息", direction, conf, reason,
                                {"news_sentiment": round(senti, 3), "n_news": n_news,
                                 "macro_linkage": link})
        except Exception as e:
            logger.warning(f"[committee] macro agent failed: {e}")
            return None

    def _agent_fundamental(self, contract: str) -> Optional[AgentOpinion]:
        """基本面 agent: 库存 × 成本链 × 季节性 × 需求 四维评分。"""
        try:
            from analysis.fundamental.model import analyze_fundamental
            res = analyze_fundamental(contract)
            score = res["score"]
            direction = res["direction"]
            confidence = res["confidence"]
            detail = res["detail"]

            # 提取四维分用于 reason
            scores = detail.get("scores", {})
            inv = scores.get("inventory", 0)
            cst = scores.get("cost", 0)
            sea = scores.get("seasonal", 0)
            dem = scores.get("demand", 0)

            reason = (f"基本面综合{score:+.2f}({direction}): "
                      f"库存{inv:+.2f}/成本{cst:+.2f}/季节{sea:+.2f}/需求{dem:+.2f}")

            return AgentOpinion(
                "fundamental", "基本面", direction, confidence, reason,
                {
                    "scores": scores,
                    "inventory": detail.get("details", {}).get("inventory", ""),
                    "cost": detail.get("details", {}).get("cost", ""),
                    "seasonal": detail.get("details", {}).get("seasonal", ""),
                    "demand": detail.get("details", {}).get("demand", ""),
                    "data_quality": detail.get("data_quality", "medium"),
                    "explanation": detail.get("explanation", ""),
                },
            )
        except Exception as e:
            logger.warning(f"[committee] fundamental agent failed: {e}")
            return None

    # ---- 主席裁决 ----
    def deliberate(self, df: pd.DataFrame, contract: str, product: str,
                   news_items: Optional[List[Dict]] = None,
                   use_llm: bool = False) -> Dict:
        """召集委员会, 各 agent 发表意见, 主席加权裁决。"""
        opinions: List[AgentOpinion] = []
        for fn, args in (
            (self._agent_technical, (df, contract)),
            (self._agent_factor, (df, contract)),
            (self._agent_ml, (df, contract)),
            (self._agent_chan, (df, contract)),
        ):
            op = fn(*args)
            if op:
                opinions.append(op)
        macro_op = self._agent_macro(product, news_items)
        if macro_op:
            opinions.append(macro_op)
        # 基本面 agent
        fundamental_op = self._agent_fundamental(contract)
        if fundamental_op:
            opinions.append(fundamental_op)

        # 加权投票: sum(w * dir_val * conf)
        weighted, total_w = 0.0, 0.0
        for op in opinions:
            w = AGENT_WEIGHTS.get(op.name, 0.1)
            weighted += w * _DIR_VAL.get(op.direction, 0.0) * op.confidence
            total_w += w
        net = weighted / total_w if total_w else 0.0   # [-1, 1]

        if net > 0.12:
            direction = "BUY"
        elif net < -0.12:
            direction = "SELL"
        else:
            direction = "WATCH"

        # 一致性: 同向 agent 占比
        same = sum(1 for op in opinions if op.direction == direction and direction in ("BUY", "SELL"))
        n_voting = sum(1 for op in opinions if op.direction in ("BUY", "SELL"))
        agreement = same / n_voting if n_voting else 0.0
        confidence = round(min(1.0, abs(net) * 1.5), 3)
        star = max(1, min(5, round(1 + abs(net) * 3 + agreement * 1)))

        verdict = {
            "direction": direction, "net_score": round(net, 3),
            "confidence": confidence, "star_rating": star,
            "agreement": round(agreement, 2),
            "agents": [op.to_dict() for op in opinions],
            "n_agents": len(opinions),
        }

        # 可选 LLM 自然语言裁决
        if use_llm:
            try:
                from core.llm.strategy_advisor import LLMStrategyAdvisor
                summary = "; ".join(f"{op.name_cn}:{op.direction}({op.confidence:.2f})" for op in opinions)
                q = f"{product} 各分析维度: {summary}。综合方向 {direction}。请给一句话决策点评。"
                verdict["llm_comment"] = LLMStrategyAdvisor().ask(q, {"regime": "trending"})
            except Exception as e:
                logger.warning(f"[committee] llm arbiter failed: {e}")

        return verdict


_committee: Optional[TradingCommittee] = None


def get_committee() -> TradingCommittee:
    global _committee
    if _committee is None:
        _committee = TradingCommittee()
    return _committee
