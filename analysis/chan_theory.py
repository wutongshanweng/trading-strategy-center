from typing import List, Dict
import numpy as np
import pandas as pd
from signals.price_action import pivot_high, pivot_low


def _merge_pivots(pivots):
    if len(pivots) < 2:
        return pivots
    merged = [pivots[0]]
    for p in pivots[1:]:
        if p["type"] == merged[-1]["type"]:
            if p["type"] == "high" and p["high"] > merged[-1]["high"]:
                merged[-1] = p
            elif p["type"] == "low" and p["low"] < merged[-1]["low"]:
                merged[-1] = p
        else:
            merged.append(p)
    return merged


class ChanTheory:
    def __init__(self):
        self.bi_list, self.zhongshu_list = [], []

    def detect_bi(self, df: pd.DataFrame, gap: int = 5):
        if df is None or len(df) < gap + 2:
            return []
        left = right = gap // 2
        pivots = []
        highs = pivot_high(df, left, right)
        lows = pivot_low(df, left, right)
        if highs is not None:
            for idx in highs.index:
                pivots.append({"idx": df.index.get_loc(idx), "type": "high", "high": highs[idx], "time": idx})
        if lows is not None:
            for idx in lows.index:
                pivots.append({"idx": df.index.get_loc(idx), "type": "low", "low": lows[idx], "time": idx})
        pivots.sort(key=lambda x: x["idx"])
        pivots = _merge_pivots(pivots)
        bi_list = []
        for i in range(len(pivots) - 1):
            p1, p2 = pivots[i], pivots[i + 1]
            if p1["type"] != p2["type"] and abs(p2["idx"] - p1["idx"]) + 1 >= gap:
                key = p2["type"]
                bi_list.append({"start_idx": p1["idx"], "end_idx": p2["idx"],
                                 "direction": "up" if p2[key] > p1[p1["type"]] else "down",
                                 "high": max(p1.get("high", p1.get("low")), p2.get("high", p2.get("low"))),
                                 "low": min(p1.get("low", p1.get("high")), p2.get("low", p2.get("high")))})
        self.bi_list = bi_list
        self.detect_zhongshu()
        return bi_list

    def detect_zhongshu(self, bi_list=None):
        bi_list = bi_list or self.bi_list
        self.zhongshu_list = []
        for i in range(len(bi_list) - 2):
            b1, b2, b3 = bi_list[i], bi_list[i + 1], bi_list[i + 2]
            overlap_high, overlap_low = min(b1["high"], b2["high"], b3["high"]), max(b1["low"], b2["low"], b3["low"])
            if overlap_high > overlap_low:
                self.zhongshu_list.append({"top": overlap_high, "bottom": overlap_low,
                                            "bi_indices": (i, i + 1, i + 2)})
        return self.zhongshu_list

    def classify_trend(self, zhongshu_list=None):
        zs = zhongshu_list or self.zhongshu_list
        if len(zs) < 2:
            return "range"
        up, down, max_up, max_down = 0, 0, 0, 0
        for i in range(len(zs) - 1):
            if zs[i + 1]["bottom"] > zs[i]["top"]:
                up += 1; down = 0
            elif zs[i + 1]["top"] < zs[i]["bottom"]:
                down += 1; up = 0
            else:
                up = down = 0
            max_up, max_down = max(max_up, up), max(max_down, down)
        return "bull" if max_up > max_down else "bear" if max_down > max_up else "range"
