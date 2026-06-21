import { useEffect, useState, useCallback } from "react";
import {
  Card, Row, Col, Tag, Typography, Spin, Empty, Statistic, Button,
  Timeline, Space, message, Tooltip, Divider, Modal, InputNumber, Form, Popover,
} from "antd";
import {
  ReloadOutlined, BellOutlined, ThunderboltOutlined, FundOutlined,
  CalendarOutlined, LinkOutlined, RiseOutlined, StarOutlined, StarFilled,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { macroNewsApi, alertApi, simTradingApi, type AlertSignal } from "../services/macroNewsApi";

const { Title, Text, Paragraph } = Typography;

const SENTI_BG: Record<string, string> = { "🟢": "#f6ffed", "🔴": "#fff1f0", "🟡": "#fffbe6" };
const DIR_CFG: Record<string, { cn: string; color: string; bg: string }> = {
  BUY: { cn: "做多", color: "#52c41a", bg: "#f6ffed" },
  SELL: { cn: "做空", color: "#ff4d4f", bg: "#fff1f0" },
  HOLD: { cn: "持有", color: "#faad14", bg: "#fffbe6" },
  WATCH: { cn: "观望", color: "#faad14", bg: "#fffbe6" },
};

function stars(n: number) {
  return "⭐".repeat(Math.max(0, Math.min(5, n)));
}

export default function MacroNews() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [dash, setDash] = useState<any>(null);
  const [signals, setSignals] = useState<AlertSignal[]>([]);
  const [sigLoading, setSigLoading] = useState(false);
  const [watchIds, setWatchIds] = useState<Set<string>>(new Set());
  const [openForm] = Form.useForm();
  const [openTarget, setOpenTarget] = useState<AlertSignal | null>(null);

  const loadDash = useCallback(async () => {
    setLoading(true);
    try {
      const d = await macroNewsApi.dashboard();
      setDash(d);
    } catch { /* 后端未连接 */ } finally { setLoading(false); }
  }, []);

  const loadSignals = useCallback(async () => {
    setSigLoading(true);
    try {
      const d = await alertApi.list(20);
      setSignals(d.signals || []);
    } catch { /* 后端未连接 */ } finally { setSigLoading(false); }
  }, []);

  const loadWatch = useCallback(async () => {
    try {
      const d = await simTradingApi.watchlist();
      setWatchIds(new Set((d.watchlist || []).map((w: any) => w.id)));
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    loadDash();
    loadSignals();
    loadWatch();
    const t1 = setInterval(loadDash, 3600000);   // 1h
    const t2 = setInterval(loadSignals, 300000);  // 5min (交易信号)
    return () => { clearInterval(t1); clearInterval(t2); };
  }, [loadDash, loadSignals, loadWatch]);

  const refreshSignals = async () => {
    setSigLoading(true);
    try {
      await alertApi.refresh();
      await loadSignals();
      message.success("信号已刷新");
    } catch { message.error("刷新失败"); } finally { setSigLoading(false); }
  };

  const toggleWatch = async (sig: AlertSignal) => {
    try {
      if (watchIds.has(sig.id)) {
        await simTradingApi.removeWatch(sig.id);
        setWatchIds((s) => { const n = new Set(s); n.delete(sig.id); return n; });
        message.success("已取消收藏");
      } else {
        await simTradingApi.addWatch(sig);
        setWatchIds((s) => new Set(s).add(sig.id));
        message.success("已收藏");
      }
    } catch { message.error("操作失败"); }
  };

  const submitOpen = async () => {
    const v = await openForm.validateFields();
    if (!openTarget) return;
    try {
      await simTradingApi.open({
        symbol: openTarget.symbol,
        direction: openTarget.direction === "SELL" ? "short" : "long",
        price: v.price, qty: v.qty, stop_loss: v.stop_loss, take_profit: v.take_profit,
      });
      message.success("模拟开仓成功");
      setOpenTarget(null);
    } catch { message.error("开仓失败"); }
  };

  const news = dash?.news?.items || [];
  const macro = dash?.macro?.indicators || [];
  const events = dash?.calendar?.events || [];
  const linkage = dash?.linkage || {};
  const outlook = dash?.outlook?.outlook || [];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Title level={3} style={{ margin: 0 }}><FundOutlined /> 新闻宏观仪表盘</Title>
        <Space>
          <Text type="secondary">{dash?.news?.updated_at ? `新闻更新 ${new Date(dash.news.updated_at).toLocaleString("zh-CN")}` : ""}</Text>
          <Button icon={<ReloadOutlined />} onClick={loadDash} loading={loading}>刷新全部</Button>
        </Space>
      </div>
      <Text type="secondary">市场快讯 + 宏观趋势 + 品种联动 + 远期展望。页面每小时自动刷新, 信号每 15 分钟刷新。</Text>
      <Divider style={{ margin: "12px 0" }} />

      {loading && !dash ? <div style={{ textAlign: "center", padding: 60 }}><Spin size="large" /></div> :
      <Row gutter={16}>
        {/* ───── 左栏 60% ───── */}
        <Col xs={24} lg={14}>
          {/* 实时快讯 */}
          <Card size="small" title={<><BellOutlined /> 实时快讯</>} style={{ marginBottom: 16 }}
            styles={{ body: { maxHeight: 360, overflowY: "auto" } }}>
            {news.length === 0 ? <Empty description="暂无新闻" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
              <Timeline
                items={news.slice(0, 30).map((n: any) => ({
                  color: n.label === "🟢" ? "green" : n.label === "🔴" ? "red" : "gold",
                  children: (
                    <div style={{ background: SENTI_BG[n.label] || "transparent", padding: "4px 8px", borderRadius: 4 }}>
                      <Popover
                        title={<span>{n.label} {n.title}</span>}
                        overlayStyle={{ maxWidth: 460 }}
                        trigger="hover"
                        content={<NewsPopoverContent n={n} />}>
                        <Text style={{ fontSize: 13, cursor: "pointer" }}>{n.label} {n.title}</Text>
                      </Popover>
                      <div>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {n.timestamp?.slice(5, 16)?.replace("T", " ")} · {n.source}
                        </Text>
                        {(n.products || []).map((p: string) => <Tag key={p} color="blue" style={{ marginLeft: 4, fontSize: 10 }}>{p}</Tag>)}
                      </div>
                    </div>
                  ),
                }))}
              />}
          </Card>

          {/* 宏观指标看板 */}
          <Card size="small" title={<><RiseOutlined /> 宏观指标看板</>} style={{ marginBottom: 16 }}>
            {macro.length === 0 ? <Empty description="暂无宏观数据" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
              <Row gutter={[12, 12]}>
                {macro.map((m: any) => (
                  <Col xs={12} sm={8} key={m.code}>
                    <Card size="small" style={{ textAlign: "center" }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>{m.name}</Text>
                      <div style={{ fontSize: 20, fontWeight: 600 }}>
                        {m.available ? m.value : "—"}
                        <span style={{ fontSize: 14, marginLeft: 4,
                          color: m.trend === "↑" ? "#52c41a" : m.trend === "↓" ? "#ff4d4f" : "#999" }}>
                          {m.trend}
                        </span>
                      </div>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {m.change != null ? `${m.change > 0 ? "+" : ""}${m.change}` : ""} {m.date?.slice(0, 7)}
                      </Text>
                    </Card>
                  </Col>
                ))}
              </Row>}
          </Card>

          {/* 宏观事件日历 */}
          <Card size="small" title={<><CalendarOutlined /> 宏观事件日历 (近 14 天)</>} style={{ marginBottom: 16 }}>
            {events.length === 0 ? <Empty description="近期无重大事件" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
              <Timeline
                items={events.map((e: any) => ({
                  color: "blue",
                  children: (
                    <Space>
                      <Text strong>{e.date?.slice(5)}</Text>
                      <Tag>{e.country}</Tag>
                      <Text>{e.event}</Text>
                      {(e.affects || []).slice(0, 4).map((p: string) => <Tag key={p} color="geekblue" style={{ fontSize: 10 }}>{p}</Tag>)}
                    </Space>
                  ),
                }))}
              />}
          </Card>
        </Col>

        {/* ───── 右栏 40% ───── */}
        <Col xs={24} lg={10}>
          <Card size="small"
            title={<><ThunderboltOutlined /> 交易信号提醒</>}
            extra={<Button size="small" icon={<ReloadOutlined />} onClick={refreshSignals} loading={sigLoading}>扫描</Button>}
            style={{ marginBottom: 16 }}>
            {sigLoading && signals.length === 0 ? <div style={{ textAlign: "center", padding: 30 }}><Spin /></div> :
              signals.length === 0 ? <Empty description="暂无活跃信号" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
              <Space direction="vertical" style={{ width: "100%" }} size={10}>
                {signals.map((s) => {
                  const cfg = DIR_CFG[s.direction] || DIR_CFG.WATCH;
                  return (
                    <Card key={s.id} size="small" hoverable
                      style={{ background: cfg.bg, borderLeft: `4px solid ${cfg.color}` }}
                      styles={{ body: { padding: 12 } }}
                      onClick={() => navigate(`/signal/${s.id}`)}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <Text strong style={{ color: cfg.color }}>
                          {s.symbol} {s.product_name} {cfg.cn}
                        </Text>
                        <Text>{stars(s.star_rating)}</Text>
                      </div>
                      <div style={{ fontSize: 12, margin: "4px 0" }}>
                        入场 <b>{s.entry_price}</b> · 止盈 <span style={{ color: "#52c41a" }}>{s.take_profit}</span> · 止损 <span style={{ color: "#ff4d4f" }}>{s.stop_loss}</span>
                      </div>
                      <Text type="secondary" style={{ fontSize: 11 }}>{s.reason}</Text>
                      <div style={{ marginTop: 8 }} onClick={(e) => e.stopPropagation()}>
                        <Space>
                          <Button size="small" type="primary" ghost
                            onClick={() => { setOpenTarget(s); openForm.setFieldsValue({ price: s.entry_price, qty: 1, stop_loss: s.stop_loss, take_profit: s.take_profit }); }}>
                            📈 模拟开仓
                          </Button>
                          <Tooltip title={watchIds.has(s.id) ? "取消收藏" : "收藏关注"}>
                            <Button size="small" icon={watchIds.has(s.id) ? <StarFilled style={{ color: "#faad14" }} /> : <StarOutlined />}
                              onClick={() => toggleWatch(s)}>收藏</Button>
                          </Tooltip>
                        </Space>
                      </div>
                    </Card>
                  );
                })}
              </Space>}
          </Card>
        </Col>
      </Row>}

      {/* ───── 联动分析 + 远期展望 ───── */}
      {dash && (
        <Card size="small" title={<><LinkOutlined /> 联动分析 + 远期趋势展望</>} style={{ marginTop: 4 }}>
          <Row gutter={24}>
            <Col xs={24} md={8}>
              <Text strong>当前市态: </Text>
              <Tag color="processing" style={{ fontSize: 14 }}>{linkage.market_state || "—"}</Tag>
              <Paragraph type="secondary" style={{ fontSize: 12, marginTop: 8 }}>{linkage.state_reason}</Paragraph>
            </Col>
            <Col xs={24} md={8}>
              <Text strong>新闻影响品种</Text>
              <div style={{ marginTop: 8 }}>
                {(linkage.news_impact || []).length === 0 ? <Text type="secondary">无品种相关新闻</Text> :
                  (linkage.news_impact || []).map((n: any) => (
                    <div key={n.product} style={{ fontSize: 13 }}>
                      {n.label} {n.product_cn}({n.product}) · {n.count} 条
                    </div>
                  ))}
              </div>
            </Col>
            <Col xs={24} md={8}>
              <Text strong>宏观 → 品种关联度</Text>
              <div style={{ marginTop: 8 }}>
                {(linkage.linkages || []).slice(0, 6).map((l: any, i: number) => (
                  <div key={i} style={{ fontSize: 13 }}>
                    {l.indicator}{l.trend} → {l.product_cn} <b style={{ color: l.corr > 0 ? "#52c41a" : "#ff4d4f" }}>{l.corr > 0 ? "+" : ""}{l.corr}</b>
                  </div>
                ))}
              </div>
            </Col>
          </Row>
          <Divider style={{ margin: "12px 0" }} />
          <Text strong><RiseOutlined /> 远期趋势</Text>
          <div style={{ marginTop: 8 }}>
            {outlook.map((o: any, i: number) => (
              <Paragraph key={i} style={{ marginBottom: 4, fontSize: 13 }}>• {o.text}</Paragraph>
            ))}
          </div>
        </Card>
      )}

      <Modal title="模拟开仓" open={!!openTarget} onOk={submitOpen} onCancel={() => setOpenTarget(null)} okText="确认开仓" cancelText="取消">
        {openTarget && (
          <Form form={openForm} layout="vertical">
            <Text>品种: <b>{openTarget.symbol} {openTarget.product_name}</b> · 方向: <b>{DIR_CFG[openTarget.direction]?.cn}</b></Text>
            <Form.Item name="price" label="开仓价" rules={[{ required: true }]} style={{ marginTop: 12 }}>
              <InputNumber style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="qty" label="数量 (手)" rules={[{ required: true }]}>
              <InputNumber style={{ width: "100%" }} min={1} />
            </Form.Item>
            <Row gutter={12}>
              <Col span={12}><Form.Item name="take_profit" label="止盈"><InputNumber style={{ width: "100%" }} /></Form.Item></Col>
              <Col span={12}><Form.Item name="stop_loss" label="止损"><InputNumber style={{ width: "100%" }} /></Form.Item></Col>
            </Row>
          </Form>
        )}
      </Modal>
    </div>
  );
}

function NewsPopoverContent({ n }: { n: any }) {
  const [full, setFull] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const loadFull = async () => {
    if (!n.url || loading || full) return;
    setLoading(true);
    try {
      const r = await macroNewsApi.newsDetail(n.url);
      setFull(r.available && r.content ? r.content : "(未能获取完整正文)");
    } catch { setFull("(获取失败)"); } finally { setLoading(false); }
  };
  return (
    <div style={{ maxWidth: 440 }}>
      <Paragraph style={{ marginBottom: 8, whiteSpace: "pre-wrap", maxHeight: 280, overflowY: "auto" }}>
        {full || n.content || "(无内容概述)"}
      </Paragraph>
      <Space wrap size={4}>
        <Tag color={n.label === "🟢" ? "green" : n.label === "🔴" ? "red" : "gold"}>
          {n.sentiment} {n.sentiment_score != null ? `(${n.sentiment_score})` : ""}
        </Tag>
        {(n.products || []).map((p: string) => <Tag key={p} color="blue">{p}</Tag>)}
        <Text type="secondary" style={{ fontSize: 11 }}>{n.source}</Text>
        {n.url && !full && (
          <Button size="small" type="link" loading={loading} onClick={loadFull} style={{ padding: 0 }}>
            展开全文
          </Button>
        )}
        {n.url && (
          <Button size="small" type="link" href={n.url} target="_blank" style={{ padding: 0 }}>
            原文
          </Button>
        )}
      </Space>
    </div>
  );
}
