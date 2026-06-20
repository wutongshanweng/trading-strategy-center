import { useState } from "react";
import {
  Card, Input, Button, Typography, Row, Col, Statistic, Tag, Space, Empty, message, Divider, Alert,
} from "antd";
import { SearchOutlined, RobotOutlined, AimOutlined } from "@ant-design/icons";
import { mlOptsApi } from "../services/phase4Api";

const { Title, Text } = Typography;

const DIR_COLOR: Record<string, string> = { BUY: "#52c41a", SELL: "#ff4d4f", HOLD: "#888" };
const DIR_ICON: Record<string, string> = { BUY: "🟢", SELL: "🔴", HOLD: "⚪" };
const HEALTH_COLOR: Record<string, string> = {
  HEALTHY: "#52c41a", WARNING: "#faad14", DECAYED: "#ff4d4f",
};

export default function MLAnalyzer() {
  const [symbol, setSymbol] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const run = async () => {
    const s = symbol.trim().toUpperCase();
    if (!s) { message.warning("请输入合约代码"); return; }
    setLoading(true); setResult(null);
    try {
      const d = await mlOptsApi.analyze(s);
      if (d?.success) { setResult(d); message.success(`${s} 分析完成`); }
      else message.error("分析返回异常");
    } catch (e: any) {
      message.error("分析失败: " + (e?.response?.data?.detail || e?.message || ""));
    } finally { setLoading(false); }
  };

  const ml = result?.ml_prediction;
  const opt = result?.option_analysis;
  const combo = result?.combo_advice;

  return (
    <div>
      <Title level={3}><RobotOutlined /> ML + 期权 完整分析</Title>
      <Card style={{ marginBottom: 16 }}>
        <Space.Compact style={{ width: "100%" }}>
          <Input
            size="large" allowClear prefix={<SearchOutlined />}
            placeholder="输入合约代码, 如 RB2510 / 600019.SH"
            value={symbol} onChange={(e) => setSymbol(e.target.value)}
            onPressEnter={run} disabled={loading}
          />
          <Button type="primary" size="large" loading={loading} onClick={run}>🧠 分析</Button>
        </Space.Compact>
        <Text type="secondary" style={{ marginTop: 8, display: "block" }}>
          数据直连仓库 · ML 即时训练预测 + 期权曲面分析
        </Text>
      </Card>

      {!loading && !result && <Card><Empty description="输入合约代码开始分析" /></Card>}

      {result && (
        <>
          {/* ML 预测结论 */}
          <Card title={<><RobotOutlined /> ML 预测结论</>} style={{ marginBottom: 16 }}
            headStyle={{ borderLeft: `4px solid ${DIR_COLOR[ml.direction] || "#888"}` }}>
            <Row gutter={24} align="middle">
              <Col><div style={{ fontSize: 40 }}>{DIR_ICON[ml.direction] || "⚪"}</div></Col>
              <Col flex="auto">
                <Title level={4} style={{ margin: 0, color: DIR_COLOR[ml.direction] }}>
                  未来5天预测 {ml.direction === "BUY" ? "上涨" : ml.direction === "SELL" ? "下跌" : "盘整"}
                  {" "}{(ml.predicted_return * 100).toFixed(2)}%
                </Title>
                <Text type="secondary">
                  模型: {ml.model_name} · {ml.feature_count} 特征 · 训练数据至 {ml.trained_at || "n/a"}
                </Text>
              </Col>
              <Col>
                <Statistic title="置信度" value={ml.confidence} />
                <Text>模型健康: <Tag color={ml.model_health === "HEALTHY" ? "green" :
                  ml.model_health === "WARNING" ? "orange" : "red"}>{ml.model_health}</Tag></Text>
              </Col>
            </Row>
            {ml.note && <Text type="warning">⚠️ {ml.note}</Text>}
          </Card>

          {/* 期权分析结论 */}
          <Card title={<><AimOutlined /> 期权分析结论</>} style={{ marginBottom: 16 }}>
            {opt.data_source === "synthetic" && (
              <Alert type="warning" showIcon style={{ marginBottom: 12 }}
                message={opt.data_note || "期权曲面为合成数据, 仅供逻辑演示"} />
            )}
            <Row gutter={16}>
              <Col xs={8}><Statistic title="IV Rank" value={opt.iv_rank} suffix="%" /></Col>
              <Col xs={8}><Statistic title="Skew" value={opt.skew}
                valueStyle={{ color: opt.skew >= 0 ? "#52c41a" : "#ff4d4f" }} /></Col>
              <Col xs={8}><Statistic title="期限结构" value={opt.term_structure} /></Col>
            </Row>
            <Divider style={{ margin: "12px 0" }} />
            <Text strong>套利信号 ({opt.arb_signals.length}):</Text>
            {opt.arb_signals.length ? opt.arb_signals.map((s: any, i: number) => (
              <div key={i} style={{ marginTop: 6 }}>
                <Tag color={s.direction === "BULLISH" ? "green" : s.direction === "BEARISH" ? "red" : "default"}>
                  {s.type}
                </Tag>
                <Text>{s.reason}</Text>
              </div>
            )) : <Text type="secondary"> 无</Text>}
          </Card>

          {/* 联合策略建议 */}
          <Card title="🎯 联合策略建议" style={{ borderLeft: "4px solid #1890ff" }}>
            <Statistic title="推荐策略" value={combo.strategy_name} />
            <p style={{ marginTop: 8 }}><Text strong>方向:</Text> {combo.direction}</p>
            <p><Text type="secondary">{combo.reason}</Text></p>
            {combo.risk_notes && <Text type="warning">⚠️ {combo.risk_notes}</Text>}
          </Card>
        </>
      )}
    </div>
  );
}
