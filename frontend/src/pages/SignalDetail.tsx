import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Card, Row, Col, Typography, Tag, Spin, Empty, Button, Statistic, Divider, Space, Progress,
} from "antd";
import {
  ArrowLeftOutlined, AimOutlined, ThunderboltOutlined, ExperimentOutlined,
  LinkOutlined, WarningOutlined, BarChartOutlined,
} from "@ant-design/icons";
import { alertApi, type AlertSignal } from "../services/macroNewsApi";
import { fundamentalApi } from "../services/fundamentalApi";

const { Title, Text, Paragraph } = Typography;

const DIR_CFG: Record<string, { cn: string; color: string }> = {
  BUY: { cn: "做多", color: "#52c41a" },
  SELL: { cn: "做空", color: "#ff4d4f" },
  HOLD: { cn: "持有", color: "#faad14" },
  WATCH: { cn: "观望", color: "#faad14" },
};

function stars(n: number) { return "⭐".repeat(Math.max(0, Math.min(5, n))); }

export default function SignalDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [sig, setSig] = useState<AlertSignal | null>(null);
  const [fundamental, setFundamental] = useState<any | null>(null);
  const [fundLoading, setFundLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    alertApi.detail(id).then(setSig).catch(() => setSig(null)).finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!sig?.symbol) return;
    setFundLoading(true);
    fundamentalApi.detail(sig.symbol)
      .then(setFundamental)
      .catch(() => setFundamental(null))
      .finally(() => setFundLoading(false));
  }, [sig?.symbol]);

  if (loading) return <div style={{ textAlign: "center", padding: 80 }}><Spin size="large" /></div>;
  if (!sig) return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/macro-news")}>返回仪表盘</Button>
      <Empty description="信号不存在或已过期" style={{ marginTop: 40 }} />
    </div>
  );

  const cfg = DIR_CFG[sig.direction] || DIR_CFG.WATCH;
  const d = sig.detail || {};
  const committee = d.committee || {};
  const agents = d.agents || [];
  const macroLink = d.macro_linkage || {};
  const slPct = sig.entry_price ? ((sig.stop_loss - sig.entry_price) / sig.entry_price * 100).toFixed(1) : "0";
  const tpPct = sig.entry_price ? ((sig.take_profit - sig.entry_price) / sig.entry_price * 100).toFixed(1) : "0";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/macro-news")}>返回仪表盘</Button>
        <Title level={4} style={{ margin: 0, color: cfg.color }}>
          {sig.symbol} {sig.product_name} {cfg.cn}信号 · {stars(sig.star_rating)}
        </Title>
      </div>
      <Divider style={{ margin: "12px 0" }} />

      <Row gutter={16}>
        {/* 交易参数 */}
        <Col xs={24} md={12}>
          <Card size="small" title={<><AimOutlined /> 交易参数</>}
            style={{ marginBottom: 16, borderLeft: `4px solid ${cfg.color}` }}>
            <Row gutter={16}>
              <Col span={8}><Statistic title="入场价" value={sig.entry_price} /></Col>
              <Col span={8}><Statistic title="止损" value={sig.stop_loss} suffix={`(${slPct}%)`} valueStyle={{ color: "#ff4d4f", fontSize: 18 }} /></Col>
              <Col span={8}><Statistic title="止盈" value={sig.take_profit} suffix={`(${tpPct}%)`} valueStyle={{ color: "#52c41a", fontSize: 18 }} /></Col>
            </Row>
            <Divider style={{ margin: "12px 0" }} />
            <Space>
              <Text type="secondary">综合置信度</Text>
              <Progress percent={Math.round(sig.confidence * 100)} size="small" style={{ width: 160 }} />
              <Text type="secondary">来源: {sig.source}</Text>
            </Space>
          </Card>
        </Col>

        {/* 委员会综合 */}
        <Col xs={24} md={12}>
          <Card size="small" title={<><ThunderboltOutlined /> 多 agent 委员会裁决</>} style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={8}><Statistic title="综合净分" value={committee.net_score ?? "—"} valueStyle={{ color: cfg.color }} /></Col>
              <Col span={8}><Statistic title="一致性" value={committee.agreement != null ? `${(committee.agreement * 100).toFixed(0)}%` : "—"} /></Col>
              <Col span={8}><Statistic title="参与agent" value={committee.n_agents ?? agents.length} /></Col>
            </Row>
            <Paragraph type="secondary" style={{ fontSize: 12, marginTop: 8 }}>
              净分区间 [-1,1], 越偏离0方向越明确; 一致性=同向agent占比。来源: {sig.source}
            </Paragraph>
            {d.llm_comment && (
              <Paragraph style={{ fontSize: 13, marginTop: 4, background: "#f6f6f6", padding: 8, borderRadius: 4 }}>
                🤖 {d.llm_comment}
              </Paragraph>
            )}
          </Card>
        </Col>
      </Row>

      {/* agent 各维度意见 */}
      <Card size="small" title={<><ThunderboltOutlined /> 各 agent 分析意见 ({agents.length})</>} style={{ marginBottom: 16 }}>
        {agents.length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
          <Space direction="vertical" style={{ width: "100%" }} size={10}>
            {agents.map((a: any, i: number) => {
              const sc = DIR_CFG[a.direction] || DIR_CFG.WATCH;
              return (
                <Card key={i} size="small" type="inner"
                  style={{ borderLeft: `4px solid ${sc.color}` }}
                  styles={{ body: { padding: "8px 12px" } }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <Space>
                      <Text strong style={{ fontSize: 14 }}>{a.name_cn}</Text>
                      <Tag color={a.direction === "BUY" ? "green" : a.direction === "SELL" ? "red" : "default"}>
                        {a.direction === "BUY" ? "做多" : a.direction === "SELL" ? "做空" : a.direction === "HOLD" ? "持有" : "观望"}
                      </Tag>
                    </Space>
                    <Space>
                      <Text type="secondary">置信</Text>
                      <Progress percent={Math.round((a.confidence || 0) * 100)} size="small" style={{ width: 100 }} />
                    </Space>
                  </div>
                  <Text type="secondary" style={{ fontSize: 12 }}>{a.reason}</Text>
                </Card>
              );
            })}
          </Space>}
      </Card>

      {/* 宏观联动 */}
      <Card size="small" title={<><LinkOutlined /> 宏观联动</>} style={{ marginBottom: 16 }}>
        {Object.keys(macroLink).length === 0 ? <Text type="secondary">该品种暂无宏观关联配置</Text> :
          <Row gutter={[12, 8]}>
            {Object.entries(macroLink).map(([ind, corr]: [string, any]) => (
              <Col xs={12} sm={8} md={6} key={ind}>
                <Card size="small" style={{ textAlign: "center" }}>
                  <Text type="secondary">{ind}</Text>
                  <div style={{ fontSize: 18, fontWeight: 600, color: corr > 0 ? "#52c41a" : "#ff4d4f" }}>
                    {corr > 0 ? "+" : ""}{corr}
                  </div>
                </Card>
              </Col>
            ))}
          </Row>}
        <Paragraph type="secondary" style={{ fontSize: 12, marginTop: 8 }}>
          正值=该宏观指标与品种正相关(指标走强利多), 负值=负相关。
        </Paragraph>
      </Card>

      {/* 基本面四维分析 */}
      <Card
        size="small"
        title={<><BarChartOutlined /> 基本面四维分析</>}
        extra={fundLoading ? <Spin size="small" /> : <Text type="secondary" style={{ fontSize: 12 }}>数据质量: {fundamental?.inventory?.data_quality || "—"}</Text>}
        style={{ marginBottom: 16 }}
      >
        {fundLoading ? (
          <div style={{ textAlign: "center", padding: 20 }}><Spin size="small" /></div>
        ) : !fundamental ? (
          <Text type="secondary">暂无基本面数据</Text>
        ) : (
          <>
            {/* 综合评分 */}
            <div style={{ textAlign: "center", marginBottom: 16 }}>
              <Text type="secondary">综合基本面评分</Text>
              <div style={{
                fontSize: 32, fontWeight: 700,
                color: (fundamental.inventory?.score ?? 0) >= 0 ? "#52c41a" : "#ff4d4f"
              }}>
                {(fundamental.inventory?.score ?? 0) >= 0 ? "+" : ""}{(fundamental.inventory?.score ?? 0).toFixed(2)}
              </div>
              <Tag color={(fundamental.inventory?.score ?? 0) >= 0 ? "green" : "red"}>
                {(fundamental.inventory?.score ?? 0) >= 0 ? "偏多" : "偏空"}
              </Tag>
            </div>

            {/* 四维评分 */}
            <Row gutter={12}>
              {[
                { key: "inventory", label: "库存", icon: "📦", value: fundamental.inventory?.score },
                { key: "cost", label: "成本", icon: "⛓️", value: fundamental.cost?.score },
                { key: "seasonal", label: "季节性", icon: "📅", value: fundamental.seasonal?.score },
                { key: "demand", label: "需求", icon: "📈", value: fundamental.demand?.score },
              ].map(({ key, label, icon, value }) => (
                <Col xs={12} sm={6} key={key}>
                  <Card size="small" style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 18 }}>{icon}</div>
                    <Text type="secondary" style={{ fontSize: 12 }}>{label}</Text>
                    <div style={{
                      fontSize: 20, fontWeight: 600,
                      color: (value ?? 0) >= 0 ? "#52c41a" : "#ff4d4f"
                    }}>
                      {(value ?? 0) >= 0 ? "+" : ""}{(value ?? 0).toFixed(2)}
                    </div>
                    <Progress
                      percent={Math.round(((value ?? 0) + 1) / 2 * 100)}
                      size="small"
                      showInfo={false}
                      strokeColor={(value ?? 0) >= 0 ? "#52c41a" : "#ff4d4f"}
                    />
                  </Card>
                </Col>
              ))}
            </Row>

            {/* 详细说明 */}
            <Divider style={{ margin: "12px 0" }} />
            <Row gutter={16}>
              {[
                { label: "库存", detail: fundamental.inventory?.detail, trend: fundamental.inventory?.trend, pct: fundamental.inventory?.percentile },
                { label: "成本", detail: fundamental.cost?.detail, pct: fundamental.cost?.total_cost_change },
                { label: "季节性", detail: fundamental.seasonal?.detail, wr: fundamental.seasonal?.win_rate },
                { label: "需求", detail: fundamental.demand?.detail, trend: fundamental.demand?.overall_trend },
              ].map(({ label, detail, trend, pct, wr }) => {
                const pctVal = pct ?? 0;
                const pctChange = pctVal * 100;
                return (
                  <Col xs={24} sm={12} key={label}>
                    <Paragraph style={{ fontSize: 12, margin: 0 }}>
                      <Text strong>{label}: </Text>
                      <Text type="secondary" style={{ fontSize: 11 }}>{detail || "—"}</Text>
                      {(trend || pct != null) && (
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {" | "}{trend ?? `变化: ${pctChange > 0 ? "+" : ""}${pctChange.toFixed(1)}%`}
                        </Text>
                      )}
                      {wr != null && (
                        <Text type="secondary" style={{ fontSize: 11 }}> | 胜率: {(wr * 100).toFixed(0)}%</Text>
                      )}
                    </Paragraph>
                  </Col>
                );
              })}
            </Row>
          </>
        )}
      </Card>

      {/* 风险提示 */}
      <Card size="small" title={<><WarningOutlined /> 风险提示</>}>
        <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13 }}>
          <li>信号基于历史行情计算, 不构成投资建议; 实盘需结合实时盘口。</li>
          <li>止损位 {sig.stop_loss} ({slPct}%), 严格执行风控, 单笔仓位建议不超过 30%。</li>
          {d.atr14 && <li>近 14 日 ATR ≈ {d.atr14}, 止盈止损按 2/4 倍 ATR 设定。</li>}
        </ul>
      </Card>
    </div>
  );
}
