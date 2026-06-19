"""
全因子研究报告生成器。

一键对全因子库执行: 计算 -> IC/ICIR 评估 -> 分层 -> 衰减检测 -> 冗余分析 ->
行业中性化对比 -> 推荐低相关组合 -> 输出 HTML/JSON/控制台。

复用既有: research.factor_lab.FactorAnalyzer (IC/分层),
          core.alpha.factor_combiner.FactorCombiner (组合),
          本包 factor_decay / industry_neutral。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger

from .factor_decay import FactorDecayDetector, FactorHealth
from .industry_neutral import IndustryNeutralizer


@dataclass
class FactorRanking:
    rank: int
    name: str
    ic_mean: float
    icir: float
    sharpe_q5q1: float
    turnover: float
    health: str
    is_recommended: bool = False


@dataclass
class FactorResearchReport:
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    total_factors: int = 0
    healthy_count: int = 0
    warning_count: int = 0
    decayed_count: int = 0
    top_factors: List[FactorRanking] = field(default_factory=list)
    recommended: List[str] = field(default_factory=list)
    recommended_ic: float = 0.0
    recommended_icir: float = 0.0
    high_correlation_pairs: List[Tuple[str, str, float]] = field(default_factory=list)
    industry_exposure_before: float = 0.0
    industry_exposure_after: float = 0.0


class FactorReportGenerator:
    """全因子研究报告生成器。"""

    def __init__(self, analyzer=None, decay_detector=None, neutralizer=None):
        # analyzer: research.factor_lab.factor_analyzer.FactorAnalyzer (惰性导入避免循环)
        if analyzer is None:
            from research.factor_lab.factor_analyzer import FactorAnalyzer
            analyzer = FactorAnalyzer()
        self.analyzer = analyzer
        self.decay_detector = decay_detector or FactorDecayDetector()
        self.neutralizer = neutralizer or IndustryNeutralizer()

    def generate(
        self,
        factors_df: pd.DataFrame,
        forward_returns: pd.Series,
        industry_labels: Optional[pd.Series] = None,
        top_n: int = 20,
        n_quantiles: int = 5,
        corr_threshold: float = 0.85,
        max_recommend: int = 10,
        max_combo_corr: float = 0.7,
    ) -> FactorResearchReport:
        """全因子研究流程。factors_df: 列=因子名, 行=标的/时间; forward_returns 对齐。"""
        rep = FactorResearchReport(total_factors=len(factors_df.columns))
        if factors_df.empty or forward_returns.empty:
            return rep

        rankings = self._rank(factors_df, forward_returns, n_quantiles)
        # 健康分布
        for r in rankings:
            if r.health == FactorHealth.HEALTHY.value:
                rep.healthy_count += 1
            elif r.health == FactorHealth.WARNING.value:
                rep.warning_count += 1
            else:
                rep.decayed_count += 1

        rep.top_factors = rankings[:top_n]
        rep.high_correlation_pairs = self._redundancy(factors_df, corr_threshold)
        rec = self._recommend(rankings, factors_df, max_recommend, max_combo_corr)
        rep.recommended = [r.name for r in rec]
        for r in rankings:
            r.is_recommended = r.name in rep.recommended
        if rec:
            rep.recommended_ic = round(float(np.mean([r.ic_mean for r in rec])), 4)
            rep.recommended_icir = round(float(np.mean([r.icir for r in rec])), 4)

        # 行业中性化效果对比 (取首个因子示例)
        if industry_labels is not None and len(factors_df.columns):
            col = factors_df.columns[0]
            fv = factors_df[col].dropna()
            rep.industry_exposure_before = round(
                self.neutralizer.max_industry_exposure(fv, industry_labels), 4)
            neu = self.neutralizer.neutralize_by_mean(fv, industry_labels)
            rep.industry_exposure_after = round(
                self.neutralizer.max_industry_exposure(neu, industry_labels), 4)
        return rep

    def _rank(self, factors_df, forward_returns, n_quantiles) -> List[FactorRanking]:
        rows = []
        for name in factors_df.columns:
            fv = factors_df[name]
            ic = self.analyzer.calculate_ic(fv, forward_returns, "spearman")
            ic = 0.0 if (ic is None or np.isnan(ic)) else float(ic)
            # ICIR 用滚动 IC 近似 (单截面无时间序列时退化为 0)
            icir = self._quick_icir(fv, forward_returns)
            layered = self.analyzer.layered_backtest(fv, forward_returns, n_quantiles)
            ls = layered.get("long_short", {})
            sharpe = float(ls.get("sharpe", 0.0)) if ls else 0.0
            turnover = float(fv.diff().abs().mean()) if len(fv) > 1 else 0.0
            ic_series = self._rolling_ic(fv, forward_returns)
            health = self.decay_detector.check(name, ic_series, fv, forward_returns,
                                               n_quantiles).health.value
            rows.append(FactorRanking(0, name, round(ic, 4), round(icir, 4),
                                      round(sharpe, 4), round(turnover, 6), health))
        rows.sort(key=lambda r: abs(r.ic_mean), reverse=True)
        for i, r in enumerate(rows, 1):
            r.rank = i
        return rows

    @staticmethod
    def _rolling_ic(fv: pd.Series, ret: pd.Series, win: int = 20) -> pd.Series:
        common = fv.index.intersection(ret.index)
        f, r = fv.loc[common], ret.loc[common]
        return f.rolling(win, min_periods=max(5, win // 2)).corr(r)

    def _quick_icir(self, fv: pd.Series, ret: pd.Series) -> float:
        ic_s = self._rolling_ic(fv, ret).dropna()
        if len(ic_s) < 2 or ic_s.std() == 0:
            return 0.0
        return float(ic_s.mean() / ic_s.std())

    @staticmethod
    def _redundancy(factors_df, threshold) -> List[Tuple[str, str, float]]:
        corr = factors_df.corr().abs()
        pairs = []
        cols = list(corr.columns)
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                v = corr.iloc[i, j]
                if pd.notna(v) and v >= threshold:
                    pairs.append((cols[i], cols[j], round(float(v), 3)))
        return pairs

    @staticmethod
    def _recommend(rankings, factors_df, max_n, max_corr) -> List[FactorRanking]:
        """从排名高到低贪心选, 保证与已选因子相关性 < max_corr。"""
        corr = factors_df.corr().abs()
        picked: List[FactorRanking] = []
        for r in rankings:
            if r.health == FactorHealth.DECAYED.value:
                continue
            if r.name not in corr.columns:
                continue
            ok = True
            for p in picked:
                if p.name in corr.columns and pd.notna(corr.loc[r.name, p.name]) \
                        and corr.loc[r.name, p.name] >= max_corr:
                    ok = False
                    break
            if ok:
                picked.append(r)
            if len(picked) >= max_n:
                break
        return picked

    # ---- 输出 ----
    def save_json(self, report: FactorResearchReport, path: str) -> None:
        d = asdict(report)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"因子报告 JSON 已写入 {path}")

    def to_dict(self, report: FactorResearchReport) -> dict:
        return asdict(report)

    def save_html(self, report: FactorResearchReport, path: str) -> None:
        rows = "".join(
            f"<tr><td>{r.rank}</td><td>{r.name}</td><td>{r.ic_mean}</td>"
            f"<td>{r.icir}</td><td>{r.sharpe_q5q1}</td><td>{r.turnover}</td>"
            f"<td>{r.health}</td><td>{'★' if r.is_recommended else ''}</td></tr>"
            for r in report.top_factors)
        html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>因子研究报告</title><style>
body{{font-family:system-ui,Arial;margin:24px;color:#222}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:6px 10px;font-size:13px}}
th{{background:#f5f5f5}}.kpi{{display:inline-block;margin-right:24px}}</style></head><body>
<h2>因子研究报告 <small>{report.generated_at[:19]}</small></h2>
<div><span class="kpi">总因子 {report.total_factors}</span>
<span class="kpi" style="color:#52c41a">健康 {report.healthy_count}</span>
<span class="kpi" style="color:#faad14">警告 {report.warning_count}</span>
<span class="kpi" style="color:#ff4d4f">失效 {report.decayed_count}</span></div>
<p>推荐组合 ({len(report.recommended)}): {', '.join(report.recommended)}
IC={report.recommended_ic} ICIR={report.recommended_icir}</p>
<p>行业暴露 中性化前 {report.industry_exposure_before} → 后 {report.industry_exposure_after}</p>
<h3>因子排名 Top {len(report.top_factors)}</h3>
<table><tr><th>#</th><th>因子</th><th>IC</th><th>ICIR</th><th>多空Sharpe</th>
<th>换手</th><th>健康</th><th>荐</th></tr>{rows}</table>
<h3>高相关冗余对 (|corr|≥0.85)</h3>
<p>{'; '.join(f'{a}~{b}:{c}' for a,b,c in report.high_correlation_pairs) or '无'}</p>
</body></html>"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"因子报告 HTML 已写入 {path}")

    def print_summary(self, report: FactorResearchReport) -> None:
        print(f"\n{'='*60}\n  因子研究报告 — {report.generated_at[:10]}\n{'='*60}")
        print(f"  总因子 {report.total_factors} | 健康 {report.healthy_count} "
              f"| 警告 {report.warning_count} | 失效 {report.decayed_count}\n")
        for f in report.top_factors[:5]:
            flag = "★" if f.is_recommended else "  "
            print(f"  {flag} #{f.rank:2d} {f.name:18s} IC={f.ic_mean:+.4f} "
                  f"ICIR={f.icir:+.2f} {f.health}")
        print(f"\n  推荐组合 IC={report.recommended_ic} ICIR={report.recommended_icir}\n{'='*60}")
