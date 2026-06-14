"""
策略锦标赛系统 - Tournament System
Strategy Tournament and Horse Racing Mechanism

功能：
1. 策略竞赛排名
2. 自动晋级机制
3. 赛马资金分配
4. 淘汰和重新优化
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class TournamentStatus(Enum):
    """锦标赛状态"""
    PREPARING = "preparing"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


@dataclass
class TournamentEntry:
    """锦标赛参赛策略"""
    strategy_id: str
    strategy_name: str
    initial_capital: float = 100000.0
    current_capital: float = 100000.0
    rank: int = 0
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    total_trades: int = 0
    status: str = "active"  # active, promoted, eliminated

    # 赛马资金分配
    capital_allocation: float = 0.0

    # 历史表现
    daily_returns: List[float] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)


class StrategyTournament:
    """策略锦标赛系统"""

    def __init__(
        self,
        name: str = "Strategy Tournament",
        duration_days: int = 30,
        initial_capital: float = 100000.0
    ):
        self.name = name
        self.duration_days = duration_days
        self.initial_capital = initial_capital
        self.status = TournamentStatus.PREPARING

        self.participants: List[TournamentEntry] = []
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.current_day: int = 0

        # 晋级和淘汰规则
        self.promotion_rate = 0.1  # 前10%晋级到实盘
        self.elimination_rate = 0.3  # 后30%淘汰

        # 赛马资金分配规则
        self.capital_distribution = {
            1: 0.20,   # 第1名: 20%资金
            2: 0.15,   # 第2名: 15%
            3: 0.12,   # 第3名: 12%
            4: 0.10,   # 第4名: 10%
            5: 0.08,   # 第5名: 8%
        }

        # 历史记录
        self.history: List[Dict] = []

    def add_participant(self, strategy_id: str, strategy_name: str):
        """添加参赛策略"""
        entry = TournamentEntry(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            initial_capital=self.initial_capital,
            current_capital=self.initial_capital,
        )
        self.participants.append(entry)
        print(f"✓ 策略 '{strategy_name}' 已加入锦标赛")

    def start_tournament(self):
        """开始锦标赛"""
        if len(self.participants) < 2:
            raise ValueError("至少需要2个参赛策略")

        self.status = TournamentStatus.RUNNING
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=self.duration_days)
        self.current_day = 0

        print(f"\n{'='*60}")
        print(f"🏆 锦标赛开始: {self.name}")
        print(f"{'='*60}")
        print(f"参赛策略数: {len(self.participants)}")
        print(f"初始资金: ${self.initial_capital:,.0f}")
        print(f"比赛天数: {self.duration_days}天")
        print(f"开始日期: {self.start_date.strftime('%Y-%m-%d')}")
        print(f"{'='*60}\n")

    def simulate_day(self, day: int):
        """
        模拟一天的交易
        实际使用时，这里应该连接真实的策略引擎
        """
        self.current_day = day

        for entry in self.participants:
            if entry.status != "active":
                continue

            # 模拟当天收益率（实际应该从策略回测获取）
            daily_return = np.random.normal(0.001, 0.02)  # 平均0.1%，标准差2%

            # 更新资金
            entry.current_capital *= (1 + daily_return)
            entry.daily_returns.append(daily_return)
            entry.equity_curve.append(entry.current_capital)

            # 模拟交易（实际从策略获取）
            if np.random.random() > 0.7:  # 30%概率有交易
                entry.total_trades += 1

        # 每周更新排名和资金分配
        if day % 7 == 0:
            self.update_rankings()
            self.allocate_capital()

    def update_rankings(self):
        """更新策略排名"""
        # 计算各项指标
        for entry in self.participants:
            if len(entry.daily_returns) == 0:
                continue

            # 总收益率
            entry.total_return = (entry.current_capital - entry.initial_capital) / entry.initial_capital

            # 夏普比率
            if len(entry.daily_returns) > 1:
                returns_std = np.std(entry.daily_returns)
                if returns_std > 0:
                    entry.sharpe_ratio = np.mean(entry.daily_returns) / returns_std * np.sqrt(252)

            # 胜率（简化计算）
            if entry.total_trades > 0:
                winning_days = sum(1 for r in entry.daily_returns if r > 0)
                entry.win_rate = winning_days / len(entry.daily_returns)

            # 最大回撤
            if len(entry.equity_curve) > 0:
                equity = np.array(entry.equity_curve)
                cummax = np.maximum.accumulate(equity)
                drawdown = (equity - cummax) / cummax
                entry.max_drawdown = drawdown.min()

        # 按夏普比率排名（也可以用其他指标）
        self.participants.sort(key=lambda x: x.sharpe_ratio, reverse=True)

        # 更新排名
        for i, entry in enumerate(self.participants, 1):
            entry.rank = i

    def allocate_capital(self):
        """赛马资金分配"""
        total_allocation = 1.0
        allocated = 0.0

        # 前几名按规则分配
        for entry in self.participants:
            if entry.rank in self.capital_distribution:
                entry.capital_allocation = self.capital_distribution[entry.rank]
                allocated += entry.capital_allocation

        # 其余策略平分剩余资金
        remaining = total_allocation - allocated
        remaining_count = len(self.participants) - len(self.capital_distribution)

        if remaining_count > 0:
            per_strategy = remaining / remaining_count
            for entry in self.participants:
                if entry.rank not in self.capital_distribution:
                    entry.capital_allocation = per_strategy

    def check_promotion_elimination(self):
        """检查晋级和淘汰"""
        n_participants = len([e for e in self.participants if e.status == "active"])

        # 晋级数量
        n_promotion = max(1, int(n_participants * self.promotion_rate))
        # 淘汰数量
        n_elimination = max(1, int(n_participants * self.elimination_rate))

        promoted = []
        eliminated = []

        for i, entry in enumerate(self.participants):
            if entry.status != "active":
                continue

            # 前10%晋级
            if i < n_promotion:
                entry.status = "promoted"
                promoted.append(entry)

            # 后30%淘汰
            elif i >= n_participants - n_elimination:
                entry.status = "eliminated"
                eliminated.append(entry)

        return promoted, eliminated

    def run_tournament(self, verbose: bool = True):
        """
        运行完整锦标赛

        Args:
            verbose: 是否打印详细过程
        """
        self.start_tournament()

        for day in range(1, self.duration_days + 1):
            self.simulate_day(day)

            if verbose and day % 7 == 0:
                print(f"\n第{day}天排行榜:")
                self.print_leaderboard(top_n=10)

        # 锦标赛结束
        self.status = TournamentStatus.FINISHED

        # 最终排名和晋级淘汰
        self.update_rankings()
        promoted, eliminated = self.check_promotion_elimination()

        print(f"\n{'='*60}")
        print(f"🏆 锦标赛结束！")
        print(f"{'='*60}")

        print(f"\n🎯 晋级到实盘 ({len(promoted)}个):")
        for entry in promoted:
            print(f"  {entry.rank}. {entry.strategy_name}")
            print(f"     收益率: {entry.total_return*100:.2f}% | 夏普: {entry.sharpe_ratio:.2f}")

        print(f"\n❌ 淘汰策略 ({len(eliminated)}个):")
        for entry in eliminated:
            print(f"  {entry.rank}. {entry.strategy_name}")
            print(f"     收益率: {entry.total_return*100:.2f}% | 夏普: {entry.sharpe_ratio:.2f}")

        # 保存历史
        self.save_results()

        return promoted, eliminated

    def print_leaderboard(self, top_n: int = 10):
        """打印排行榜"""
        print(f"\n{'排名':<6}{'策略名称':<20}{'收益率':<12}{'夏普':<8}{'胜率':<8}{'资金占比':<10}")
        print("-" * 70)

        for i, entry in enumerate(self.participants[:top_n], 1):
            print(
                f"{entry.rank:<6}"
                f"{entry.strategy_name:<20}"
                f"{entry.total_return*100:>10.2f}%  "
                f"{entry.sharpe_ratio:>6.2f}  "
                f"{entry.win_rate*100:>6.1f}%  "
                f"{entry.capital_allocation*100:>8.1f}%"
            )

    def get_leaderboard(self, top_n: Optional[int] = None) -> List[Dict]:
        """获取排行榜数据"""
        entries = self.participants[:top_n] if top_n else self.participants

        return [
            {
                "rank": entry.rank,
                "strategy_id": entry.strategy_id,
                "strategy_name": entry.strategy_name,
                "total_return": entry.total_return,
                "sharpe_ratio": entry.sharpe_ratio,
                "win_rate": entry.win_rate,
                "max_drawdown": entry.max_drawdown,
                "total_trades": entry.total_trades,
                "capital_allocation": entry.capital_allocation,
                "status": entry.status,
            }
            for entry in entries
        ]

    def save_results(self, filepath: str = "tournament_results.json"):
        """保存锦标赛结果"""
        results = {
            "tournament_name": self.name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "duration_days": self.duration_days,
            "participants": len(self.participants),
            "leaderboard": self.get_leaderboard(),
        }

        Path(filepath).write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"\n✓ 结果已保存: {filepath}")


# API路由
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/tournament", tags=["tournament"])

# 全局锦标赛实例
active_tournament: Optional[StrategyTournament] = None


class CreateTournamentRequest(BaseModel):
    name: str
    duration_days: int = 30
    strategy_ids: List[str]


@router.post("/create")
async def create_tournament(request: CreateTournamentRequest):
    """创建新锦标赛"""
    global active_tournament

    tournament = StrategyTournament(
        name=request.name,
        duration_days=request.duration_days,
    )

    # 添加策略
    for strategy_id in request.strategy_ids:
        tournament.add_participant(strategy_id, f"Strategy_{strategy_id}")

    active_tournament = tournament

    return {
        "status": "success",
        "tournament_name": tournament.name,
        "participants": len(tournament.participants),
    }


@router.post("/start")
async def start_tournament():
    """开始锦标赛"""
    if not active_tournament:
        raise HTTPException(status_code=404, detail="No active tournament")

    active_tournament.start_tournament()

    return {
        "status": "success",
        "message": "Tournament started",
        "start_date": active_tournament.start_date.isoformat(),
    }


@router.get("/leaderboard")
async def get_leaderboard(top_n: Optional[int] = None):
    """获取排行榜"""
    if not active_tournament:
        raise HTTPException(status_code=404, detail="No active tournament")

    return {
        "tournament_name": active_tournament.name,
        "status": active_tournament.status.value,
        "current_day": active_tournament.current_day,
        "leaderboard": active_tournament.get_leaderboard(top_n),
    }


@router.get("/status")
async def get_tournament_status():
    """获取锦标赛状态"""
    if not active_tournament:
        return {"status": "no_active_tournament"}

    return {
        "status": active_tournament.status.value,
        "name": active_tournament.name,
        "participants": len(active_tournament.participants),
        "current_day": active_tournament.current_day,
        "duration_days": active_tournament.duration_days,
    }
