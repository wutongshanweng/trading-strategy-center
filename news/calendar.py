"""宏观事件日历 — 内置规则化种子事件 + 近 N 天展望。

不依赖外部 API: 用固定发布规律推算未来事件。
- 中国: PMI 每月最后一天、CPI/PPI 每月 9 号、GDP 每季度次月中旬
- 美国: 非农 每月第一个周五、美联储议息 (1/3/5/6/7/9/11/12 月)
"""

from __future__ import annotations

import calendar as _cal
from datetime import date, datetime, timedelta
from typing import Dict, List

# 美联储议息月份 (近似, 每年 8 次)
_FOMC_MONTHS = {1, 3, 5, 6, 7, 9, 11, 12}


def _first_friday(year: int, month: int) -> date:
    d = date(year, month, 1)
    # weekday(): Mon=0 ... Fri=4
    offset = (4 - d.weekday()) % 7
    return d + timedelta(days=offset)


def _last_day(year: int, month: int) -> date:
    return date(year, month, _cal.monthrange(year, month)[1])


def _events_for_month(year: int, month: int) -> List[Dict]:
    evs: List[Dict] = []
    # 中国 PMI — 月末
    evs.append({"date": _last_day(year, month).isoformat(), "country": "中国",
                "event": "制造业PMI", "importance": 3,
                "affects": ["RB", "HC", "CU", "I"]})
    # 中国 CPI/PPI — 每月 9 号
    evs.append({"date": date(year, month, 9).isoformat(), "country": "中国",
                "event": "CPI / PPI", "importance": 3,
                "affects": ["M", "Y", "C", "RB", "CU"]})
    # 美国非农 — 第一个周五
    evs.append({"date": _first_friday(year, month).isoformat(), "country": "美国",
                "event": "非农就业", "importance": 3, "affects": ["AU", "AG", "CU"]})
    # 美联储议息
    if month in _FOMC_MONTHS:
        evs.append({"date": date(year, month, 20).isoformat(), "country": "美国",
                    "event": "美联储议息会议", "importance": 3,
                    "affects": ["AU", "AG", "CU", "SC"]})
    # GDP — 季度次月 (1/4/7/10 月 中旬)
    if month in (1, 4, 7, 10):
        evs.append({"date": date(year, month, 16).isoformat(), "country": "中国",
                    "event": "GDP (季度)", "importance": 3,
                    "affects": ["CU", "RB", "NI"]})
    return evs


class MacroCalendar:
    """宏观事件日历。"""

    def upcoming(self, days: int = 14) -> List[Dict]:
        """返回未来 days 天内的宏观事件 (按日期升序)。"""
        today = datetime.now().date()
        end = today + timedelta(days=days)
        # 覆盖当前月 + 下月, 足够 14 天窗口
        months = {(today.year, today.month),
                  (end.year, end.month)}
        all_events: List[Dict] = []
        for y, m in months:
            all_events.extend(_events_for_month(y, m))
        out = [e for e in all_events
               if today <= date.fromisoformat(e["date"]) <= end]
        out.sort(key=lambda e: e["date"])
        return out
