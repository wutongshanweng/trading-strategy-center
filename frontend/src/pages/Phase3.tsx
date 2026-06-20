import { useState, useEffect } from "react";
import {
  Card, Row, Col, Table, Tag, Typography, Button, Spin, message,
  Statistic, Select, Slider, Space, Divider, Empty,
} from "antd";
import { ExperimentOutlined, FundOutlined, ThunderboltOutlined } from "@ant-design/icons";
import { phase3Api } from "../services/phase3Api";

const { Title, Text } = Typography;

// IV 值 → 颜色 (蓝→绿→黄→红 热力)
function ivColor(v: number | null, min: number, max: number): string {
  if (v === null || isNaN(v)) return "#f0f0f0";
  const t = max > min ? (v - min) / (max - min) : 0.5;
  const hue = (1 - t) * 220; // 220(蓝)→0(红)
  return `hsl(${hue}, 70%, 55%)`;
}

const dirColor: Record<string, string> = {
  BULLISH: "#52c41a", BEARISH: "#ff4d4f", NEUTRAL: "#888",
};

export default function Phase3() {
  // ML 特征
  const [features, setFeatures] = useState<any[]>([]);
  // 期权曲面
  const [forward, setForward] = useState(100);
  const [surface, setSurface] = useState<any>(null);
  const [surfaceLoading, setSurfaceLoading] = useState(false);
  // 套利信号
  const [arbSignals, setArbSignals] = useState<any[]>([]);
  // 联合策略
  const [comboDir, setComboDir] = useState("BUY");
  const [comboIvRank, setComboIvRank] = useState(50);
  const [comboSkew, setComboSkew] = useState(0);
  const [combo, setCombo] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        const d = await phase3Api.mlFeatures();
        if (d?.features) setFeatures(d.features);
      } catch { /* 后端未启动 */ }
    })();
    loadSurface();
  }, []);

  const loadSurface = async () => {
    setSurfaceLoading(true);
    try {
      const [s, a] = await Promise.all([
        phase3Api.optionsSurface(forward),
        phase3Api.optionsArbitrage(forward),
      ]);
      if (s?.success) setSurface(s);
      if (a?.success) setArbSignals(a.signals || []);
    } catch (e: any) {
      message.error("曲面加载失败: " + (e?.message || ""));
    } finally {
      setSurfaceLoading(false);
    }
  };

  const runCombo = async () => {
    try {
      const d = await phase3Api.optionsCombo({
        futures_direction: comboDir, futures_confidence: 0.7,
        iv_rank: comboIvRank, skew: comboSkew, spot: forward,
      });
      if (d?.success) setCombo(d.advice);
    } catch (e: any) {
      message.error("联合策略失败: " + (e?.message || ""));
    }
  };

  // 曲面色阶范围
  const flat: number[] = surface
    ? surface.iv_grid.flat().filter((v: any) => v !== null && !isNaN(v))
    : [];
  const ivMin = flat.length ? Math.min(...flat) : 0;
  const ivMax = flat.length ? Math.max(...flat) : 1;

  return (
    <div>
      <Title level={3}>
        <ThunderboltOutlined /> Phase 3 — ML 升级 + 期权深度
      </Title>
      <Text type="secondary">
        机器学习特征工程、波动率曲面、期限结构套利、期权-期货联合策略
      </Text>
      <Divider />

      {/* ML 特征面板 */}
      <Card
        title={<><ExperimentOutlined /> ML 特征工程 ({features.length} 个技术面特征)</>}
        style={{ marginBottom: 16 }}
      >
        <Table
          dataSource={features.map((f, i) => ({ ...f, key: i }))}
          size="small"
          pagination={{ pageSize: 7 }}
          columns={[
            { title: "特征名", dataIndex: "name", render: (t) => <Text code>{t}</Text> },
            {
              title: "分类", dataIndex: "category",
              render: (c) => <Tag color="blue">{c}</Tag>,
            },
          ]}
        />
      </Card>

      {/* 期权波动率曲面 */}
      <Card
        title={<><FundOutlined /> 期权波动率曲面 (IV 热力图)</>}
        style={{ marginBottom: 16 }}
        extra={
          <Space>
            <Text>标的价</Text>
            <Select
              value={forward}
              style={{ width: 100 }}
              onChange={setForward}
              options={[50, 100, 200, 3800, 5000].map((v) => ({ value: v, label: v }))}
            />
            <Button type="primary" onClick={loadSurface} loading={surfaceLoading}>
              重建曲面
            </Button>
          </Space>
        }
      >
        {surfaceLoading ? (
          <Spin />
        ) : surface ? (
          <Row gutter={16}>
            <Col xs={24} lg={16}>
              {/* 热力图: 行=行权价, 列=到期 */}
              <div style={{ overflowX: "auto" }}>
                <table style={{ borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      <th style={{ padding: 4, fontSize: 11 }}>K \ T</th>
                      {surface.ttms.map((t: number) => (
                        <th key={t} style={{ padding: 4, fontSize: 11 }}>{t.toFixed(2)}y</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {surface.iv_grid.map((row: any[], ri: number) => (
                      <tr key={ri}>
                        <td style={{ padding: 4, fontSize: 11, fontWeight: "bold" }}>
                          {surface.strikes[ri]?.toFixed(0)}
                        </td>
                        {row.map((v, ci) => (
                          <td
                            key={ci}
                            title={v !== null ? `IV=${v}` : "N/A"}
                            style={{
                              width: 46, height: 26,
                              background: ivColor(v, ivMin, ivMax),
                              color: "#fff", fontSize: 10, textAlign: "center",
                            }}
                          >
                            {v !== null ? (v * 100).toFixed(0) : ""}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  色阶: 蓝(低IV) → 红(高IV), 数字为 IV%
                </Text>
              </div>
            </Col>
            <Col xs={24} lg={8}>
              <Title level={5}>期限结构 (ATM)</Title>
              {(surface.term_structure || []).map((p: any) => (
                <div key={p.T} style={{ display: "flex", alignItems: "center", marginBottom: 6 }}>
                  <span style={{ width: 50 }}>{p.T.toFixed(2)}y</span>
                  <div style={{ flex: 1, background: "#f0f0f0", borderRadius: 4, height: 18 }}>
                    <div style={{
                      width: `${Math.min(p.iv * 200, 100)}%`, height: "100%",
                      background: "#1890ff", borderRadius: 4,
                    }} />
                  </div>
                  <span style={{ width: 60, textAlign: "right" }}>{(p.iv * 100).toFixed(1)}%</span>
                </div>
              ))}
              <Divider style={{ margin: "12px 0" }} />
              <Title level={5}>套利信号 ({arbSignals.length})</Title>
              {arbSignals.length ? arbSignals.map((s, i) => (
                <Card key={i} size="small" style={{ marginBottom: 8,
                  borderLeft: `3px solid ${dirColor[s.direction] || "#888"}` }}>
                  <Space>
                    <Tag color={dirColor[s.direction] === "#52c41a" ? "green" :
                      dirColor[s.direction] === "#ff4d4f" ? "red" : "default"}>
                      {s.type}
                    </Tag>
                    <Text strong style={{ color: dirColor[s.direction] }}>{s.direction}</Text>
                    <Text type="secondary">score={s.score.toFixed(2)}</Text>
                  </Space>
                  <div style={{ fontSize: 12, marginTop: 4 }}>{s.reason}</div>
                  <Text type="secondary" style={{ fontSize: 12 }}>建议: {s.suggested_strategy}</Text>
                </Card>
              )) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前曲面无套利信号" />}
            </Col>
          </Row>
        ) : <Empty description="点击「重建曲面」加载" />}
      </Card>

      {/* 期权-期货联合策略 */}
      <Card title="期权-期货联合策略决策">
        <Row gutter={24}>
          <Col xs={24} md={10}>
            <Space direction="vertical" style={{ width: "100%" }}>
              <div>
                <Text>期货方向</Text>
                <Select
                  value={comboDir}
                  style={{ width: "100%" }}
                  onChange={setComboDir}
                  options={[
                    { value: "BUY", label: "看多 (BUY)" },
                    { value: "SELL", label: "看空 (SELL)" },
                    { value: "HOLD", label: "观望 (HOLD)" },
                  ]}
                />
              </div>
              <div>
                <Text>IV Rank: {comboIvRank}</Text>
                <Slider min={0} max={100} value={comboIvRank} onChange={setComboIvRank} />
              </div>
              <div>
                <Text>Skew: {comboSkew.toFixed(2)}</Text>
                <Slider min={-0.2} max={0.2} step={0.01} value={comboSkew} onChange={setComboSkew} />
              </div>
              <Button type="primary" onClick={runCombo}>生成联合策略</Button>
            </Space>
          </Col>
          <Col xs={24} md={14}>
            {combo ? (
              <Card size="small" style={{ borderLeft: "4px solid #1890ff" }}>
                <Statistic title="推荐策略" value={combo.strategy_name} />
                <Divider style={{ margin: "8px 0" }} />
                <p><Text strong>期货腿:</Text> {combo.futures_direction}</p>
                <p><Text strong>期权腿:</Text> {combo.options_leg}</p>
                <p><Text strong>方向:</Text> {combo.adjusted_direction}
                  　<Text strong>置信度:</Text> {(combo.adjusted_confidence * 100).toFixed(0)}%</p>
                <p><Text type="secondary">{combo.reason}</Text></p>
                {combo.risk_notes && <Text type="warning">⚠️ {combo.risk_notes}</Text>}
              </Card>
            ) : <Empty description="设置参数后生成策略" />}
          </Col>
        </Row>
      </Card>
    </div>
  );
}
