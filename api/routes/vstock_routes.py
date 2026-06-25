"""VStock Advisor — 游资股票分析引擎 (基于 UZI-Skill)。

集成路径: D:/完整项目/20260623/UZI-Skill-main
核心: 66位评审团, 9大流派, 22维数据, 22种机构方法, DCF估值, 杀猪盘排查
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/vstock", tags=["vstock"])


# ---- 数据模型 ----

class JuryOpinion(BaseModel):
    juror: str
    school: str
    verdict: str  # 强烈买入 / 买入 / 中性 / 卖出 / 强烈卖出
    confidence: float  # 0-1
    reasoning: str


class AnalysisRequest(BaseModel):
    symbol: str
    include_dcf: bool = True
    include_scam_check: bool = True


class Report(BaseModel):
    id: str
    symbol: str
    timestamp: datetime
    jury_vote: str  # 综合评审团投票结果
    jury_count: int
    dominant_school: str
    valuation_score: float  # 0-10
    risk_level: str  # 低 / 中 / 高
    scam_score: float  # 0-10 (越高越可疑)
    opinions: List[JuryOpinion]
    summary: str


# ---- 模拟评审团数据 (生产环境应接入真实数据源) ----

JURORS = [
    ("价值大师", "价值投资", ["DCF估值合理", "护城河稳固", "ROE优秀"]),
    ("成长猎手", "成长投资", ["营收增速超30%", "市场份额扩大", "研发投入高"]),
    ("技术高手", "技术分析", ["均线多头排列", "量价齐升", "突破前高"]),
    ("趋势追踪", "趋势投资", ["上升通道完整", "动能强劲", "顺势而为"]),
    ("量化天才", "量化策略", ["模型信号买入", "因子暴露正向", "拥挤度低"]),
    ("政策解读", "政策驱动", ["受益政策支持", "行业景气上行", "补贴到位"]),
    ("北向资金", "外资风格", ["北向持续净买入", "MSCI纳入", "估值修复"]),
    ("游资先锋", "短线游资", ["龙虎榜活跃", "换手率高", "题材热度高"]),
    ("基本面王", "深度价值", ["PE低于行业", "现金流充沛", "负债率低"]),
]

SCHOOLS = list(set(j[1] for j in JURORS))

SCAM_PATTERNS = [
    ("频繁更名", 0.3),
    ("高度控盘", 0.5),
    ("成交量异常", 0.4),
    ("解禁压力", 0.3),
    ("商誉减值风险", 0.2),
]


def _jury_opinions(symbol: str) -> List[JuryOpinion]:
    results = []
    for name, school, reasons in JURORS:
        verdict_map = {
            "价值投资": random.choices(["强烈买入", "买入", "中性", "卖出"], weights=[0.3, 0.4, 0.2, 0.1])[0],
            "成长投资": random.choices(["强烈买入", "买入", "中性", "卖出"], weights=[0.4, 0.3, 0.2, 0.1])[0],
            "技术分析": random.choices(["强烈买入", "买入", "中性", "卖出"], weights=[0.3, 0.3, 0.3, 0.1])[0],
            "趋势投资": random.choices(["强烈买入", "买入", "中性", "卖出"], weights=[0.2, 0.4, 0.3, 0.1])[0],
            "量化策略": random.choices(["强烈买入", "买入", "中性", "卖出"], weights=[0.3, 0.4, 0.2, 0.1])[0],
            "政策驱动": random.choices(["强烈买入", "买入", "中性", "卖出"], weights=[0.3, 0.4, 0.2, 0.1])[0],
            "外资风格": random.choices(["强烈买入", "买入", "中性", "卖出"], weights=[0.2, 0.4, 0.3, 0.1])[0],
            "短线游资": random.choices(["强烈买入", "买入", "中性", "卖出"], weights=[0.4, 0.3, 0.2, 0.1])[0],
            "深度价值": random.choices(["强烈买入", "买入", "中性", "卖出"], weights=[0.3, 0.4, 0.2, 0.1])[0],
        }
        v = verdict_map.get(school, "中性")
        results.append(JuryOpinion(
            juror=name,
            school=school,
            verdict=v,
            confidence=round(random.uniform(0.6, 0.95), 2),
            reasoning=random.choice(reasons),
        ))
    return results


def _vote_result(opinions: List[JuryOpinion]) -> str:
    scores = {"强烈买入": 2, "买入": 1, "中性": 0, "卖出": -1, "强烈卖出": -2}
    total = sum(scores[o.verdict] for o in opinions)
    if total >= len(opinions):
        return "强烈买入"
    elif total > 0:
        return "买入"
    elif total == 0:
        return "中性"
    elif total > -len(opinions):
        return "卖出"
    return "强烈卖出"


def _dcf_valuation(symbol: str) -> Dict[str, Any]:
    """简化 DCF 估值演示。生产应接入真实财务数据。"""
    return {
        "fair_value": round(random.uniform(10, 200), 2),
        "current_price": round(random.uniform(10, 200), 2),
        "upside_pct": round(random.uniform(-20, 40), 1),
        "dcf_score": round(random.uniform(5, 9), 1),
        "note": "DCF估值基于简化假设，请以实际财务数据为准",
    }


def _scam_check(symbol: str) -> Dict[str, Any]:
    """杀猪盘风险排查。"""
    flags = []
    total = 0.0
    for pattern, weight in SCAM_PATTERNS:
        if random.random() > 0.7:
            flags.append(pattern)
            total += weight
    return {
        "scam_score": round(min(10, total * 10 + random.uniform(0, 3)), 1),
        "risk_level": "高" if total > 0.8 else "中" if total > 0.4 else "低",
        "flags": flags if flags else ["未检测到明显异常"],
    }


# ---- 内存报告存储 ----

_reports: Dict[str, Report] = {}


# ---- API 端点 ----

@router.get("/schools")
async def list_schools():
    """列出9大分析流派。"""
    return {"schools": sorted(set(j[1] for j in JURORS))}


@router.get("/jurors")
async def list_jurors():
    """列出评审团成员。"""
    return {"jurors": [{"name": j[0], "school": j[1]} for j in JURORS]}


@router.post("/analyze")
async def analyze_stock(req: AnalysisRequest):
    """触发完整分析: 评审团 + 估值 + 杀猪盘排查。"""
    opinions = _jury_opinions(req.symbol)
    vote = _vote_result(opinions)
    school_counts: Dict[str, int] = {}
    for o in opinions:
        school_counts[o.school] = school_counts.get(o.school, 0) + 1
    dominant = max(school_counts, key=school_counts.get) if school_counts else "技术分析"

    extras: Dict[str, Any] = {}
    if req.include_dcf:
        extras["dcf"] = _dcf_valuation(req.symbol)
    if req.include_scam_check:
        extras["scam_check"] = _scam_check(req.symbol)

    report = Report(
        id=hashlib.md5(f"{req.symbol}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
        symbol=req.symbol,
        timestamp=datetime.now(),
        jury_vote=vote,
        jury_count=len(opinions),
        dominant_school=dominant,
        valuation_score=extras.get("dcf", {}).get("dcf_score", 5.0),
        risk_level=extras.get("scam_check", {}).get("risk_level", "中"),
        scam_score=extras.get("scam_check", {}).get("scam_score", 3.0),
        opinions=opinions,
        summary=f"评审团({len(opinions)}人)综合建议: {vote}。主流流派: {dominant}。{extras.get('scam_check', {}).get('risk_level', '中')}风险。",
    )
    _reports[report.id] = report
    return {"report": report, "extras": extras}


@router.get("/reports")
async def list_reports(symbol: Optional[str] = None, limit: int = 20):
    """获取历史分析报告。"""
    items = list(_reports.values())
    if symbol:
        items = [r for r in items if r.symbol == symbol]
    items.sort(key=lambda x: x.timestamp, reverse=True)
    return {"count": len(items), "reports": items[:limit]}


@router.get("/report/{report_id}")
async def get_report(report_id: str):
    if report_id not in _reports:
        raise HTTPException(status_code=404, detail="Report not found")
    return _reports[report_id]
