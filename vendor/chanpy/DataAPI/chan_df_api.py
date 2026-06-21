"""自定义 DataAPI — 从内存 DataFrame 喂给 chan.py。

通过 data_src="custom:chan_df_api.ChanDFApi" 动态加载。
DataFrame 由 analysis/chan_pro.py 注册到 _DF_REGISTRY (code 即注册 key)。
"""

import pandas as pd

from Common.CEnum import DATA_FIELD, KL_TYPE
from Common.CTime import CTime
from KLine.KLine_Unit import CKLine_Unit

from .CommonStockAPI import CCommonStockApi


def _to_ctime(ts) -> CTime:
    t = pd.Timestamp(ts)
    return CTime(t.year, t.month, t.day, t.hour, t.minute)


class ChanDFApi(CCommonStockApi):
    def __init__(self, code, k_type=KL_TYPE.K_DAY, begin_date=None, end_date=None, autype=None):
        super(ChanDFApi, self).__init__(code, k_type, begin_date, end_date, autype)

    def get_kl_data(self):
        # 延迟导入避免循环 (analysis 包在项目根)
        from analysis.chan_pro import get_registered_df
        df = get_registered_df(self.code)
        if df is None or df.empty:
            return
        for ts, row in df.iterrows():
            item = {
                DATA_FIELD.FIELD_TIME: _to_ctime(ts),
                DATA_FIELD.FIELD_OPEN: float(row["open"]),
                DATA_FIELD.FIELD_HIGH: float(row["high"]),
                DATA_FIELD.FIELD_LOW: float(row["low"]),
                DATA_FIELD.FIELD_CLOSE: float(row["close"]),
            }
            yield CKLine_Unit(item, autofix=True)

    def SetBasciInfo(self):
        pass

    @classmethod
    def do_init(cls):
        pass

    @classmethod
    def do_close(cls):
        pass
