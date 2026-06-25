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
    # =========================================================
    # Alpha 102-191 (新增 — 来自 docs/因子.md 中文部分)
    # =========================================================
    "alpha102": {
        "chinese_name": "成交量变动率-正偏量",
        "formula": "成交量变动率6日SMA(正偏部分)",
        "interpretation": "值高: 成交量持续放大 → 市场活跃度提升\n"
                          "值低: 成交量缩减 → 市场活跃度下降",
        "use_case": "衡量成交量增长动量",
    },
    "alpha103": {
        "chinese_name": "低价距-20日低点距离",
        "formula": "(20-LOWDAY(LOW,20))/20*100",
        "interpretation": "值高: 接近20日最低点 → 低位支撑区\n"
                          "值低: 距低点较远 → 价格已脱离底部",
        "use_case": "判断价格相对历史低点的位置",
    },
    "alpha104": {
        "chinese_name": "量价相关变动-波动调整",
        "formula": "-1 * delta(corr(HIGH,VOLUME,5),5) * rank(std(CLOSE,20))",
        "interpretation": "值高: 量价相关性下降且波动率低 → 趋势减弱\n"
                          "值低: 量价相关稳定 → 趋势持续",
        "use_case": "捕捉量价关系的变化",
    },
    "alpha105": {
        "chinese_name": "开盘-成交量排名相关",
        "formula": "-1 * corr(rank(OPEN), rank(VOLUME), 10)",
        "interpretation": "值高: 开盘高时成交量偏低 → 上涨乏力\n"
                          "值低: 开盘与量同步 → 方向确认",
        "use_case": "验证开盘方向是否有量能支撑",
    },
    "alpha106": {
        "chinese_name": "收盘-20日变动",
        "formula": "CLOSE - DELAY(CLOSE, 20)",
        "interpretation": "值高: 价格高于20日前 → 20日趋势向上\n"
                          "值低: 价格低于20日前 → 20日趋势向下",
        "use_case": "中期趋势跟踪",
    },
    "alpha107": {
        "chinese_name": "开盘价-极值偏离复合",
        "formula": "((OPEN-DELAY(HIGH,1))*(OPEN-DELAY(CLOSE,1))*(OPEN-DELAY(LOW,1)))取负排名",
        "interpretation": "值高: 开盘处于近期高价区 → 偏空\n"
                          "值低: 开盘处于低价区 → 偏多",
        "use_case": "开盘位置的极值信号",
    },
    "alpha108": {
        "chinese_name": "高价突破-量能加权",
        "formula": "((RANK((HIGH-MIN(HIGH,2)))^RANK(CORR(VWAP,MEAN(VOLUME,120),6)))*-1",
        "interpretation": "值高: 突破力度强且量能配合 → 强势\n"
                          "值低: 突破无量 → 假突破风险",
        "use_case": "突破信号的质量验证",
    },
    "alpha109": {
        "chinese_name": "日内波幅-标准差比率",
        "formula": "SMA(HIGH-LOW,10,2)/SMA(SMA(HIGH-LOW,10,2),10,2)",
        "interpretation": "值高: 波幅放大且有持续性 → 趋势明确\n"
                          "值低: 波幅收缩 → 盘整或趋势减弱",
        "use_case": "衡量波动率的稳定性",
    },
    "alpha110": {
        "chinese_name": "上涨/下跌能量比",
        "formula": "SUM(MAX(0,HIGH-DELAY(CLOSE,1)),20)/SUM(MAX(0,DELAY(CLOSE,1)-LOW),20)*100",
        "interpretation": "值高: 上涨能量强于下跌 → 多头占优\n"
                          "值低: 下跌能量强于上涨 → 空头占优",
        "use_case": "多空能量对比",
    },
    "alpha111": {
        "chinese_name": "加权价量变化-价差动量",
        "formula": "SMA(VOL*(CLOSE-LOW-(HIGH-CLOSE))/(HIGH-LOW),11,2)-SMA(VOL*(CLOSE-LOW-(HIGH-CLOSE))/(HIGH-LOW),4,2)",
        "interpretation": "值高: 近期价差动量上升 → 短期偏多\n"
                          "值低: 价差动量下降 → 短期偏空",
        "use_case": "加权价差动量变化",
    },
    "alpha112": {
        "chinese_name": "涨跌成交量净比",
        "formula": "(上涨量-下跌量)/(上涨量+下跌量)*100",
        "interpretation": "值高: 上涨时成交量更大 → 多头主导\n"
                          "值低: 下跌时成交量更大 → 空头主导",
        "use_case": "量能主导方向",
    },
    "alpha113": {
        "chinese_name": "持仓量-均线偏离复合",
        "formula": "-1 * (rank(sum(DELAY(CLOSE,5),20)/20)*corr(CLOSE,VOLUME,2))*rank(corr(sum(CLOSE,5),sum(CLOSE,20),2))",
        "interpretation": "值高: 价格与量背离且中期走弱 → 偏空\n"
                          "值低: 价格量配合良好 → 偏多",
        "use_case": "价量与均线偏离综合信号",
    },
    "alpha114": {
        "chinese_name": "波幅-成交量结构比",
        "formula": "rank((HIGH-LOW)/(SUM(CLOSE,5)/5))*rank(VOLUME)/((HIGH-LOW)/(SUM(CLOSE,5)/5)/(VWAP-CLOSE))",
        "interpretation": "值高: 高波幅+高成交量+价格低于VWAP → 偏空\n"
                          "值低: 波幅适中+价格高于VWAP → 偏多",
        "use_case": "波幅与成交量的结构分析",
    },
    "alpha115": {
        "chinese_name": "价量相关-时序排名复合",
        "formula": "rank(corr((HIGH*0.9+CLOSE*0.1),mean(VOLUME,30),10))^rank(corr(TSRANK((HIGH+LOW)/2,4),TSRANK(VOLUME,10),7))",
        "interpretation": "值高: 价量相关强且时序排名靠前 → 趋势确认\n"
                          "值低: 相关性弱 → 趋势不明",
        "use_case": "价量时序复合信号",
    },
    "alpha116": {
        "chinese_name": "收盘价-线性回归斜率",
        "formula": "REGBETA(CLOSE,SEQUENCE,20)",
        "interpretation": "值高: 20日线性趋势向上 → 偏多\n"
                          "值低: 趋势向下 → 偏空",
        "use_case": "线性趋势强度",
    },
    "alpha117": {
        "chinese_name": "量排名-价格位置-收益复合",
        "formula": "TSRANK(VOLUME,32)*(1-TSRANK((CLOSE+HIGH-LOW),16))*(1-TSRANK(RET,32))",
        "interpretation": "值高: 放量+价格位置低+收益为负 → 超卖反弹可能\n"
                          "值低: 缩量+价格位置高 → 偏空",
        "use_case": "量价位三维度复合",
    },
    "alpha118": {
        "chinese_name": "上影线/下影线比率",
        "formula": "SUM(HIGH-OPEN,20)/SUM(OPEN-LOW,20)*100",
        "interpretation": "值高: 上影线长 → 冲高回落，偏空\n"
                          "值低: 下影线长 → 探底回升，偏多",
        "use_case": "日内多空争夺判断",
    },
    "alpha119": {
        "chinese_name": "VWAP-量能相关-衰减复合",
        "formula": "rank(decay_linear(corr(VWAP,sum(mean(VOLUME,5),26),5),7))-rank(decay_linear(TSRANK(MIN(corr(rank(OPEN),rank(mean(VOLUME,15)),21),9),7),8))",
        "interpretation": "值高: VWAP量价关系强于开盘量价 → 偏多\n"
                          "值低: 反之 → 偏空",
        "use_case": "VWAP与开盘量能衰减差",
    },
    "alpha120": {
        "chinese_name": "VWAP-收盘价比率",
        "formula": "rank((VWAP-CLOSE))/(VWAP+CLOSE)",
        "interpretation": "值高: 收盘价低于VWAP → 偏空\n"
                          "值低: 收盘价高于VWAP → 偏多",
        "use_case": "收盘价相对VWAP位置",
    },
    "alpha121": {
        "chinese_name": "VWAP偏离-量能相关复合",
        "formula": "(rank((VWAP-MIN(VWAP,12)))^TSRANK(corr(TSRANK(VWAP,20),TSRANK(mean(VOLUME,60),2),18),3))*-1",
        "interpretation": "值高: VWAP下方且量能萎缩 → 偏空\n"
                          "值低: VWAP上方且量能配合 → 偏多",
        "use_case": "VWAP偏离与量能复合",
    },
    "alpha122": {
        "chinese_name": "对数收盘价-三次平滑差分",
        "formula": "三重SMA(log(CLOSE),13,2)的一阶差分",
        "interpretation": "值高: 对数价格加速上升 → 动能增强\n"
                          "值低: 对数价格减速或下降 → 动能减弱",
        "use_case": "对数价格动量的高阶平滑",
    },
    "alpha123": {
        "chinese_name": "中价量能相关-低价相关对比",
        "formula": "(rank(corr(sum((HIGH+LOW)/2,20),sum(mean(VOLUME,60),20),9))<rank(corr(LOW,VOLUME,6)))*-1",
        "interpretation": "值高: 低价量价相关更强 → 底部支撑\n"
                          "值低: 中价量价更相关 → 偏空",
        "use_case": "量价支撑来源分析",
    },
    "alpha124": {
        "chinese_name": "VWAP基差-波动调整",
        "formula": "(CLOSE-VWAP)/decay_linear(rank(TSMAX(CLOSE,30)),2)",
        "interpretation": "值高: 收盘高于VWAP且波动调整后仍高 → 偏多\n"
                          "值低: 收盘低于VWAP → 偏空",
        "use_case": "VWAP基差的波动调整",
    },
    "alpha125": {
        "chinese_name": "VWAP量价相关-价变动量对比",
        "formula": "rank(decay_linear(corr(VWAP,mean(VOLUME,80),17),20))/rank(decay_linear(delta(CLOSE*0.5+VWAP*0.5,3),16))",
        "interpretation": "值高: 量价相关强于价变动量 → 偏多\n"
                          "值低: 价变动量更强 → 偏空",
        "use_case": "VWAP量价与价变动量对比",
    },
    "alpha126": {
        "chinese_name": "典型价格",
        "formula": "(CLOSE+HIGH+LOW)/3",
        "interpretation": "值高: 典型价格高 → 当日均价偏强\n"
                          "值低: 典型价格低 → 当日均价偏弱",
        "use_case": "最基础的均价计算",
    },
    "alpha127": {
        "chinese_name": "收盘偏离-12日最高",
        "formula": "mean((100*(CLOSE-MAX(CLOSE,12))/(MAX(CLOSE,12)))^2)^0.5",
        "interpretation": "值高: 收盘远离12日最高 → 超买\n"
                          "值低: 收盘接近12日最高 → 强势",
        "use_case": "价格相对近期高点偏离度",
    },
    "alpha128": {
        "chinese_name": "典型价格动量振荡器",
        "formula": "100/(1+SUM(典型价格>前日?量*典型价格:0,14)/SUM(典型价格<前日?量*典型价格:0,14))",
        "interpretation": "值高: 上涨日量能更强 → 多头动能\n"
                          "值低: 下跌日量能更强 → 空头动能",
        "use_case": "量能加权动量振荡器",
    },
    "alpha129": {
        "chinese_name": "下跌幅度累加",
        "formula": "SUM(|CLOSE-DELAY(CLOSE,1)|,12) 下行部分",
        "interpretation": "值高: 累计下跌幅度大 → 下跌趋势强\n"
                          "值低: 下跌幅度小 → 下跌有限",
        "use_case": "下跌动量累加",
    },
    "alpha130": {
        "chinese_name": "中价量价相关-排名比",
        "formula": "rank(decay_linear(corr((HIGH+LOW)/2,mean(VOLUME,40),9),10))/rank(decay_linear(corr(rank(VWAP),rank(VOLUME),7),3))",
        "interpretation": "值高: 中价量价关系强于VWAP量价 → 偏多\n"
                          "值低: VWAP量价更相关 → 偏空",
        "use_case": "量价相关来源对比",
    },
    "alpha131": {
        "chinese_name": "VWAP变动-量能相关复合",
        "formula": "rank(delta(VWAP,1))^TSRANK(corr(CLOSE,mean(VOLUME,50),18),18)",
        "interpretation": "值高: VWAP上升且量价配合 → 偏多\n"
                          "值低: VWAP下降 → 偏空",
        "use_case": "VWAP变动与量价相关复合",
    },
    "alpha132": {
        "chinese_name": "成交额均线",
        "formula": "mean(AMOUNT,20)",
        "interpretation": "值高: 成交额高于均量 → 市场活跃\n"
                          "值低: 成交额低于均量 → 市场冷清",
        "use_case": "绝对成交金额趋势",
    },
    "alpha133": {
        "chinese_name": "高价/低价日位置差",
        "formula": "((20-HIGHDAY(HIGH,20))/20)*100-((20-LOWDAY(LOW,20))/20)*100",
        "interpretation": "值高: 距高价更近 → 偏空\n"
                          "值低: 距低价更近 → 偏多",
        "use_case": "价格区间位置对比",
    },
    "alpha134": {
        "chinese_name": "量加权价格变动",
        "formula": "(CLOSE-DELAY(CLOSE,12))/DELAY(CLOSE,12)*VOLUME",
        "interpretation": "值高: 价格上涨且放量 → 强势\n"
                          "值低: 价格下跌且放量 → 弱势",
        "use_case": "量能加权的价格变动",
    },
    "alpha135": {
        "chinese_name": "收盘价延迟-平滑",
        "formula": "SMA(DELAY(CLOSE/DELAY(CLOSE,20),1),20,1)",
        "interpretation": "值高: 20日收益率平滑值上升 → 偏多\n"
                          "值低: 收益率平滑值下降 → 偏空",
        "use_case": "延迟收益率的平滑跟踪",
    },
    "alpha136": {
        "chinese_name": "收益变动-开盘量相关",
        "formula": "(-1*rank(delta(RET,3)))*corr(OPEN,VOLUME,10)",
        "interpretation": "值高: 收益变动与开盘量正相关 → 偏多\n"
                          "值低: 负相关 → 偏空",
        "use_case": "收益变动与开盘量能的关系",
    },
    "alpha137": {
        "chinese_name": "价差加权成交量变化",
        "formula": "16*(CLOSE-DELAY(CLOSE,1)+(CLOSE-OPEN)/2+DELAY(CLOSE,1)-DELAY(OPEN,1))/典型价格波动量 * MAX波动",
        "interpretation": "值高: 上涨日成交量加权更多 → 偏多\n"
                          "值低: 下跌日量加权更多 → 偏空",
        "use_case": "典型价差成交量变化",
    },
    "alpha138": {
        "chinese_name": "低价量价相关-衰减复合",
        "formula": "(rank(decay_linear(delta(((LOW*0.7+VWAP*0.3)),3),20))-TSRANK(decay_linear(TSRANK(corr(TSRANK(LOW,8),TSRANK(mean(VOLUME,60),17),5),19),16),7))*-1",
        "interpretation": "值高: 低价量价关系改善 → 底部支撑增强\n"
                          "值低: 低价量价恶化 → 底部破位风险",
        "use_case": "低价区量价关系",
    },
    "alpha139": {
        "chinese_name": "开盘-成交量相关",
        "formula": "-1*corr(OPEN,VOLUME,10)",
        "interpretation": "值高: 开盘高时量能跟不上 → 偏空\n"
                          "值低: 开盘高时放量 → 偏多",
        "use_case": "开盘方向与量能配合",
    },
    "alpha140": {
        "chinese_name": "开盘收盘极值-低价相关复合",
        "formula": "min(rank(decay_linear(((rank(OPEN)+rank(LOW))-(rank(HIGH)+rank(CLOSE))),8)),TSRANK(decay_linear(corr(TSRANK(CLOSE,8),TSRANK(mean(VOLUME,60),20),8),7),3))",
        "interpretation": "值高: 低价量价关系相对强 → 底部支撑\n"
                          "值低: 高价量价相对强 → 偏空",
        "use_case": "价量结构综合分析",
    },
    "alpha141": {
        "chinese_name": "高价-成交量排名相关",
        "formula": "rank(corr(rank(HIGH),rank(mean(VOLUME,15)),9))*-1",
        "interpretation": "值高: 高价时量能跟不上 → 偏空\n"
                          "值低: 高价时放量 → 偏多",
        "use_case": "高价区量能验证",
    },
    "alpha142": {
        "chinese_name": "价格变动加速度-量复合",
        "formula": "(((-1*rank(TSRANK(CLOSE,10)))*rank(delta(delta(CLOSE,1),1)))*rank(TSRANK((VOLUME/mean(VOLUME,20)),5)))",
        "interpretation": "值高: 价格加速度为负且量能缩 → 加速下跌\n"
                          "值低: 价格加速度为正 → 偏多",
        "use_case": "价格变动加速度与量能",
    },
    "alpha143": {
        "chinese_name": "条件累计收益",
        "formula": "CLOSE>DELAY(CLOSE,1)?累计收益:SELF",
        "interpretation": "值高: 持续上涨 → 累计正收益\n"
                          "值低: 持续下跌 → 偏空",
        "use_case": "趋势跟踪条件累计",
    },
    "alpha144": {
        "chinese_name": "下跌日量加权价变化均值",
        "formula": "SUMIF(|CLOSE/DELAY(CLOSE,1)-1|/AMOUNT,20,CLOSE<DELAY(CLOSE,1))/COUNT(CLOSE<DELAY(CLOSE,1),20)",
        "interpretation": "值高: 下跌日单位成交额带来更大价跌 → 空头强\n"
                          "值低: 下跌效率低 → 空头弱",
        "use_case": "下跌效率分析",
    },
    "alpha145": {
        "chinese_name": "成交量均线差值",
        "formula": "(mean(VOLUME,9)-mean(VOLUME,26))/mean(VOLUME,12)*100",
        "interpretation": "值高: 短期均量高于长期 → 放量趋势\n"
                          "值低: 短期均量低于长期 → 缩量趋势",
        "use_case": "量能趋势判断",
    },
    "alpha146": {
        "chinese_name": "收益偏离-波动调整",
        "formula": "mean(RET-SMA(RET,61,2),20)*(RET-SMA(RET,61,2))/SMA((RET-SMA(RET,61,2))^2,60)",
        "interpretation": "值高: 收益持续偏离均值 → 趋势持续\n"
                          "值低: 收益回归均值 → 趋势减弱",
        "use_case": "均值回归与趋势持续判断",
    },
    "alpha147": {
        "chinese_name": "收盘价回归斜率-12日",
        "formula": "REGBETA(mean(CLOSE,12),SEQUENCE(12))",
        "interpretation": "值高: 12日趋势向上 → 偏多\n"
                          "值低: 趋势向下 → 偏空",
        "use_case": "中期线性趋势",
    },
    "alpha148": {
        "chinese_name": "开盘-量能相关-低价排名复合",
        "formula": "(rank(corr((OPEN),sum(mean(VOLUME,60),9),6))<rank((OPEN-TSMIN(OPEN,14))))*-1",
        "interpretation": "值高: 开盘低位且量价相关弱 → 反弹可能\n"
                          "值低: 开盘高位 → 偏空",
        "use_case": "开盘位置与量价综合",
    },
    "alpha149": {
        "chinese_name": "相对大盘-收益回归",
        "formula": "REGBETA(个股收益/大盘收益,大盘收益,252)",
        "interpretation": "值高: 个股强于大盘 → 偏多\n"
                          "值低: 个股弱于大盘 → 偏空",
        "use_case": "相对强弱分析",
    },
    "alpha150": {
        "chinese_name": "典型价格成交额",
        "formula": "(CLOSE+HIGH+LOW)/3*VOLUME",
        "interpretation": "值高: 价高且量大 → 主力参与度高\n"
                          "值低: 价低且量小 → 参与度低",
        "use_case": "主力活跃度指标",
    },
    "alpha151": {
        "chinese_name": "20日收盘价变动平滑",
        "formula": "SMA(CLOSE-DELAY(CLOSE,20),20,1)",
        "interpretation": "值高: 20日变动均值为正 → 趋势向上\n"
                          "值低: 趋势向下 → 偏空",
        "use_case": "20日趋势平滑",
    },
    "alpha152": {
        "chinese_name": "价量均线差值-双平滑",
        "formula": "SMA(mean(delay(SMA(CLOSE/DELAY(CLOSE,9),9,1),1),12)-mean(delay(SMA(CLOSE/DELAY(CLOSE,9),9,1),1),26),9,1)",
        "interpretation": "值高: 短期均线上穿长期 → 偏多\n"
                          "值低: 短期均线下穿 → 偏空",
        "use_case": "MACD类量价信号",
    },
    "alpha153": {
        "chinese_name": "多重均线均值",
        "formula": "(mean(CLOSE,3)+mean(CLOSE,6)+mean(CLOSE,12)+mean(CLOSE,24))/4",
        "interpretation": "值高: 多周期均线均向上 → 偏多\n"
                          "值低: 多周期均线均向下 → 偏空",
        "use_case": "多周期均线共振",
    },
    "alpha154": {
        "chinese_name": "VWAP偏离-量能条件",
        "formula": "(VWAP-MIN(VWAP,16))<corr(VWAP,mean(VOLUME,180),18)",
        "interpretation": "值高: VWAP下方+量价背离 → 超卖反弹\n"
                          "值低: VWAP上方 → 偏多",
        "use_case": "VWAP超卖信号",
    },
    "alpha155": {
        "chinese_name": "成交量MACD",
        "formula": "SMA(VOLUME,13,2)-SMA(VOLUME,27,2)-SMA(SMA(VOLUME,13,2)-SMA(VOLUME,27,2),10,2)",
        "interpretation": "值高: 成交量均线金叉 → 量能增加\n"
                          "值低: 死叉 → 量能减少",
        "use_case": "量能趋势转变",
    },
    "alpha156": {
        "chinese_name": "价格变动-量能双重确认",
        "formula": "(max(rank(decay_linear(delta(VWAP,5),3)),rank(decay_linear(delta(((OPEN*0.15+LOW*0.85)),2)/((OPEN*0.15+LOW*0.85))*-1,3)))*-1)",
        "interpretation": "值高: 量价双重确认上升 → 偏多\n"
                          "值低: 双重确认下跌 → 偏空",
        "use_case": "量价双重确认信号",
    },
    "alpha157": {
        "chinese_name": "复合收益排名-延迟调整",
        "formula": "MIN(PROD(rank(rank(LOG(SUM(TSMIN(rank(rank((-1*rank(delta((CLOSE-1),5))))),2),1)))),1),5)+TSRANK(delay((-1*RET),6),5)",
        "interpretation": "值高: 多周期排名靠前 → 偏多\n"
                          "值低: 排名靠后 → 偏空",
        "use_case": "多周期排名复合",
    },
    "alpha158": {
        "chinese_name": "价格偏离-波动调整",
        "formula": "((HIGH-SMA(CLOSE,15,2))-(LOW-SMA(CLOSE,15,2)))/CLOSE",
        "interpretation": "值高: 价格上轨偏离大于下轨 → 偏空\n"
                          "值低: 下轨偏离更大 → 偏多",
        "use_case": "布林带类偏离分析",
    },
    "alpha159": {
        "chinese_name": "VWAP-KC叠加",
        "formula": "VWAP-Keltner Channel复合计算",
        "interpretation": "值高: 突破KC上轨 → 偏多\n"
                          "值低: 跌破下轨 → 偏空",
        "use_case": "Keltner通道信号",
    },
    "alpha160": {
        "chinese_name": "下跌日波动率",
        "formula": "SMA(CLOSE<=DELAY(CLOSE,1)?STD(CLOSE,20):0,20,1)",
        "interpretation": "值高: 下跌日波动更大 → 空头强\n"
                          "值低: 下跌日波动小 → 空头弱",
        "use_case": "下跌波动分析",
    },
    "alpha161": {
        "chinese_name": "真实波幅均值",
        "formula": "mean(MAX(MAX((HIGH-LOW),ABS(DELAY(CLOSE,1)-HIGH)),ABS(DELAY(CLOSE,1)-LOW)),12)",
        "interpretation": "值高: 波动加大 → 趋势可能形成\n"
                          "值低: 波动收窄 → 盘整",
        "use_case": "平均真实波幅",
    },
    "alpha162": {
        "chinese_name": "RSI类振荡器-标准化",
        "formula": "(RSI12-MIN(RSI12,12))/(MAX(RSI12,12)-MIN(RSI12,12))",
        "interpretation": "值高: RSI处于超买区 → 警惕回调\n"
                          "值低: RSI超卖 → 反弹可能",
        "use_case": "RSI标准化区间",
    },
    "alpha163": {
        "chinese_name": "收益-量-价复合",
        "formula": "rank((((-1*RET)*mean(VOLUME,20))*VWAP)*(HIGH-CLOSE))",
        "interpretation": "值高: 下跌+放量+高价 → 主力出货\n"
                          "值低: 上涨+缩量 → 偏多",
        "use_case": "主力行为识别",
    },
    "alpha164": {
        "chinese_name": "倒数动量振荡器",
        "formula": "SMA(((CLOSE>DELAY(CLOSE,1))?1/(CLOSE-DELAY(CLOSE,1)):1)-MIN(...)/(HIGH-LOW)*100,13,2)",
        "interpretation": "值高: 上涨日倒数动量强 → 偏多\n"
                          "值低: 下跌日动量强 → 偏空",
        "use_case": "倒数动量分析",
    },
    "alpha165": {
        "chinese_name": "累积波动幅度",
        "formula": "(MAX(SUMAC(CLOSE-MEAN(CLOSE,48)))-MIN(SUMAC(CLOSE-MEAN(CLOSE,48))))/STD(CLOSE,48)",
        "interpretation": "值高: 波动范围大且趋势强 → 偏空\n"
                          "值低: 波动收窄 → 盘整",
        "use_case": "累积波动范围",
    },
    "alpha166": {
        "chinese_name": "收益率偏度",
        "formula": "-20*(20-1)^1.5*SUM(RET-MEAN(RET,20),20)/((20-1)*(20-2)*STD(RET,20)^1.5)",
        "interpretation": "值高: 正偏度 → 右尾肥 → 上涨概率大\n"
                          "值低: 负偏度 → 左尾肥 → 下跌概率大",
        "use_case": "收益率分布偏度",
    },
    "alpha167": {
        "chinese_name": "上涨幅度累加",
        "formula": "SUM(CLOSE>DELAY(CLOSE,1)?CLOSE-DELAY(CLOSE,1):0,12)",
        "interpretation": "值高: 累计涨幅大 → 偏多\n"
                          "值低: 涨幅有限 → 偏空",
        "use_case": "上涨动量累加",
    },
    "alpha168": {
        "chinese_name": "量能倒数",
        "formula": "-VOLUME/mean(VOLUME,20)",
        "interpretation": "值高: 缩量 → 观望\n"
                          "值低: 放量 → 活跃",
        "use_case": "量能反向指标",
    },
    "alpha169": {
        "chinese_name": "收益率均线差值-MACD",
        "formula": "SMA(mean(delay(SMA(CLOSE-DELAY(CLOSE,1),9,1),1),12)-mean(delay(SMA(CLOSE-DELAY(CLOSE,1),9,1),1),26),10,1)",
        "interpretation": "值高: MACD柱为正 → 偏多\n"
                          "值低: MACD柱为负 → 偏空",
        "use_case": "收益率MACD",
    },
    "alpha170": {
        "chinese_name": "量价位置复合",
        "formula": "(((rank((1/CLOSE))*VOLUME/mean(VOLUME,20))*((HIGH*rank(HIGH-CLOSE))/(sum(HIGH,5)/5)))-rank((VWAP-delay(VWAP,5))))",
        "interpretation": "值高: 低价+缩量+高价强势 → 偏多\n"
                          "值低: 高价+放量+VWAP下滑 → 偏空",
        "use_case": "量价位置综合",
    },
    "alpha171": {
        "chinese_name": "高低价比倒数",
        "formula": "(-1*((LOW-CLOSE)*(OPEN^5)))/((CLOSE-HIGH)*(CLOSE^5))",
        "interpretation": "值高: 下影线长+开盘低 → 偏多\n"
                          "值低: 上影线长+开盘高 → 偏空",
        "use_case": "K线形态分析",
    },
    "alpha172": {
        "chinese_name": "StochRSI类指标",
        "formula": "mean(ABS(SUM(LD>0?LD:0,14)*100/SUM(TR,14)-SUM(HD>0?HD:0,14)*100/SUM(TR,14))/...,6)",
        "interpretation": "值高: 多头能量强 → 偏多\n"
                          "值低: 空头能量强 → 偏空",
        "use_case": "随机RSI类",
    },
    "alpha173": {
        "chinese_name": "三次指数平滑-复合",
        "formula": "3*SMA(CLOSE,13,2)-2*SMA(SMA(CLOSE,13,2),13,2)+SMA(SMA(SMA(LOG(CLOSE),13,2),13,2),13,2)",
        "interpretation": "值高: 价格三重平滑上升 → 偏多\n"
                          "值低: 平滑下降 → 偏空",
        "use_case": "三重平滑趋势",
    },
    "alpha174": {
        "chinese_name": "上涨日波动率",
        "formula": "SMA(CLOSE>DELAY(CLOSE,1)?STD(CLOSE,20):0,20,1)",
        "interpretation": "值高: 上涨日波动大 → 偏多\n"
                          "值低: 上涨日波动小 → 偏空",
        "use_case": "上涨波动分析",
    },
    "alpha175": {
        "chinese_name": "波幅均值-短期",
        "formula": "mean(MAX(MAX((HIGH-LOW),ABS(DELAY(CLOSE,1)-HIGH)),ABS(DELAY(CLOSE,1)-LOW)),6)",
        "interpretation": "值高: 短期波动加大 → 趋势形成\n"
                          "值低: 波动收窄 → 盘整",
        "use_case": "短期波动",
    },
    "alpha176": {
        "chinese_name": "RSV-量相关",
        "formula": "corr(rank((CLOSE-TSMIN(LOW,12))/(TSMAX(HIGH,12)-TSMIN(LOW,12))),rank(VOLUME),6)",
        "interpretation": "值高: 超卖时放量 → 反弹信号\n"
                          "值低: 超买时缩量 → 偏空",
        "use_case": "RSV量价相关",
    },
    "alpha177": {
        "chinese_name": "高价距-20日高点",
        "formula": "((20-HIGHDAY(HIGH,20))/20)*100",
        "interpretation": "值高: 接近20日最高 → 强势\n"
                          "值低: 距高点远 → 偏弱",
        "use_case": "价格相对高点位置",
    },
    "alpha178": {
        "chinese_name": "量加权收益率",
        "formula": "(CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1)*VOLUME",
        "interpretation": "值高: 上涨放量 → 偏多\n"
                          "值低: 下跌放量 → 偏空",
        "use_case": "量能加权收益",
    },
    "alpha179": {
        "chinese_name": "VWAP-量排名-低价量排名复合",
        "formula": "rank(corr(VWAP,VOLUME,4))*rank(corr(rank(LOW),rank(mean(VOLUME,50)),12))",
        "interpretation": "值高: VWAP量价+低价量价同步 → 底部支撑\n"
                          "值低: 背离 → 偏空",
        "use_case": "双量价相关复合",
    },
    "alpha180": {
        "chinese_name": "放量-价格变动条件",
        "formula": "(mean(VOLUME,20)<VOLUME)?((-1*TSRANK(abs(delta(CLOSE,7)),60))*sign(delta(CLOSE,7))):(-1*VOLUME)",
        "interpretation": "值高: 放量+价格上涨 → 偏多\n"
                          "值低: 缩量+价格下跌 → 偏空",
        "use_case": "量能条件价格变动",
    },
    "alpha181": {
        "chinese_name": "超额收益波动",
        "formula": "SUM(((RET-MEAN(RET,20))-(BENCHMARK-MEAN(BENCHMARK,20)))^2,20)/SUM((BENCHMARK-MEAN(BENCHMARK,20))^3)",
        "interpretation": "值高: 超额收益波动大 → Alpha不稳定\n"
                          "值低: Alpha稳定 → 有Alpha",
        "use_case": "Alpha稳定性",
    },
    "alpha182": {
        "chinese_name": "同向波动计数比",
        "formula": "COUNT((CLOSE>OPEN&BENCHMARK>OPEN)OR(CLOSE<OPEN&BENCHMARK<OPEN),20)/20",
        "interpretation": "值高: 与大盘同向次数多 → Beta高\n"
                          "值低: 与大盘不同步 → 有Alpha",
        "use_case": "与大盘同步性",
    },
    "alpha183": {
        "chinese_name": "累积偏差幅度-24日",
        "formula": "(MAX(SUMAC(CLOSE-MEAN(CLOSE,24)))-MIN(SUMAC(CLOSE-MEAN(CLOSE,24))))/STD(CLOSE,24)",
        "interpretation": "值高: 累积偏差大 → 趋势强\n"
                          "值低: 偏差小 → 盘整",
        "use_case": "24日累积偏差",
    },
    "alpha184": {
        "chinese_name": "延迟价差-排名",
        "formula": "rank(corr(delay((OPEN-CLOSE),1),CLOSE,200))+rank((OPEN-CLOSE))",
        "interpretation": "值高: 价差扩大+历史200日相关 → 趋势确认\n"
                          "值低: 价差收窄 → 盘整",
        "use_case": "延迟价差趋势",
    },
    "alpha185": {
        "chinese_name": "开盘收盘偏离-平方",
        "formula": "rank((-1*((1-(OPEN/CLOSE))^2)))",
        "interpretation": "值高: 开盘收盘偏离大 → 日内波动大\n"
                          "值低: 偏离小 → 日内平稳",
        "use_case": "日内波动强度",
    },
    "alpha186": {
        "chinese_name": "StochRSI平滑",
        "formula": "mean(StochRSI,6)+delay(mean(StochRSI,6),6)的一半",
        "interpretation": "值高: 多头信号持续 → 偏多\n"
                          "值低: 空头信号 → 偏空",
        "use_case": "StochRSI平滑",
    },
    "alpha187": {
        "chinese_name": "高开缺口累加",
        "formula": "SUM(OPEN<=DELAY(OPEN,1)?0:MAX((HIGH-OPEN),(OPEN-DELAY(OPEN,1))),20)",
        "interpretation": "值高: 高开缺口多 → 多头强势\n"
                          "值低: 低开缺口多 → 空头强势",
        "use_case": "缺口分析",
    },
    "alpha188": {
        "chinese_name": "波幅偏离率",
        "formula": "(HIGH-LOW-SMA(HIGH-LOW,11,2))/SMA(HIGH-LOW,11,2)*100",
        "interpretation": "值高: 波幅超出历史均值 → 趋势形成\n"
                          "值低: 波幅低于均值 → 盘整",
        "use_case": "波幅异常检测",
    },
    "alpha189": {
        "chinese_name": "收盘价偏离均值",
        "formula": "mean(ABS(CLOSE-MEAN(CLOSE,6)),6)",
        "interpretation": "值高: 偏离6日均值大 → 趋势或背离\n"
                          "值低: 贴近均值 → 盘整",
        "use_case": "均值偏离度",
    },
    "alpha190": {
        "chinese_name": "收益分布偏离-复杂统计",
        "formula": "LOG((COUNT(RET>日化收益,20)-1)*SUMIF((RET-日化收益)^2,...)/...)",
        "interpretation": "值高: 收益分布正偏 → 偏多\n"
                          "值低: 负偏 → 偏空",
        "use_case": "收益分布形态",
    },
    "alpha191": {
        "chinese_name": "低价量价-中价复合",
        "formula": "(corr(mean(VOLUME,20),LOW,5)+((HIGH+LOW)/2)-CLOSE)",
        "interpretation": "值高: 低价量价关系强+中价支撑 → 偏多\n"
                          "值低: 收盘远离中价 → 偏空",
        "use_case": "低价量价与中价支撑复合",
    },
    # =========================================================
    # Alpha_EN 001-101 (新增 — 来自 docs/因子.md 英文部分 Alpha#)
    # 这些是不同于 Alpha 1-101 的独立公式
    # =========================================================
    "alpha_en001": {
        "chinese_name": "波动率加权-时序排名",
        "formula": "rank(Ts_ArgMax(SignedPower((收益<0?stddev(收益,20):close),2),5))-0.5",
        "interpretation": "值高: 低波动时价格高位 → 偏多\n"
                          "值低: 高波动时价格低位 → 偏空",
        "use_case": "波动率加权动量",
    },
    "alpha_en002": {
        "chinese_name": "成交量变化-涨跌相关",
        "formula": "-1*correlation(rank(delta(log(volume),2)),rank((close-open)/open),6)",
        "interpretation": "值高: 上涨时缩量 → 偏空\n"
                          "值低: 价量同步 → 偏多",
        "use_case": "量价背离检测",
    },
    "alpha_en003": {
        "chinese_name": "开盘-成交量排名相关",
        "formula": "-1*correlation(rank(open),rank(volume),10)",
        "interpretation": "值高: 开盘高时量小 → 偏空\n"
                          "值低: 开盘与量同向 → 偏多",
        "use_case": "开盘量能验证",
    },
    "alpha_en004": {
        "chinese_name": "低价时序排名",
        "formula": "-1*Ts_Rank(rank(low),9)",
        "interpretation": "值高: 低价排名靠前 → 偏多\n"
                          "值低: 低价排名靠后 → 偏空",
        "use_case": "低价位置",
    },
    "alpha_en005": {
        "chinese_name": "开盘-VWAP偏离复合",
        "formula": "rank(open-sum(vwap,10)/10)*(-1*abs(rank(close-vwap)))",
        "interpretation": "值高: 开盘高+收盘VWAP背离 → 偏空\n"
                          "值低: 开盘低+VWAP支撑 → 偏多",
        "use_case": "开盘VWAP综合",
    },
    "alpha_en006": {
        "chinese_name": "开盘-成交量相关",
        "formula": "-1*correlation(open,volume,10)",
        "interpretation": "值高: 开盘高时量小 → 偏空\n"
                          "值低: 开盘高时量大 → 偏多",
        "use_case": "开盘量价",
    },
    "alpha_en007": {
        "chinese_name": "放量条件价格变动",
        "formula": "(adv20<volume)?((-1*ts_rank(abs(delta(close,7)),60))*sign(delta(close,7))):(-1*1)",
        "interpretation": "值高: 放量上涨 → 偏多\n"
                          "值低: 放量下跌或缩量 → 偏空",
        "use_case": "量能条件信号",
    },
    "alpha_en008": {
        "chinese_name": "开盘收益乘积动量",
        "formula": "-1*rank((sum(open,5)*sum(returns,5))-delay((sum(open,5)*sum(returns,5)),10))",
        "interpretation": "值高: 乘积动量下降 → 偏空\n"
                          "值低: 乘积动量上升 → 偏多",
        "use_case": "开盘收益动量",
    },
    "alpha_en009": {
        "chinese_name": "条件价格变动",
        "formula": "(0<ts_min(delta(close,1),5))?delta(close,1):((ts_max(delta(close,1),5)<0)?delta(close,1):(-1*delta(close,1)))",
        "interpretation": "值高: 持续上涨 → 偏多\n"
                          "值低: 持续下跌 → 偏空",
        "use_case": "条件趋势跟随",
    },
    "alpha_en010": {
        "chinese_name": "条件价格排名",
        "formula": "rank((0<ts_min(delta(close,1),4))?delta(close,1):((ts_max(delta(close,1),4)<0)?delta(close,1):(-1*delta(close,1))))",
        "interpretation": "值高: 上涨趋势靠前 → 偏多\n"
                          "值低: 下跌趋势靠前 → 偏空",
        "use_case": "横截面条件排名",
    },
    "alpha_en011": {
        "chinese_name": "VWAP极值-量复合",
        "formula": "(rank(ts_max((vwap-close),3))+rank(ts_min((vwap-close),3)))*rank(delta(volume,3))",
        "interpretation": "值高: VWAP偏离大+量能增加 → 偏多\n"
                          "值低: 偏离小+缩量 → 偏空",
        "use_case": "VWAP极值量能",
    },
    "alpha_en012": {
        "chinese_name": "量变动-价格变动符号",
        "formula": "sign(delta(volume,1))*(-1*delta(close,1))",
        "interpretation": "值高: 缩量上涨 → 偏多\n"
                          "值低: 放量下跌 → 偏空",
        "use_case": "量价变动方向",
    },
    "alpha_en013": {
        "chinese_name": "收盘-成交量排名协方差",
        "formula": "-1*rank(covariance(rank(close),rank(volume),5))",
        "interpretation": "值高: 收盘高时量小 → 偏多\n"
                          "值低: 收盘高时量大 → 偏空",
        "use_case": "收盘量价协方差",
    },
    "alpha_en014": {
        "chinese_name": "收益变动-开盘量相关",
        "formula": "(-1*rank(delta(returns,3)))*correlation(open,volume,10)",
        "interpretation": "值高: 收益变动与开盘量正相关 → 偏多\n"
                          "值低: 负相关 → 偏空",
        "use_case": "收益变动量能",
    },
    "alpha_en015": {
        "chinese_name": "高价-成交量排名相关-3日累加",
        "formula": "-1*sum(rank(correlation(rank(high),rank(volume),3)),3)",
        "interpretation": "值高: 高价时量小 → 偏空\n"
                          "值低: 高价时量大 → 偏多",
        "use_case": "高价量能3日累积",
    },
    "alpha_en016": {
        "chinese_name": "高价-成交量排名协方差",
        "formula": "-1*rank(covariance(rank(high),rank(volume),5))",
        "interpretation": "值高: 高价时量小 → 偏空\n"
                          "值低: 高价时量大 → 偏多",
        "use_case": "高价量能协方差",
    },
    "alpha_en017": {
        "chinese_name": "收盘时序排名-量复合",
        "formula": "((-1*rank(ts_rank(close,10)))*rank(delta(delta(close,1),1)))*rank(ts_rank((volume/adv20),5))",
        "interpretation": "值高: 价格上涨减速+缩量 → 偏空\n"
                          "值低: 价格上涨加速+放量 → 偏多",
        "use_case": "价量加速度复合",
    },
    "alpha_en018": {
        "chinese_name": "波动价差-相关复合",
        "formula": "-1*rank(((stddev(abs((close-open)),5)+(close-open))+correlation(close,open,10)))",
        "interpretation": "值高: 波动大+价跌 → 偏空\n"
                          "值低: 波动适中+价涨 → 偏多",
        "use_case": "波动价差综合",
    },
    "alpha_en019": {
        "chinese_name": "收益-量能复合",
        "formula": "(-1*sign((close-delay(close,7))+delta(close,7)))*(1+rank(1+sum(returns,250)))",
        "interpretation": "值高: 价涨+长期收益正 → 偏多\n"
                          "值低: 价跌+长期收益负 → 偏空",
        "use_case": "长短期收益复合",
    },
    "alpha_en020": {
        "chinese_name": "开盘-极值偏离复合",
        "formula": "((-1*rank((open-delay(high,1))))*rank((open-delay(close,1))))*rank((open-delay(low,1))))",
        "interpretation": "值高: 开盘处于高价区 → 偏空\n"
                          "值低: 开盘处于低价区 → 偏多",
        "use_case": "开盘极值位置",
    },
    "alpha_en021": {
        "chinese_name": "均值-波动条件",
        "formula": "(((sum(close,8)/8)+stddev(close,8))<(sum(close,2)/2))?(-1*1):(((sum(close,2)/2)<((sum(close,8)/8)-stddev(close,8)))?1:((1<(volume/adv20))?1:(-1*1)))",
        "interpretation": "值高: 收盘高于均线+放量 → 偏多\n"
                          "值低: 收盘低于均线 → 偏空",
        "use_case": "均值偏离条件",
    },
    "alpha_en022": {
        "chinese_name": "量价相关变动-波动调整",
        "formula": "-1*(delta(correlation(high,volume,5),5)*rank(stddev(close,20)))",
        "interpretation": "值高: 量价相关下降+波动低 → 偏空\n"
                          "值低: 量价相关上升 → 偏多",
        "use_case": "量价相关变化",
    },
    "alpha_en023": {
        "chinese_name": "高价条件变动",
        "formula": "(((sum(high,20)/20)<high)?(-1*delta(high,2)):0)",
        "interpretation": "值高: 价格创20日新高 → 偏多\n"
                          "值低: 未创新高 → 中性",
        "use_case": "新高检测",
    },
    "alpha_en024": {
        "chinese_name": "长期偏离条件",
        "formula": "(((delta((sum(close,100)/100),100)/delay(close,100))<0.05)?(-1*(close-ts_min(close,100))):(-1*delta(close,3)))",
        "interpretation": "值高: 长期低估+短期反弹 → 偏多\n"
                          "值低: 长期高估+短期下跌 → 偏空",
        "use_case": "长期低估反弹",
    },
    "alpha_en025": {
        "chinese_name": "VWAP量能收益复合",
        "formula": "rank((((-1*returns)*adv20)*vwap)*(high-close))",
        "interpretation": "值高: 下跌+放量+高价 → 主力出货\n"
                          "值低: 上涨+缩量 → 偏多",
        "use_case": "主力行为",
    },
    "alpha_en026": {
        "chinese_name": "量排名相关-时序最大",
        "formula": "-1*ts_max(correlation(ts_rank(volume,5),ts_rank(high,5),5),3)",
        "interpretation": "值高: 量价背离累积 → 偏空\n"
                          "值低: 量价同步 → 偏多",
        "use_case": "量价背离时序",
    },
    "alpha_en027": {
        "chinese_name": "量价排名相关-条件",
        "formula": "((0.5<rank((sum(correlation(rank(volume),rank(vwap),6),2)/2.0)))?(-1*1):1)",
        "interpretation": "值高: 量价相关高于阈值 → 偏多\n"
                          "值低: 低于阈值 → 偏空",
        "use_case": "量价相关阈值",
    },
    "alpha_en028": {
        "chinese_name": "低价量价相关-中价",
        "formula": "scale(((correlation(adv20,low,5)+((high+low)/2))-close))",
        "interpretation": "值高: 低价量价+中价支撑强 → 偏多\n"
                          "值低: 收盘远离 → 偏空",
        "use_case": "低价量价中价复合",
    },
    "alpha_en029": {
        "chinese_name": "复合排名-延迟调整",
        "formula": "min(product(rank(rank(scale(log(sum(ts_min(rank(rank((-1*rank(delta((close-1),5))))),2),1))))),1),5)+ts_rank(delay((-1*returns),6),5)",
        "interpretation": "值高: 多周期排名靠前 → 偏多\n"
                          "值低: 排名靠后 → 偏空",
        "use_case": "多周期复合排名",
    },
    "alpha_en030": {
        "chinese_name": "符号变化-量能加权",
        "formula": "(((1-rank(((sign((close-delay(close,1)))+sign((delay(close,1)-delay(close,2))))+sign((delay(close,2)-delay(close,3)))))))*sum(volume,5))/sum(volume,20)",
        "interpretation": "值高: 持续上涨+放量 → 偏多\n"
                          "值低: 持续下跌 → 偏空",
        "use_case": "符号变化量能",
    },
    "alpha_en031": {
        "chinese_name": "排名复合-延迟",
        "formula": "(rank(rank(rank(decay_linear((-1*rank(rank(delta(close,10)))),10))))+rank((-1*delta(close,3))))+sign(scale(correlation(adv20,low,12))))",
        "interpretation": "值高: 排名上升+低价量价正 → 偏多\n"
                          "值低: 排名下降 → 偏空",
        "use_case": "多维排名复合",
    },
    "alpha_en032": {
        "chinese_name": "均值偏离-VWAP相关复合",
        "formula": "scale(((sum(close,7)/7)-close))+(20*scale(correlation(vwap,delay(close,5),230))))",
        "interpretation": "值高: 价格低+VWAP长期正相关 → 偏多\n"
                          "值低: 价格高 → 偏空",
        "use_case": "均值偏离VWAP复合",
    },
    "alpha_en033": {
        "chinese_name": "涨跌比平方",
        "formula": "rank((-1*((1-(open/close))^1)))",
        "interpretation": "值高: 实体大(涨跌明显) → 日内方向明确\n"
                          "值低: 实体小 → 日内震荡",
        "use_case": "涨跌实体强度",
    },
    "alpha_en034": {
        "chinese_name": "波动率比-变动复合",
        "formula": "rank((1-rank((stddev(returns,2)/stddev(returns,5))))+rank((-1*delta(close,1))))",
        "interpretation": "值高: 短期波动高+价格上升 → 偏多\n"
                          "值低: 波动低+价格下降 → 偏空",
        "use_case": "波动率变动复合",
    },
    "alpha_en035": {
        "chinese_name": "量排名-价位置-收益复合",
        "formula": "(Ts_Rank(volume,32)*(1-Ts_Rank(((close+high)-low),16)))*(1-Ts_Rank(returns,32))",
        "interpretation": "值高: 缩量+低价+下跌 → 超卖反弹\n"
                          "值低: 放量+高价+上涨 → 偏空",
        "use_case": "量价位收益复合",
    },
    "alpha_en036": {
        "chinese_name": "多因子复合",
        "formula": "((((2.21*rank(correlation((close-open),delay(volume,1),15)))+(0.7*rank((open-close))))+(0.73*rank(Ts_Rank(delay((-1*returns),6),5))))+rank(abs(correlation(vwap,adv20,6))))+(0.6*rank((((sum(close,200)/200)-open)*(close-open)))))",
        "interpretation": "值高: 多因子综合偏多 → 强偏多\n"
                          "值低: 多因子综合偏空 → 强偏空",
        "use_case": "多因子综合",
    },
    "alpha_en037": {
        "chinese_name": "延迟价差-200日相关",
        "formula": "rank(correlation(delay((open-close),1),close,200))+rank((open-close))",
        "interpretation": "值高: 价差扩大+长期正相关 → 趋势确认\n"
                          "值低: 价差收窄 → 盘整",
        "use_case": "长期价差趋势",
    },
    "alpha_en038": {
        "chinese_name": "收盘时序排名-涨跌幅",
        "formula": "((-1*rank(ts_rank(close,10)))*rank((close/open)))",
        "interpretation": "值高: 收盘排名高+上涨 → 偏多\n"
                          "值低: 收盘排名低+下跌 → 偏空",
        "use_case": "收盘时序涨跌幅",
    },
    "alpha_en039": {
        "chinese_name": "价格变动-量能衰减复合",
        "formula": "(-1*rank((delta(close,7)*(1-rank(decay_linear((volume/adv20),9))))))*(1+rank(sum(returns,250)))",
        "interpretation": "值高: 价格下跌+量能衰减 → 偏空\n"
                          "值低: 价格下跌+量能增加 → 偏多",
        "use_case": "量能衰减复合",
    },
    "alpha_en040": {
        "chinese_name": "高价波动-量相关",
        "formula": "((-1*rank(stddev(high,10)))*correlation(high,volume,10))",
        "interpretation": "值高: 高价时波动低+量相关强 → 偏多\n"
                          "值低: 高价时波动高 → 偏空",
        "use_case": "高价波动量相关",
    },
    "alpha_en041": {
        "chinese_name": "典型价差",
        "formula": "(((high*low)^0.5)-vwap)",
        "interpretation": "值高: 收盘高于典型价 → 偏多\n"
                          "值低: 收盘低于 → 偏空",
        "use_case": "典型价差",
    },
    "alpha_en042": {
        "chinese_name": "VWAP比率",
        "formula": "rank((vwap-close))/(vwap+close)",
        "interpretation": "值高: 收盘低于VWAP → 偏空\n"
                          "值低: 收盘高于VWAP → 偏多",
        "use_case": "VWAP比率",
    },
    "alpha_en043": {
        "chinese_name": "量排名-价变动时序排名复合",
        "formula": "ts_rank((volume/adv20),20)*ts_rank((-1*delta(close,7)),8)",
        "interpretation": "值高: 放量+价格下跌 → 超卖反弹可能\n"
                          "值低: 缩量+价格上涨 → 偏空",
        "use_case": "量价时序复合",
    },
    "alpha_en044": {
        "chinese_name": "高价-量排名相关",
        "formula": "-1*correlation(high,rank(volume),5)",
        "interpretation": "值高: 高价时量小 → 偏空\n"
                          "值低: 高价时量大 → 偏多",
        "use_case": "高价量能",
    },
    "alpha_en045": {
        "chinese_name": "延迟价格-量相关复合",
        "formula": "-1*((rank((sum(delay(close,5),20)/20))*correlation(close,volume,2))*rank(correlation(sum(close,5),sum(close,20),2))))",
        "interpretation": "值高: 价格高于延迟均线+量价背离 → 偏空\n"
                          "值低: 配合良好 → 偏多",
        "use_case": "延迟均线量价复合",
    },
    "alpha_en046": {
        "chinese_name": "长期偏离-短期条件",
        "formula": "((0.25<(((delay(close,20)-delay(close,10))/10)-((delay(close,10)-close)/10)))?(-1*1):(((((delay(close,20)-delay(close,10))/10)-((delay(close,10)-close)/10))<0)?1:((-1*1)*(close-delay(close,1)))))",
        "interpretation": "值高: 短期下跌加速 → 偏空\n"
                          "值低: 短期反弹 → 偏多",
        "use_case": "长短期偏离条件",
    },
    "alpha_en047": {
        "chinese_name": "量价位置复合",
        "formula": "((((rank((1/close))*volume)/adv20)*((high*rank((high-close)))/(sum(high,5)/5)))-rank((vwap-delay(vwap,5))))",
        "interpretation": "值高: 低价+缩量+高价强势 → 偏多\n"
                          "值低: 高价+放量+VWAP下滑 → 偏空",
        "use_case": "多维位置复合",
    },
    "alpha_en048": {
        "chinese_name": "行业中性收益",
        "formula": "indneutralize(((correlation(delta(close,1),delta(delay(close,1),1),250)*delta(close,1))/close),IndClass.subindustry)/sum(((delta(close,1)/delay(close,1))^2),250)",
        "interpretation": "值高: 行业中性Alpha正 → 偏多\n"
                          "值低: Alpha负 → 偏空",
        "use_case": "行业中性Alpha",
    },
    "alpha_en049": {
        "chinese_name": "长期偏离条件-5%阈值",
        "formula": "(((((delay(close,20)-delay(close,10))/10)-((delay(close,10)-close)/10))<-0.1)?1:((-1*1)*(close-delay(close,1)))",
        "interpretation": "值高: 长期低估 → 反弹\n"
                          "值低: 长期高估 → 偏空",
        "use_case": "5%阈值偏离",
    },
    "alpha_en050": {
        "chinese_name": "VWAP量排名-时序最大",
        "formula": "-1*ts_max(rank(correlation(rank(volume),rank(vwap),5)),5)",
        "interpretation": "值高: VWAP量排名最大时下跌 → 偏空\n"
                          "值低: VWAP量排名最大时上涨 → 偏多",
        "use_case": "VWAP量排名极值",
    },
    "alpha_en051": {
        "chinese_name": "长期偏离条件-3%阈值",
        "formula": "(((((delay(close,20)-delay(close,10))/10)-((delay(close,10)-close)/10))<-0.05)?1:((-1*1)*(close-delay(close,1)))",
        "interpretation": "值高: 轻微低估 → 偏多\n"
                          "值低: 轻微高估 → 偏空",
        "use_case": "3%阈值偏离",
    },
    "alpha_en052": {
        "chinese_name": "低价极值-收益复合",
        "formula": "((((-1*ts_min(low,5))+delay(ts_min(low,5),5))*rank(((sum(returns,240)-sum(returns,20))/220)))*ts_rank(volume,5))",
        "interpretation": "值高: 低价极值反弹+量能配合 → 偏多\n"
                          "值低: 低价破位 → 偏空",
        "use_case": "低价极值反弹",
    },
    "alpha_en053": {
        "chinese_name": "RSI类指标",
        "formula": "-1*delta((((close-low)-(high-close))/(close-low)),9)",
        "interpretation": "值高: RSI下降 → 偏空\n"
                          "值低: RSI上升 → 偏多",
        "use_case": "RSI变化",
    },
    "alpha_en054": {
        "chinese_name": "高低价比倒数",
        "formula": "(-1*((low-close)*(open^5)))/((low-high)*(close^5))",
        "interpretation": "值高: 下影线长+开盘低 → 偏多\n"
                          "值低: 上影线长 → 偏空",
        "use_case": "K线形态",
    },
    "alpha_en055": {
        "chinese_name": "RSV-量相关",
        "formula": "-1*correlation(rank(((close-ts_min(low,12))/(ts_max(high,12)-ts_min(low,12)))),rank(volume),6)",
        "interpretation": "值高: 超卖时放量 → 反弹\n"
                          "值低: 超买时缩量 → 偏空",
        "use_case": "RSV量价",
    },
    "alpha_en056": {
        "chinese_name": "收益市值复合",
        "formula": "0-(1*(rank((sum(returns,10)/sum(sum(returns,2),3)))*rank((returns*cap))))",
        "interpretation": "值高: 小市值+正收益 → 偏多\n"
                          "值低: 大市值+负收益 → 偏空",
        "use_case": "市值收益复合",
    },
    "alpha_en057": {
        "chinese_name": "VWAP基差-延迟最大复合",
        "formula": "0-(1*((close-vwap)/decay_linear(rank(ts_argmax(close,30)),2)))",
        "interpretation": "值高: 收盘高于VWAP → 偏多\n"
                          "值低: 收盘低于VWAP → 偏空",
        "use_case": "VWAP基差延迟",
    },
    "alpha_en058": {
        "chinese_name": "行业中性VWAP量价",
        "formula": "-1*Ts_Rank(decay_linear(correlation(IndNeutralize(vwap,IndClass.sector),volume,3.92795),7.89291),5.50322)",
        "interpretation": "值高: 行业中性VWAP量价正 → 偏多\n"
                          "值低: 负 → 偏空",
        "use_case": "行业中性VWAP",
    },
    "alpha_en059": {
        "chinese_name": "行业中性价量",
        "formula": "-1*Ts_Rank(decay_linear(correlation(IndNeutralize(((vwap*0.728317)+(vwap*(1-0.728317))),IndClass.industry),volume,4.25197),16.2289),8.19648)",
        "interpretation": "值高: 行业中性价量正 → 偏多\n"
                          "值低: 负 → 偏空",
        "use_case": "行业中性价量",
    },
    "alpha_en060": {
        "chinese_name": "价量标准化排名",
        "formula": "0-(1*((2*scale(rank(((((close-low)-(high-close))/(high-low))*volume))))-scale(rank(ts_argmax(close,10)))))",
        "interpretation": "值高: 放量上涨+突破 → 偏多\n"
                          "值低: 缩量+不突破 → 偏空",
        "use_case": "标准化价量",
    },
    "alpha_en061": {
        "chinese_name": "VWAP偏离-量相关条件",
        "formula": "rank((vwap-ts_min(vwap,16.1219)))<rank(correlation(vwap,adv180,17.9282))",
        "interpretation": "值高: VWAP下方+量价背离 → 偏多\n"
                          "值低: VWAP上方 → 偏空",
        "use_case": "VWAP偏离条件",
    },
    "alpha_en062": {
        "chinese_name": "VWAP相关-价位置复合",
        "formula": "(rank(correlation(vwap,sum(adv20,22.4101),9.91009))<rank(((rank(open)+rank(open))<(rank(((high+low)/2))+rank(high)))))*-1",
        "interpretation": "值高: 量价相关弱+高价强势 → 偏多\n"
                          "值低: 量价相关强 → 偏空",
        "use_case": "量价位置复合",
    },
    "alpha_en063": {
        "chinese_name": "行业中性价格变动",
        "formula": "(rank(decay_linear(delta(IndNeutralize(close,IndClass.industry),2.25164),8.22237))-rank(decay_linear(correlation(((vwap*0.318108)+(open*(1-0.318108))),sum(adv180,37.2467),13.557),12.2883)))*-1",
        "interpretation": "值高: 行业中性价格上涨 → 偏多\n"
                          "值低: 价格下跌 → 偏空",
        "use_case": "行业中性价格",
    },
    "alpha_en064": {
        "chinese_name": "中价量相关-价格变动复合",
        "formula": "(rank(correlation(sum(((open*0.178404)+(low*(1-0.178404))),12.7054),sum(adv120,12.7054),16.6208))<rank(delta(((((high+low)/2)*0.178404)+(vwap*(1-0.178404))),3.69741)))*-1",
        "interpretation": "值高: 量价相关弱+价格上涨 → 偏多\n"
                          "值低: 量价相关强 → 偏空",
        "use_case": "中价量价复合",
    },
    "alpha_en065": {
        "chinese_name": "VWAP开盘相关-低价排名",
        "formula": "(rank(correlation(((open*0.00817205)+(vwap*(1-0.00817205))),sum(adv60,8.6911),6.40374))<rank((open-ts_min(open,13.635))))*-1",
        "interpretation": "值高: VWAP开盘相关低+低价 → 偏多\n"
                          "值低: 高价 → 偏空",
        "use_case": "VWAP低价复合",
    },
    "alpha_en066": {
        "chinese_name": "VWAP变动-低价复合",
        "formula": "(rank(decay_linear(delta(vwap,3.51013),7.23052))+Ts_Rank(decay_linear(((((low*0.96633)+(low*(1-0.96633)))-vwap)/(open-((high+low)/2))),11.4157),6.72611))*-1",
        "interpretation": "值高: VWAP上升+低价支撑 → 偏多\n"
                          "值低: VWAP下降 → 偏空",
        "use_case": "VWAP低价复合",
    },
    "alpha_en067": {
        "chinese_name": "高价突破-行业中性量价",
        "formula": "(rank((high-ts_min(high,2.14593)))^rank(correlation(IndNeutralize(vwap,IndClass.sector),IndNeutralize(adv20,IndClass.subindustry),6.02936)))*-1",
        "interpretation": "值高: 突破+行业中性量价正 → 偏多\n"
                          "值低: 突破失败 → 偏空",
        "use_case": "突破量价验证",
    },
    "alpha_en068": {
        "chinese_name": "高价量排名-价格变动",
        "formula": "(Ts_Rank(correlation(rank(high),rank(adv15),8.91644),13.9333)<rank(delta(((close*0.518371)+(low*(1-0.518371))),1.06157)))*-1",
        "interpretation": "值高: 高价量排名低+价格下跌 → 偏空\n"
                          "值低: 价格反弹 → 偏多",
        "use_case": "高价量价",
    },
    "alpha_en069": {
        "chinese_name": "VWAP变动-行业中性相关",
        "formula": "(rank(ts_max(delta(IndNeutralize(vwap,IndClass.industry),2.72412),4.79344))^Ts_Rank(correlation(((close*0.490655)+(vwap*(1-0.490655))),adv20,4.92416),9.0615))*-1",
        "interpretation": "值高: VWAP上升+行业正相关 → 偏多\n"
                          "值低: VWAP下降 → 偏空",
        "use_case": "行业VWAP复合",
    },
    "alpha_en070": {
        "chinese_name": "VWAP变动-收益相关复合",
        "formula": "(rank(delta(vwap,1.29456))^Ts_Rank(correlation(IndNeutralize(close,IndClass.industry),adv50,17.8256),17.9171))*-1",
        "interpretation": "值高: VWAP上升+行业正收益 → 偏多\n"
                          "值低: VWAP下降 → 偏空",
        "use_case": "VWAP收益复合",
    },
    "alpha_en071": {
        "chinese_name": "双时序排名复合",
        "formula": "max(Ts_Rank(decay_linear(correlation(Ts_Rank(close,3.43976),Ts_Rank(adv180,12.0647),18.0175),4.20501),15.6948),Ts_Rank(decay_linear((rank(((low+open)-(vwap+vwap)))^2),16.4662),4.4388))",
        "interpretation": "值高: 收盘排名+VWAP偏离排名高 → 偏多\n"
                          "值低: 排名低 → 偏空",
        "use_case": "双时序排名",
    },
    "alpha_en072": {
        "chinese_name": "中价量相关-排名比",
        "formula": "rank(decay_linear(correlation(((high+low)/2),adv40,8.93345),10.1519))/rank(decay_linear(correlation(Ts_Rank(vwap,3.72469),Ts_Rank(volume,18.5188),6.86671),2.95011)))",
        "interpretation": "值高: 中价量相关强于VWAP量相关 → 偏多\n"
                          "值低: 反之 → 偏空",
        "use_case": "量价相关对比",
    },
    "alpha_en073": {
        "chinese_name": "VWAP变动-低价复合-时序最大",
        "formula": "(max(rank(decay_linear(delta(vwap,4.72775),2.91864)),Ts_Rank(decay_linear(((delta(((open*0.147155)+(low*(1-0.147155))),2.03608)/((open*0.147155)+(low*(1-0.147155))))*-1),3.33829),16.7411))*-1",
        "interpretation": "值高: VWAP下降+低价下跌 → 偏空\n"
                          "值低: VWAP上升 → 偏多",
        "use_case": "VWAP低价双重",
    },
    "alpha_en074": {
        "chinese_name": "收盘量相关-低价复合",
        "formula": "(rank(correlation(close,sum(adv30,37.4843),15.1365))<rank(correlation(rank(((high*0.0261661)+(vwap*(1-0.0261661)))),rank(volume),11.4791)))*-1",
        "interpretation": "值高: 收盘量相关弱+低价量相关强 → 偏多\n"
                          "值低: 反之 → 偏空",
        "use_case": "收盘低价复合",
    },
    "alpha_en075": {
        "chinese_name": "VWAP量相关-低价相关对比",
        "formula": "rank(correlation(vwap,volume,4.24304))<rank(correlation(rank(low),rank(adv50),12.4413))",
        "interpretation": "值高: 低价量相关更强 → 底部支撑\n"
                          "值低: VWAP量相关更强 → 偏空",
        "use_case": "量相关来源",
    },
    "alpha_en076": {
        "chinese_name": "VWAP变动-低价排名复合",
        "formula": "(max(rank(decay_linear(delta(vwap,1.24383),11.8259)),Ts_Rank(decay_linear(Ts_Rank(correlation(IndNeutralize(low,IndClass.sector),adv81,8.14941),19.569),17.1543),19.383))*-1",
        "interpretation": "值高: VWAP下方+低价量价正 → 偏多\n"
                          "值低: VWAP上方 → 偏空",
        "use_case": "VWAP低价",
    },
    "alpha_en077": {
        "chinese_name": "中价极值-量相关复合",
        "formula": "min(rank(decay_linear(((((high+low)/2)+high)-(vwap+high)),20.0451)),rank(decay_linear(correlation(((high+low)/2),adv40,3.1614),5.64125)))",
        "interpretation": "值高: 高价+中价量价正 → 偏多\n"
                          "值低: 中价量价负 → 偏空",
        "use_case": "中价极值",
    },
    "alpha_en078": {
        "chinese_name": "中价量相关-VWAP排名复合",
        "formula": "rank(correlation(sum(((low*0.352233)+(vwap*(1-0.352233))),19.7428),sum(adv40,19.7428),6.83313))^rank(correlation(rank(vwap),rank(volume),5.77492))",
        "interpretation": "值高: 中价量价+VWAP量价同向 → 偏多\n"
                          "值低: 背离 → 偏空",
        "use_case": "多量价相关复合",
    },
    "alpha_en079": {
        "chinese_name": "行业中性价格变动-排名",
        "formula": "rank(delta(IndNeutralize(((close*0.60733)+(open*(1-0.60733))),IndClass.sector),1.23438))<rank(correlation(Ts_Rank(vwap,3.60973),Ts_Rank(adv150,9.18637),14.6644))",
        "interpretation": "值高: 行业中性价涨+VWAP量价正 → 偏多\n"
                          "值低: 价跌 → 偏空",
        "use_case": "行业中性价量",
    },
    "alpha_en080": {
        "chinese_name": "高价突破-行业中性",
        "formula": "((rank(Sign(delta(IndNeutralize(((open*0.868128)+(high*(1-0.868128))),IndClass.industry),4.04545)))^Ts_Rank(correlation(high,adv10,5.11456),5.53756))*-1",
        "interpretation": "值高: 高价突破+行业量价正 → 偏多\n"
                          "值低: 突破失败 → 偏空",
        "use_case": "突破行业验证",
    },
    "alpha_en081": {
        "chinese_name": "VWAP相关-量排名复合",
        "formula": "(rank(Log(product(rank((rank(correlation(vwap,sum(adv10,49.6054),8.47743))^4)),14.9655)))<rank(correlation(rank(vwap),rank(volume),5.07914)))*-1",
        "interpretation": "值高: VWAP量价排名靠前 → 偏多\n"
                          "值低: 量价排名靠后 → 偏空",
        "use_case": "对数量价复合",
    },
    "alpha_en082": {
        "chinese_name": "开盘变动-量相关复合",
        "formula": "min(rank(decay_linear(delta(open,1.46063),14.8717)),Ts_Rank(decay_linear(correlation(IndNeutralize(volume,IndClass.sector),((open*0.634196)+(open*(1-0.634196))),17.4842),6.92131),13.4283))*-1",
        "interpretation": "值高: 开盘上涨+量价正 → 偏多\n"
                          "值低: 开盘下跌 → 偏空",
        "use_case": "开盘量价",
    },
    "alpha_en083": {
        "chinese_name": "波幅-成交量结构",
        "formula": "(rank(delay(((high-low)/(sum(close,5)/5)),2))*rank(rank(volume)))/(((high-low)/(sum(close,5)/5))/(vwap-close))",
        "interpretation": "值高: 波幅大+量高+VWAP下方 → 偏空\n"
                          "值低: 波幅适中 → 偏多",
        "use_case": "波幅结构",
    },
    "alpha_en084": {
        "chinese_name": "VWAP偏离-时序最大",
        "formula": "SignedPower(Ts_Rank((vwap-ts_max(vwap,15.3217)),20.7127),delta(close,4.96796))",
        "interpretation": "值高: VWAP偏离增大+价格上涨 → 偏多\n"
                          "值低: VWAP偏离减小 → 偏空",
        "use_case": "VWAP偏离动量",
    },
    "alpha_en085": {
        "chinese_name": "价量时序排名相关",
        "formula": "rank(correlation(((high*0.876703)+(close*(1-0.876703))),adv30,9.61331))^rank(correlation(Ts_Rank(((high+low)/2),3.70596),Ts_Rank(volume,10.1595),7.11408))",
        "interpretation": "值高: 价量时序排名靠前 → 偏多\n"
                          "值低: 排名靠后 → 偏空",
        "use_case": "时序排名复合",
    },
    "alpha_en086": {
        "chinese_name": "收盘VWAP相关-价位置",
        "formula": "((Ts_Rank(correlation(close,sum(adv20,14.7444),6.00049),20.4195)<rank(((open+close)-(vwap+open))))*-1",
        "interpretation": "值高: 收盘量价相关低+价高 → 偏空\n"
                          "值低: 价低 → 偏多",
        "use_case": "收盘VWAP",
    },
    "alpha_en087": {
        "chinese_name": "VWAP变动-量相关复合",
        "formula": "(max(rank(decay_linear(delta(((close*0.369701)+(vwap*(1-0.369701))),1.91233),2.65461)),Ts_Rank(decay_linear(abs(correlation(IndNeutralize(adv81,IndClass.industry),close,13.4132)),4.89768),14.4535))*-1",
        "interpretation": "值高: VWAP上升+量价正 → 偏多\n"
                          "值低: VWAP下降 → 偏空",
        "use_case": "VWAP量相关",
    },
    "alpha_en088": {
        "chinese_name": "开盘低价极值-量相关",
        "formula": "min(rank(decay_linear(((rank(open)+rank(low))-(rank(high)+rank(close))),8.06882)),Ts_Rank(decay_linear(correlation(Ts_Rank(close,8.44728),Ts_Rank(adv60,20.6966),8.01266),6.65053),2.61957))",
        "interpretation": "值高: 低价+量价正 → 偏多\n"
                          "值低: 高价+量价负 → 偏空",
        "use_case": "开盘低价",
    },
    "alpha_en089": {
        "chinese_name": "低价量相关-时序排名",
        "formula": "Ts_Rank(decay_linear(correlation(((low*0.967285)+(low*(1-0.967285))),adv10,6.94279),5.51607),3.79744)-Ts_Rank(decay_linear(delta(IndNeutralize(vwap,IndClass.industry),3.48158),10.1466),15.3012)",
        "interpretation": "值高: 低价量价强-VWAP下降 → 偏多\n"
                          "值低: 反之 → 偏空",
        "use_case": "低价量价差",
    },
    "alpha_en090": {
        "chinese_name": "高价偏离-行业量相关",
        "formula": "((rank((close-ts_max(close,4.66719)))^Ts_Rank(correlation(IndNeutralize(adv40,IndClass.subindustry),low,5.38375),3.21856))*-1",
        "interpretation": "值高: 高价+行业量价正 → 偏多\n"
                          "值低: 高价+行业量价负 → 偏空",
        "use_case": "高价偏离",
    },
    "alpha_en091": {
        "chinese_name": "行业价量-时序复合",
        "formula": "(Ts_Rank(decay_linear(decay_linear(correlation(IndNeutralize(close,IndClass.industry),volume,9.74928),16.398),3.83219),4.8667)-rank(decay_linear(correlation(vwap,adv30,4.01303),2.6809)))*-1",
        "interpretation": "值高: 行业价量强-VWAP量价弱 → 偏多\n"
                          "值低: 反之 → 偏空",
        "use_case": "行业时序复合",
    },
    "alpha_en092": {
        "chinese_name": "低价条件-时序排名",
        "formula": "min(Ts_Rank(decay_linear(((((high+low)/2)+close)<(low+open),14.7221),18.8683),Ts_Rank(decay_linear(correlation(rank(low),rank(adv30),7.58555),6.94024),6.80584))",
        "interpretation": "值高: 低价+量价正 → 偏多\n"
                          "值低: 高价+量价负 → 偏空",
        "use_case": "低价条件",
    },
    "alpha_en093": {
        "chinese_name": "VWAP量相关-时序排名比",
        "formula": "Ts_Rank(decay_linear(correlation(IndNeutralize(vwap,IndClass.industry),adv81,17.4193),19.848),7.54455)/rank(decay_linear(delta(((close*0.524434)+(vwap*(1-0.524434))),2.77377),16.2664))",
        "interpretation": "值高: VWAP量价强+价上涨 → 偏多\n"
                          "值低: VWAP量价弱 → 偏空",
        "use_case": "VWAP时序",
    },
    "alpha_en094": {
        "chinese_name": "VWAP偏离-量相关复合",
        "formula": "(rank((vwap-ts_min(vwap,11.5783)))^Ts_Rank(correlation(Ts_Rank(vwap,19.6462),Ts_Rank(adv60,4.02992),18.0926),2.70756))*-1",
        "interpretation": "值高: VWAP下方+量价正 → 偏多\n"
                          "值低: VWAP上方 → 偏空",
        "use_case": "VWAP偏离",
    },
    "alpha_en095": {
        "chinese_name": "开盘低价-量相关对比",
        "formula": "rank((open-ts_min(open,12.4105)))<Ts_Rank((rank(correlation(sum(((high+low)/2),19.1351),sum(adv40,19.1351),12.8742))^5),11.7584)",
        "interpretation": "值高: 开盘低价+量价正 → 偏多\n"
                          "值低: 开盘高价 → 偏空",
        "use_case": "开盘低价",
    },
    "alpha_en096": {
        "chinese_name": "VWAP量排名-时序复合",
        "formula": "(max(Ts_Rank(decay_linear(correlation(rank(vwap),rank(volume),3.83878),4.16783),8.38151),Ts_Rank(decay_linear(Ts_ArgMax(correlation(Ts_Rank(close,7.45404),Ts_Rank(adv60,4.13242),3.65459),12.6556),14.0365),13.4143))*-1",
        "interpretation": "值高: VWAP量排名靠前 → 偏多\n"
                          "值低: 排名靠后 → 偏空",
        "use_case": "VWAP时序最大",
    },
    "alpha_en097": {
        "chinese_name": "行业低价量价-时序复合",
        "formula": "(rank(decay_linear(delta(IndNeutralize(((low*0.721001)+(vwap*(1-0.721001))),IndClass.industry),3.3705),20.4523))-Ts_Rank(decay_linear(Ts_Rank(correlation(Ts_Rank(low,7.87871),Ts_Rank(adv60,17.255),4.97547),18.5925),15.7152),6.71659))*-1",
        "interpretation": "值高: 行业低价量价强 → 偏多\n"
                          "值低: 行业高价 → 偏空",
        "use_case": "行业低价",
    },
    "alpha_en098": {
        "chinese_name": "VWAP量相关-延迟相关复合",
        "formula": "rank(decay_linear(correlation(vwap,sum(adv5,26.4719),4.58418),7.18088))-rank(decay_linear(Ts_Rank(Ts_ArgMin(correlation(rank(open),rank(adv15),20.8187),8.62571),6.95668),8.07206))",
        "interpretation": "值高: VWAP量相关强-开盘量相关弱 → 偏多\n"
                          "值低: 反之 → 偏空",
        "use_case": "VWAP开盘复合",
    },
    "alpha_en099": {
        "chinese_name": "中价量相关-低价量相关对比",
        "formula": "((rank(correlation(sum(((high+low)/2),19.8975),sum(adv60,19.8975),8.8136))<rank(correlation(low,volume,6.28259)))*-1",
        "interpretation": "值高: 低价量相关强 → 底部支撑\n"
                          "值低: 中价量相关强 → 偏空",
        "use_case": "量相关来源",
    },
    "alpha_en100": {
        "chinese_name": "行业中性价量-标准化",
        "formula": "0-(1*(((1.5*scale(indneutralize(indneutralize(rank(((((close-low)-(high-close))/(high-low))*volume)),IndClass.subindustry),IndClass.subindustry)))-scale(indneutralize((correlation(close,rank(adv20),5)-rank(ts_argmin(close,30))),IndClass.subindustry)))*(volume/adv20))))",
        "interpretation": "值高: 行业中性价量标准化高 → 偏多\n"
                          "值低: 低 → 偏空",
        "use_case": "行业标准化价量",
    },
    "alpha_en101": {
        "chinese_name": "日内收益率",
        "formula": "(close-open)/((high-low)+0.001)",
        "interpretation": "值高: 收盘远高于开盘 → 当日强势\n"
                          "值低: 收盘低于开盘 → 当日弱势",
        "use_case": "最直观的日内多空",
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
