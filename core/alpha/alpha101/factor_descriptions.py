"""
Alpha 101 因子中文描述字典。

每个条目包含:
  - chinese_name: 中文名 (简明)
  - formula: 计算公式 (口语化伪代码, 用户可理解)
  - interpretation: 值高/值低分别意味着什么 (两行, 用 \\n 分隔)
  - use_case: 适合什么场景
  - signal_logic: (可选) 信号方向逻辑

用法:
    from core.alpha.alpha101.factor_descriptions import get_description
    desc = get_description("alpha001")
    print(desc["chinese_name"])  # "价格动量-高峰位置"

数据来源: 依据各因子真实 WorldQuant 公式与 category 人工撰写。
"""

from typing import Dict, Optional

ALPHA101_DESCRIPTIONS: Dict[str, dict] = {
    "alpha001": {
        "chinese_name": "价格动量-高峰位置",
        "formula": "对过去5天内价格最高点出现的时间位置打分, 越近值越高",
        "interpretation": "值高: 价格高点出现在最近 → 上涨势头强劲, 短期可能继续\n"
                          "值低: 价格高点出现在较远 → 上涨动力减弱",
        "use_case": "识别短期上涨趋势的持续性",
        "signal_logic": "值高 → 做多; 值低 → 做空 (动量延续)",
    },
    "alpha002": {
        "chinese_name": "量价相关性-背离反转",
        "formula": "成交量变化与当日涨跌幅的相关系数, 取负 (背离时为正)",
        "interpretation": "值高: 价涨量缩或价跌量增 → 量价背离, 趋势可能反转\n"
                          "值低: 价量同步 → 趋势健康延续",
        "use_case": "识别趋势背离/反转信号",
        "signal_logic": "值高 → 警惕反转; 值低 → 趋势可信",
    },
    "alpha003": {
        "chinese_name": "开盘-成交量负相关",
        "formula": "过去10天开盘价排名与成交量排名的相关系数, 取负",
        "interpretation": "值高: 开盘走高时放量不明显 → 上涨缺量配合\n"
                          "值低: 开盘与成交量同向 → 量价配合良好",
        "use_case": "验证开盘方向是否有量能支撑",
    },
    "alpha004": {
        "chinese_name": "低价区间-时序排名",
        "formula": "当前最低价在过去9天里的相对高低排名, 取负",
        "interpretation": "值高: 近期最低价相对偏低 → 处于支撑区, 关注反弹\n"
                          "值低: 近期最低价偏高 → 价格重心抬升",
        "use_case": "判断价格在近期低点区间的位置",
    },
    "alpha005": {
        "chinese_name": "开盘-均价偏离",
        "formula": "开盘价相对过去10天VWAP均价的偏离, 结合收盘与VWAP的距离",
        "interpretation": "值高: 开盘显著高于均价但收盘回落 → 开盘透支\n"
                          "值低: 开盘低于均价 → 开盘偏弱可能低估",
        "use_case": "判断开盘是否透支或低估",
    },
    "alpha006": {
        "chinese_name": "开盘-成交量相关",
        "formula": "过去10天开盘价与成交量的相关系数, 取负",
        "interpretation": "值高: 开盘与放量背离 → 趋势可能转弱\n"
                          "值低: 开盘与成交量同步 → 趋势延续",
        "use_case": "判断开盘方向与量能是否一致",
    },
    "alpha007": {
        "chinese_name": "放量-价格变动强度",
        "formula": "当成交量超过20日均量时, 取近期收盘变动幅度的时序排名(反向)",
        "interpretation": "值高: 放量但价格变动收敛 → 趋势承压\n"
                          "值低: 放量伴随大幅价格变动 → 趋势强势",
        "use_case": "结合量能验证价格变动的强度",
    },
    "alpha008": {
        "chinese_name": "开盘-收益乘积动量",
        "formula": "过去5天开盘价与收益乘积, 与10天前的同一乘积之差, 取负排名",
        "interpretation": "值高: 近期开盘×收益动量低于过去 → 动量衰减\n"
                          "值低: 近期动量高于过去 → 动量增强",
        "use_case": "捕捉中期动量的变化趋势",
    },
    "alpha009": {
        "chinese_name": "短期价格变动-条件趋势",
        "formula": "若近5天日变动持续为正/负则顺势, 否则反向取日变动",
        "interpretation": "值高: 近期日涨幅持续为正 → 短期上升趋势\n"
                          "值低: 近期日跌幅持续 → 短期下降趋势",
        "use_case": "捕捉短期趋势方向的条件信号",
    },
    "alpha010": {
        "chinese_name": "日变动-条件趋势排名",
        "formula": "alpha009 的排名版本, 对近4天日变动做条件判断后排名",
        "interpretation": "值高: 近期上涨趋势在横截面中靠前\n"
                          "值低: 近期下跌趋势靠前",
        "use_case": "捕捉短期趋势方向 (横截面相对强弱)",
    },
    "alpha011": {
        "chinese_name": "日内强弱-极值排名",
        "formula": "过去5天(收盘-开盘)/开盘的最大与最小排名之和",
        "interpretation": "值高: 近期日内多次收强于开 → 买盘占优\n"
                          "值低: 近期日内收弱于开 → 卖盘占优",
        "use_case": "衡量日内买卖力量的强弱",
    },
    "alpha012": {
        "chinese_name": "开高低收-四价位差",
        "formula": "(开盘排名-最高排名)与(最低排名-收盘排名)的加权",
        "interpretation": "值高: 开盘偏强、收盘偏弱 → 冲高回落特征\n"
                          "值低: 开盘偏弱、收盘偏强 → 探底回升特征",
        "use_case": "捕捉日内冲高回落 / 探底回升形态",
    },
    "alpha013": {
        "chinese_name": "高低收量-综合变动",
        "formula": "高/低/收/量的日变动排名的综合平均",
        "interpretation": "值高: 价量同步走强 → 多头动能聚集\n"
                          "值低: 价量同步走弱 → 空头动能聚集",
        "use_case": "综合价量四要素的短期动能",
    },
    "alpha014": {
        "chinese_name": "最高-成交量负相关",
        "formula": "过去5天最高价排名与成交量排名相关系数, 取负",
        "interpretation": "值高: 创新高时量能不足 → 上涨乏力\n"
                          "值低: 创新高伴随放量 → 上涨健康",
        "use_case": "验证创新高的量能支撑",
    },
    "alpha015": {
        "chinese_name": "收盘-成交量负相关",
        "formula": "过去3天收盘价排名与成交量排名相关系数, 取负",
        "interpretation": "值高: 收盘走高时量能背离 → 趋势承压\n"
                          "值低: 收盘与成交量同步 → 趋势可信",
        "use_case": "短周期量价配合度检验",
    },
    "alpha016": {
        "chinese_name": "最高-成交量负相关(短)",
        "formula": "过去3天最高价排名与成交量排名相关系数, 取负",
        "interpretation": "值高: 短期创高量能不足 → 警惕回落\n"
                          "值低: 短期创高放量 → 上涨有力",
        "use_case": "超短周期创高量能检验",
    },
    "alpha017": {
        "chinese_name": "最低-成交量负相关",
        "formula": "过去5天最低价排名与成交量排名相关系数, 取负",
        "interpretation": "值高: 探底时量能背离 → 下跌或趋缓\n"
                          "值低: 探底放量 → 抛压沉重",
        "use_case": "探底过程的量能检验",
    },
    "alpha018": {
        "chinese_name": "开盘-成交量瞬时相关",
        "formula": "开盘价与成交量的1日相关系数, 取负",
        "interpretation": "值高: 开盘与量能瞬时背离 → 方向存疑\n"
                          "值低: 开盘与量能同步 → 方向明确",
        "use_case": "开盘瞬时量价一致性",
    },
    "alpha019": {
        "chinese_name": "中期收益-反转动量",
        "formula": "近7日与14日价格变化的符号(反向)乘以年收益排名权重",
        "interpretation": "值高: 中期跌幅大且长期收益低 → 超跌反弹潜力\n"
                          "值低: 中期涨幅大 → 高位回落风险",
        "use_case": "中期超跌/超涨反转判断",
    },
    "alpha020": {
        "chinese_name": "开高-量能相关差",
        "formula": "开盘量相关(反向)与最高量相关的平均",
        "interpretation": "值高: 量价结构偏多 → 上行倾向\n"
                          "值低: 量价结构偏空 → 下行倾向",
        "use_case": "开盘与最高价的量能结构对比",
    },
    "alpha021": {
        "chinese_name": "收盘趋势-量价斜率",
        "formula": "收盘价60日回归斜率 + 收盘量10日相关",
        "interpretation": "值高: 长期上行斜率 + 量价配合 → 趋势稳健向上\n"
                          "值低: 斜率向下或量价背离 → 趋势转弱",
        "use_case": "中长期趋势稳健性判断",
    },
    "alpha022": {
        "chinese_name": "高量相关-变动乘积",
        "formula": "最高量相关的6日变动 × 收盘排名变动, 取负",
        "interpretation": "值高: 量价相关性下降伴随价格变动 → 趋势松动\n"
                          "值低: 量价相关稳定 → 趋势延续",
        "use_case": "量价相关性变化捕捉趋势拐点",
    },
    "alpha023": {
        "chinese_name": "高位回落-条件做空",
        "formula": "当价格高于20日均高时, 取最高价2日变动的负值, 否则0",
        "interpretation": "值高: 仅在高位且最高价回落时触发 → 高位转弱\n"
                          "值低/零: 未到高位或仍在走强",
        "use_case": "高位回落的条件性做空信号",
    },
    "alpha024": {
        "chinese_name": "均线突破-条件动量",
        "formula": "依据价格相对100日均线位置, 切换动量或反转逻辑",
        "interpretation": "值高: 价格上穿长期均线 → 趋势转多\n"
                          "值低: 价格跌破长期均线 → 趋势转空",
        "use_case": "长期均线突破的趋势切换",
    },
    "alpha025": {
        "chinese_name": "收益-量能加权排名",
        "formula": "近5日收益率与成交量乘积的负向排名",
        "interpretation": "值高: 放量下跌后 → 超跌反弹倾向\n"
                          "值低: 放量上涨后 → 高位回落倾向",
        "use_case": "量能加权的短期反转",
    },
    "alpha026": {
        "chinese_name": "收盘-成交量负相关(5日)",
        "formula": "过去5天收盘价排名与成交量排名相关系数, 取负",
        "interpretation": "值高: 收盘走高量能背离 → 上涨乏力\n"
                          "值低: 收盘与量能同步 → 上涨健康",
        "use_case": "5日周期量价配合检验",
    },
    "alpha027": {
        "chinese_name": "量价相关-条件反转",
        "formula": "若量价相关排名偏高则取收盘变动反向, 否则取正",
        "interpretation": "值高: 量价高度相关后 → 反转做空倾向\n"
                          "值低: 量价相关弱 → 维持原方向",
        "use_case": "基于量价相关强度的反转",
    },
    "alpha028": {
        "chinese_name": "价格区间-标准化位置",
        "formula": "收盘价在过去100日高低区间内的归一化位置",
        "interpretation": "值高: 价格接近100日高点 → 强势\n"
                          "值低: 价格接近100日低点 → 弱势",
        "use_case": "长周期价格位置 (类似随机指标)",
    },
    "alpha029": {
        "chinese_name": "收盘-量价复合排名",
        "formula": "收盘反向排名 + 量价相关的二重排名",
        "interpretation": "值高: 价格偏低且量价相关靠前 → 潜在反弹\n"
                          "值低: 价格偏高 → 回落风险",
        "use_case": "复合排名的反转倾向",
    },
    "alpha030": {
        "chinese_name": "最高-成交量负相关(3日)",
        "formula": "过去3天最高价排名与成交量排名相关系数, 取负",
        "interpretation": "值高: 短期创高量能背离 → 警惕回落\n"
                          "值低: 短期创高放量 → 上涨有力",
        "use_case": "超短周期创高量能检验",
    },
    "alpha031": {
        "chinese_name": "收盘衰减-量价复合",
        "formula": "收盘10日变动的衰减排名 + 3日变动反向 + 量低相关符号",
        "interpretation": "值高: 价格变动趋缓且量价偏多 → 趋势企稳\n"
                          "值低: 价格快速下行 → 趋势走弱",
        "use_case": "多重时间维度的趋势复合判断",
    },
    "alpha032": {
        "chinese_name": "均价回归-VWAP相关",
        "formula": "7日均价偏离 + VWAP与5日前收盘的长周期相关",
        "interpretation": "值高: 价格低于均价且VWAP长期相关强 → 回归上行\n"
                          "值低: 价格高于均价 → 回归下行",
        "use_case": "均值回归 + VWAP趋势确认",
    },
    "alpha033": {
        "chinese_name": "开收比-反向排名",
        "formula": "1-(开盘/收盘) 的负向排名",
        "interpretation": "值高: 收盘显著高于开盘 → 当日强势\n"
                          "值低: 收盘低于开盘 → 当日弱势",
        "use_case": "当日收开强弱的横截面排名",
    },
    "alpha034": {
        "chinese_name": "波动比-动量复合",
        "formula": "(收益2日/5日波动比)反向 + 收盘1日变动反向, 求和排名",
        "interpretation": "值高: 近期波动收窄且未大涨 → 蓄势\n"
                          "值低: 近期波动放大或刚大涨 → 不稳定",
        "use_case": "波动率与动量的稳定性复合",
    },
    "alpha035": {
        "chinese_name": "量能-价位-收益三重",
        "formula": "成交量时序排名 ×(1-价位排名)×(1-收益排名)",
        "interpretation": "值高: 放量、价位不高、收益不高 → 低位放量蓄势\n"
                          "值低: 缩量或高位高收益 → 动能透支",
        "use_case": "低位放量的潜在启动",
    },
    "alpha036": {
        "chinese_name": "多因子综合信号",
        "formula": "量价相关/开收差/滞后收益/VWAP相关/均线偏离的加权组合",
        "interpretation": "值高: 多个分项共振偏多 → 综合看多\n"
                          "值低: 多个分项偏空 → 综合看空",
        "use_case": "综合多个子信号的复合多空判断",
    },
    "alpha037": {
        "chinese_name": "开收差-滞后相关",
        "formula": "滞后开收差与收盘的200日相关 + 当日开收差排名",
        "interpretation": "值高: 历史开收结构与价格正相关 → 结构延续\n"
                          "值低: 结构背离 → 可能转向",
        "use_case": "长周期开收结构的延续性",
    },
    "alpha038": {
        "chinese_name": "收盘排名-收开比",
        "formula": "收盘10日时序排名反向 × 收开比排名",
        "interpretation": "值高: 收盘相对低位且收强于开 → 低位转强\n"
                          "值低: 收盘高位 → 高位风险",
        "use_case": "收盘位置与日内强弱结合",
    },
    "alpha039": {
        "chinese_name": "收盘变动-量能衰减",
        "formula": "收盘7日变动×(1-量能衰减排名), 取负, 乘年收益排名",
        "interpretation": "值高: 价格下行且放量衰减 → 超跌倾向\n"
                          "值低: 价格上行放量 → 高位风险",
        "use_case": "量能衰减加权的反转",
    },
    "alpha040": {
        "chinese_name": "高价波动-量能相关",
        "formula": "最高价10日波动率反向排名 × 高量相关",
        "interpretation": "值高: 高价波动小且量价正相关 → 平稳上行\n"
                          "值低: 高价波动大 → 不稳定",
        "use_case": "高价稳定性与量能配合",
    },
    "alpha041": {
        "chinese_name": "几何中价-VWAP差",
        "formula": "(最高×最低)的平方根 - VWAP",
        "interpretation": "值高: 几何中价高于VWAP → 价格重心偏高\n"
                          "值低: 几何中价低于VWAP → 价格重心偏低",
        "use_case": "价格重心相对成交均价的偏离",
    },
    "alpha042": {
        "chinese_name": "VWAP偏离-比值排名",
        "formula": "(VWAP-收盘)排名 / (VWAP+收盘)排名",
        "interpretation": "值高: 收盘低于VWAP明显 → 日内弱于均价\n"
                          "值低: 收盘高于VWAP → 日内强于均价",
        "use_case": "收盘相对成交均价的强弱",
    },
    "alpha043": {
        "chinese_name": "量比-收盘变动排名",
        "formula": "量/20日均量的时序排名 × 收盘7日变动反向时序排名",
        "interpretation": "值高: 放量且价格下行 → 超跌反弹倾向\n"
                          "值低: 缩量或价格上行 → 动能不足",
        "use_case": "放量下跌后的反弹捕捉",
    },
    "alpha044": {
        "chinese_name": "最高-量能负相关",
        "formula": "最高价与成交量排名的5日相关, 取负",
        "interpretation": "值高: 创高量能背离 → 上涨乏力\n"
                          "值低: 创高放量 → 上涨健康",
        "use_case": "创高量能检验",
    },
    "alpha045": {
        "chinese_name": "收盘均值-量价相关",
        "formula": "滞后收盘均值排名 × 收盘量相关 × 收盘求和相关, 取负",
        "interpretation": "值高: 量价结构偏空 → 下行倾向\n"
                          "值低: 量价结构偏多 → 上行倾向",
        "use_case": "复合量价相关的方向判断",
    },
    "alpha046": {
        "chinese_name": "斜率比较-条件反转",
        "formula": "比较近10日与前10日价格斜率, 条件触发反转",
        "interpretation": "值高: 价格加速上行后 → 反向回落预期\n"
                          "值低: 价格加速下行后 → 反向反弹预期",
        "use_case": "斜率变化的条件反转",
    },
    "alpha047": {
        "chinese_name": "量能-高价复合",
        "formula": "(1/收盘量比)×高价排名/均高 - VWAP变动排名",
        "interpretation": "值高: 低价放量且高价强 → 潜在突破\n"
                          "值低: VWAP快速上行 → 透支",
        "use_case": "量能与高价结构的突破信号",
    },
    "alpha048": {
        "chinese_name": "行业中性化动量",
        "formula": "收盘变动相关性除以波动 (简化的行业中性动量)",
        "interpretation": "值高: 剔除共性后仍有正动量 → 个体强势\n"
                          "值低: 个体弱于共性 → 相对弱势",
        "use_case": "剔除市场共性的相对动量",
    },
    "alpha049": {
        "chinese_name": "斜率阈值-条件反转",
        "formula": "当价格斜率跌破阈值时触发反向, 否则取负变动",
        "interpretation": "值高: 急跌触发 → 反弹预期\n"
                          "值低: 正常下行 → 顺势",
        "use_case": "急跌后的条件反弹",
    },
    "alpha050": {
        "chinese_name": "量价相关-极值反转",
        "formula": "量与VWAP排名相关的5日最大值, 取负",
        "interpretation": "值高: 量价相关曾极高后 → 回落倾向\n"
                          "值低: 量价相关平稳 → 维持",
        "use_case": "量价相关极值后的反转",
    },
    "alpha051": {
        "chinese_name": "斜率阈值-条件反转(强)",
        "formula": "alpha049 的更严格阈值版本",
        "interpretation": "值高: 更急跌触发 → 强反弹预期\n"
                          "值低: 正常下行 → 顺势",
        "use_case": "急跌后的强条件反弹",
    },
    "alpha052": {
        "chinese_name": "低点动量-收益结构",
        "formula": "最低价5日变动 × 长短期收益差排名 × 量能时序排名",
        "interpretation": "值高: 低点抬升且收益结构改善放量 → 启动\n"
                          "值低: 低点下移 → 走弱",
        "use_case": "低点抬升的启动信号",
    },
    "alpha053": {
        "chinese_name": "日内位置-变动反向",
        "formula": "((收-低)-(高-收))/(收-低) 的9日变动, 取负",
        "interpretation": "值高: 收盘位置由强转弱 → 日内动能减弱\n"
                          "值低: 收盘位置由弱转强 → 日内动能增强",
        "use_case": "日内收盘位置的动能变化",
    },
    "alpha054": {
        "chinese_name": "价格结构-开收幂次",
        "formula": "(低-收)×开^5 / ((低-高)×收^5), 取负",
        "interpretation": "值高: 收盘靠近最高 → 当日强势\n"
                          "值低: 收盘靠近最低 → 当日弱势",
        "use_case": "当日收盘在区间内的强弱(放大)",
    },
    "alpha055": {
        "chinese_name": "随机位置-量能相关",
        "formula": "收盘在12日区间位置排名与量能排名相关, 取负",
        "interpretation": "值高: 价格位置与量能背离 → 趋势承压\n"
                          "值低: 位置与量能同步 → 趋势可信",
        "use_case": "随机指标位置的量能验证",
    },
    "alpha056": {
        "chinese_name": "收益复合动量",
        "formula": "短期收益与中期收益比值的复合 (含量能代理)",
        "interpretation": "值高: 短期收益相对中期偏强 → 动量加速\n"
                          "值低: 短期弱于中期 → 动量衰减",
        "use_case": "多周期收益的动量复合",
    },
    "alpha057": {
        "chinese_name": "VWAP偏离-高点衰减",
        "formula": "(收盘-VWAP)/最高点位置衰减排名, 取负",
        "interpretation": "值高: 收盘低于VWAP且远离近期高点 → 弱势\n"
                          "值低: 收盘高于VWAP → 强势",
        "use_case": "收盘相对VWAP与高点的强弱",
    },
    "alpha058": {
        "chinese_name": "板块中性-量价相关",
        "formula": "VWAP与量能相关的衰减时序排名 (简化板块中性)",
        "interpretation": "值高: 剔除板块后量价仍背离 → 个体承压\n"
                          "值低: 个体量价配合 → 相对强势",
        "use_case": "剔除板块共性的量价相关",
    },
    "alpha059": {
        "chinese_name": "行业中性-量价相关",
        "formula": "加权VWAP与量能相关的衰减排名 (简化行业中性)",
        "interpretation": "值高: 行业中性后量价背离 → 承压\n"
                          "值低: 量价配合 → 强势",
        "use_case": "剔除行业共性的量价相关",
    },
    "alpha060": {
        "chinese_name": "日内位置-量能加权",
        "formula": "((收-低)-(高-收))/(高-低)×量 的排名, 与高点位置之差",
        "interpretation": "值高: 日内强势放量但未过度 → 健康上行\n"
                          "值低: 日内弱势或高点透支 → 回落",
        "use_case": "日内位置量能加权的方向",
    },
    "alpha061": {
        "chinese_name": "VWAP低点-量能比较",
        "formula": "VWAP距16日低点排名 与 VWAP长周期量能相关排名 比较",
        "interpretation": "值高: VWAP远离低点但量能相关弱 → 上行存疑\n"
                          "值低: VWAP接近低点 → 低位",
        "use_case": "VWAP位置与量能相关的比较",
    },
    "alpha062": {
        "chinese_name": "VWAP量能-开盘结构",
        "formula": "VWAP量能相关 与 开盘/中价结构排名 比较, 取负",
        "interpretation": "值高: 结构偏空 → 下行倾向\n"
                          "值低: 结构偏多 → 上行倾向",
        "use_case": "VWAP量能与开盘结构对比",
    },
    "alpha063": {
        "chinese_name": "行业中性-动量相关",
        "formula": "收盘变动衰减与量价加权衰减之差 (简化行业中性)",
        "interpretation": "值高: 中性后动量偏多 → 相对强\n"
                          "值低: 中性后偏空 → 相对弱",
        "use_case": "剔除行业的动量相关",
    },
    "alpha064": {
        "chinese_name": "开低加权-量能相关",
        "formula": "开低加权均值与均量相关 vs 中价VWAP加权变动, 取负",
        "interpretation": "值高: 量价结构偏空 → 下行\n"
                          "值低: 量价结构偏多 → 上行",
        "use_case": "开低加权的量价结构方向",
    },
    "alpha065": {
        "chinese_name": "开盘VWAP-量能相关",
        "formula": "开盘VWAP加权与均量相关 vs 开盘距低点排名, 取负",
        "interpretation": "值高: 结构偏空 → 下行\n"
                          "值低: 结构偏多 → 上行",
        "use_case": "开盘VWAP的量能结构方向",
    },
    "alpha066": {
        "chinese_name": "VWAP变动-日内衰减",
        "formula": "VWAP变动衰减排名 + 低价VWAP结构衰减时序排名, 取负",
        "interpretation": "值高: 结构偏空 → 下行\n"
                          "值低: 结构偏多 → 上行",
        "use_case": "VWAP变动与日内结构的衰减",
    },
    "alpha067": {
        "chinese_name": "动量-波动复合",
        "formula": "动量与波动率的复合 (简化)",
        "interpretation": "值高: 动量强且波动可控 → 趋势健康\n"
                          "值低: 动量弱或波动失控 → 趋势不稳",
        "use_case": "动量与波动率的稳定性复合",
    },
    "alpha068": {
        "chinese_name": "高量相关-收低结构",
        "formula": "高量相关时序排名 vs 收低加权变动排名, 取负",
        "interpretation": "值高: 结构偏空 → 下行\n"
                          "值低: 结构偏多 → 上行",
        "use_case": "高量相关与收低结构对比",
    },
    "alpha069": {
        "chinese_name": "波动调整动量",
        "formula": "动量除以波动率 (波动率归一的动量)",
        "interpretation": "值高: 单位波动的动量高 → 高质量趋势\n"
                          "值低: 单位波动的动量低 → 低质量趋势",
        "use_case": "风险调整后的动量质量",
    },
    "alpha070": {
        "chinese_name": "量价交互复合",
        "formula": "价格与成交量交互的复合得分",
        "interpretation": "值高: 量价正向交互 → 趋势有量支撑\n"
                          "值低: 量价背离 → 趋势缺量",
        "use_case": "量价交互的趋势确认",
    },
    "alpha071": {
        "chinese_name": "量价衰减-极大值",
        "formula": "收盘量能相关衰减 与 开低VWAP结构衰减 取较大",
        "interpretation": "值高: 任一量价结构走强 → 偏多\n"
                          "值低: 两者皆弱 → 偏空",
        "use_case": "双路量价结构的最优",
    },
    "alpha072": {
        "chinese_name": "中价量能-VWAP量能比",
        "formula": "中价均量相关衰减排名 / VWAP量能相关衰减排名",
        "interpretation": "值高: 中价量价强于VWAP量价 → 偏多\n"
                          "值低: 反之 → 偏空",
        "use_case": "两类量价相关的相对强弱",
    },
    "alpha073": {
        "chinese_name": "VWAP变动-开低衰减",
        "formula": "VWAP变动衰减 与 开低比值衰减时序 取极大, 取负",
        "interpretation": "值高: 结构偏空 → 下行\n"
                          "值低: 结构偏多 → 上行",
        "use_case": "VWAP变动与开低比的衰减",
    },
    "alpha074": {
        "chinese_name": "收盘均量-高VWAP相关",
        "formula": "收盘均量相关 vs 高VWAP加权量能相关, 取负",
        "interpretation": "值高: 结构偏空 → 下行\n"
                          "值低: 结构偏多 → 上行",
        "use_case": "收盘与高VWAP的量能对比",
    },
    "alpha075": {
        "chinese_name": "VWAP量能-低均量比较",
        "formula": "VWAP量能相关 与 低价均量相关 比较",
        "interpretation": "值高: VWAP量价强于低价量价 → 偏多\n"
                          "值低: 反之 → 偏空",
        "use_case": "VWAP与低价量能相关比较",
    },
    "alpha076": {
        "chinese_name": "量价趋势复合",
        "formula": "成交量与价格趋势的复合得分",
        "interpretation": "值高: 量价趋势同向 → 趋势可信\n"
                          "值低: 量价趋势背离 → 趋势存疑",
        "use_case": "量价趋势一致性",
    },
    "alpha077": {
        "chinese_name": "中价高点-量能衰减",
        "formula": "中价高点结构衰减 与 中价均量相关衰减 取较小",
        "interpretation": "值高: 两路结构皆偏多 → 上行\n"
                          "值低: 任一偏空 → 谨慎",
        "use_case": "中价结构与量能的保守组合",
    },
    "alpha078": {
        "chinese_name": "低VWAP-量能幂次相关",
        "formula": "低VWAP求和均量相关 ^ VWAP量能相关",
        "interpretation": "值高: 量价相关共振 → 趋势强\n"
                          "值低: 量价相关弱 → 趋势弱",
        "use_case": "低VWAP的量价共振",
    },
    "alpha079": {
        "chinese_name": "收益动量复合",
        "formula": "收益率的动量复合得分",
        "interpretation": "值高: 收益动量持续 → 趋势延续\n"
                          "值低: 收益动量衰减 → 趋势转弱",
        "use_case": "收益率动量的延续性",
    },
    "alpha080": {
        "chinese_name": "量价背离-评分",
        "formula": "价格与成交量背离程度的评分",
        "interpretation": "值高: 量价背离明显 → 趋势反转预警\n"
                          "值低: 量价同步 → 趋势稳健",
        "use_case": "量价背离的反转预警",
    },
    "alpha081": {
        "chinese_name": "VWAP量能-对数乘积",
        "formula": "VWAP均量相关的对数乘积排名 vs VWAP量能相关, 取负",
        "interpretation": "值高: 结构偏空 → 下行\n"
                          "值低: 结构偏多 → 上行",
        "use_case": "VWAP量能的对数复合",
    },
    "alpha082": {
        "chinese_name": "动量相关复合",
        "formula": "动量与相关性的复合得分",
        "interpretation": "值高: 动量与相关性共振 → 趋势强\n"
                          "值低: 二者背离 → 趋势弱",
        "use_case": "动量相关性复合",
    },
    "alpha083": {
        "chinese_name": "高低区间-量能比值",
        "formula": "滞后高低区间排名 × 量能排名 / (区间/VWAP差)",
        "interpretation": "值高: 区间收窄放量 → 蓄势突破\n"
                          "值低: 区间放大或缩量 → 不稳定",
        "use_case": "区间压缩放量的突破",
    },
    "alpha084": {
        "chinese_name": "VWAP高点-收盘幂次",
        "formula": "VWAP距高点时序排名 ^ 收盘5日变动",
        "interpretation": "值高: VWAP回落且收盘走强 → 背离转多\n"
                          "值低: VWAP创高且收盘走弱 → 背离转空",
        "use_case": "VWAP与收盘的幂次背离",
    },
    "alpha085": {
        "chinese_name": "高收加权-量能幂相关",
        "formula": "高收加权均量相关 ^ 中价量能时序相关",
        "interpretation": "值高: 量价相关共振 → 偏多\n"
                          "值低: 量价相关弱 → 偏空",
        "use_case": "高收加权的量价共振",
    },
    "alpha086": {
        "chinese_name": "收盘均量-开收VWAP",
        "formula": "收盘均量相关时序排名 vs 开收VWAP结构, 取负",
        "interpretation": "值高: 结构偏空 → 下行\n"
                          "值低: 结构偏多 → 上行",
        "use_case": "收盘量能与开收结构对比",
    },
    "alpha087": {
        "chinese_name": "量价动量复合",
        "formula": "成交量加权的价格动量复合",
        "interpretation": "值高: 放量动量 → 趋势有力\n"
                          "值低: 缩量动量 → 趋势乏力",
        "use_case": "量能加权动量",
    },
    "alpha088": {
        "chinese_name": "开低高收-量能衰减",
        "formula": "开低高收排名差衰减 与 收盘均量相关衰减 取较小",
        "interpretation": "值高: 两路皆偏多 → 上行\n"
                          "值低: 任一偏空 → 谨慎",
        "use_case": "四价位与量能的保守组合",
    },
    "alpha089": {
        "chinese_name": "波动调整动量(89)",
        "formula": "动量经波动率调整 (变体)",
        "interpretation": "值高: 风险调整动量高 → 高质量趋势\n"
                          "值低: 风险调整动量低 → 低质量",
        "use_case": "风险调整动量质量",
    },
    "alpha090": {
        "chinese_name": "价格离散度",
        "formula": "收盘10日标准差 / 收盘10日均值 (变异系数)",
        "interpretation": "值高: 价格离散度大 → 波动剧烈/趋势不稳\n"
                          "值低: 价格离散度小 → 走势平稳",
        "use_case": "衡量价格波动的相对离散程度",
    },
    "alpha091": {
        "chinese_name": "收益-量能相关复合",
        "formula": "收益率与成交量相关性的复合得分",
        "interpretation": "值高: 收益与量能正相关 → 趋势有量支撑\n"
                          "值低: 收益与量能背离 → 趋势缺量",
        "use_case": "收益量能相关确认",
    },
    "alpha092": {
        "chinese_name": "中价收开-量能衰减",
        "formula": "中价收开条件衰减 与 低均量相关衰减 取较小",
        "interpretation": "值高: 两路皆偏多 → 上行\n"
                          "值低: 任一偏空 → 谨慎",
        "use_case": "中价条件与量能保守组合",
    },
    "alpha093": {
        "chinese_name": "量价排名背离",
        "formula": "成交量排名与价格排名的背离程度",
        "interpretation": "值高: 量价排名背离 → 趋势预警\n"
                          "值低: 量价排名同步 → 趋势稳健",
        "use_case": "横截面量价排名背离",
    },
    "alpha094": {
        "chinese_name": "VWAP低点-量能幂相关",
        "formula": "VWAP距12日低点排名 ^ VWAP量能时序相关, 取负",
        "interpretation": "值高: VWAP远离低点但量能背离 → 上行存疑\n"
                          "值低: VWAP接近低点量价配合 → 低位机会",
        "use_case": "VWAP位置与量能的幂次结构",
    },
    "alpha095": {
        "chinese_name": "开盘低点-中价量能",
        "formula": "开盘距低点排名 与 中价均量相关幂次时序排名 比较",
        "interpretation": "值高: 开盘走高且量价共振 → 偏多\n"
                          "值低: 开盘低位 → 偏空",
        "use_case": "开盘位置与中价量能",
    },
    "alpha096": {
        "chinese_name": "量价衰减-极大反转",
        "formula": "VWAP量能相关衰减 与 收盘量能极值衰减 取极大, 取负",
        "interpretation": "值高: 量价结构偏空 → 下行\n"
                          "值低: 量价结构偏多 → 上行",
        "use_case": "双路量价衰减的反转",
    },
    "alpha097": {
        "chinese_name": "量能加权收益动量",
        "formula": "成交量加权的收益动量得分",
        "interpretation": "值高: 放量收益动量 → 趋势有力\n"
                          "值低: 缩量收益动量 → 趋势乏力",
        "use_case": "量能加权收益动量",
    },
    "alpha098": {
        "chinese_name": "VWAP量能-开盘衰减差",
        "formula": "VWAP均量相关衰减 - 开盘量能极小值衰减时序",
        "interpretation": "值高: VWAP量价强于开盘量价 → 偏多\n"
                          "值低: 反之 → 偏空",
        "use_case": "VWAP与开盘量能的衰减差",
    },
    "alpha099": {
        "chinese_name": "中价量能-低量相关",
        "formula": "中价求和均量相关 vs 低量相关, 取负",
        "interpretation": "值高: 结构偏空 → 下行\n"
                          "值低: 结构偏多 → 上行",
        "use_case": "中价与低价的量能相关对比",
    },
    "alpha100": {
        "chinese_name": "收益-量能动量复合",
        "formula": "收益率与成交量的动量复合得分",
        "interpretation": "值高: 量价动量同向 → 趋势延续\n"
                          "值低: 量价动量背离 → 趋势转弱",
        "use_case": "收益量能动量复合",
    },
    "alpha101": {
        "chinese_name": "日内强弱-收开振幅比",
        "formula": "(收盘-开盘)/(最高-最低+微小量)",
        "interpretation": "值高: 收盘远高于开盘且实体占振幅大 → 当日强势\n"
                          "值低: 收盘低于开盘 → 当日弱势",
        "use_case": "最直观的当日多空力量对比",
        "signal_logic": "值高 → 做多; 值低 → 做空",
    },
}

