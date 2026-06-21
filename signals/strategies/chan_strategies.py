"""缠论买卖点策略 — 接入专业版 chan.py 引擎 (analysis/chan_pro)。

作为新信号源加入 54 策略体系, 产出的信号经共振引擎参与综合决策。
买卖点类型→置信度: 一买/卖(1) 最强, 三买/卖(3a/3b) 次之, 类买卖/盘整背驰(2s/1p) 再次。
"""

import pandas as pd
from signals.base import BaseStrategy, Signal, Direction
from signals.registry import register

# 买卖点类型置信度权重
_BSP_CONF = {
    "1": 0.85, "1p": 0.6, "2": 0.7, "2s": 0.5,
    "3a": 0.65, "3b": 0.6,
}


def _conf_for(type_str: str) -> float:
    if not type_str:
        return 0.5
    types = type_str.split(",")
    return max((_BSP_CONF.get(t.strip(), 0.5) for t in types), default=0.5)


@register
class ChanBSP(BaseStrategy):
    name = "chan_bsp"
    description = "缠论买卖点 (专业版: 一/二/三买卖+盘整背驰)"
    timeframes = ["1d", "4h", "1h"]
    params = {"recent_bars": 5}  # 仅当买卖点落在最近 N 根内才触发

    def compute(self, df: pd.DataFrame, symbol: str = "") -> Signal | None:
        if df is None or len(df) < 60:
            return None
        from analysis.chan_pro import get_engine
        res = get_engine().compute_bsp(df, symbol)
        if res.get("error") or not res.get("bsp"):
            return None

        last_bsp = res["bsp"][-1]
        # 仅在买卖点足够新时才作为信号 (避免历史买卖点反复触发)
        recent = max(1, int(self.params.get("recent_bars", 5)))
        bsp_time = str(last_bsp["time"])
        recent_times = {str(pd.Timestamp(t)).split(" ")[0].replace("-", "/")
                        for t in df.index[-recent:]}
        # chan 时间格式 YYYY/MM/DD; 宽松匹配 (只比对日期部分)
        bsp_date = bsp_time.split(" ")[0]
        if not any(bsp_date in rt or rt in bsp_date for rt in recent_times):
            return None

        close = float(df["close"].iloc[-1])
        conf = _conf_for(last_bsp["type_str"])
        if last_bsp["is_buy"]:
            return Signal(symbol=symbol, direction=Direction.BUY, confidence=conf,
                          price=close, reason=f"缠论{last_bsp['type_str']}买点 (中枢{res['n_zs']})",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(close * 0.96), take_profit=float(close * 1.08),
                          extra={"bsp_type": last_bsp["type_str"], "n_zs": res["n_zs"],
                                 "n_bi": res["n_bi"], "n_seg": res["n_seg"]})
        else:
            return Signal(symbol=symbol, direction=Direction.SELL, confidence=conf,
                          price=close, reason=f"缠论{last_bsp['type_str']}卖点 (中枢{res['n_zs']})",
                          strategy_name=self.name, timeframe=self.timeframes[0],
                          stop_loss=float(close * 1.04), take_profit=float(close * 0.92),
                          extra={"bsp_type": last_bsp["type_str"], "n_zs": res["n_zs"],
                                 "n_bi": res["n_bi"], "n_seg": res["n_seg"]})