# 分类中文说明 (对应因子真实 category)
CATEGORIES: Dict[str, str] = {
    "momentum": "动量类 — 衡量价格变化的速度和方向",
    "trend": "趋势类 — 识别价格趋势的强度和持续性",
    "volume_price": "量价类 — 分析成交量与价格的关系",
    "price_volume": "价量类 — 价格主导的量价交互",
    "price_momentum": "价格动量类 — 基于价格自身的动量",
    "price_position": "价格位置类 — 价格在区间内的相对位置",
    "price_structure": "价格结构类 — 开高低收的几何结构",
    "price_reversal": "反转类 — 识别趋势末端/反转信号",
    "price_dispersion": "离散类 — 衡量价格波动的离散程度",
    "vwap": "均价类 — 基于成交均价(VWAP)的分析",
    "complex_signal": "复合类 — 多个子信号加权的综合因子",
}

# 因子展示字段中文名映射
DISPLAY_FIELDS: Dict[str, str] = {
    "chinese_name": "中文名",
    "formula": "计算公式",
    "interpretation": "值高/值低含义",
    "use_case": "适用场景",
    "signal_logic": "信号逻辑",
}


def get_description(name: str) -> Optional[dict]:
    """获取某个因子的中文描述; 无则返回 None。"""
    return ALPHA101_DESCRIPTIONS.get(name)


def get_category_description(category: str) -> Optional[str]:
    """获取某个分类的中文说明。"""
    return CATEGORIES.get(category)
