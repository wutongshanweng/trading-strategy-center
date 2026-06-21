import { useEffect, useState, useCallback } from "react";
import {
  Row, Col, Card, Table, Tag, Button, Space, InputNumber, Modal, Form,
  Typography, Statistic, Tabs, message, Empty, Popconfirm,
} from "antd";
import {
  CloseCircleOutlined, StockOutlined, ArrowUpOutlined, ArrowDownOutlined,
  StarOutlined, ReloadOutlined, HistoryOutlined, ProfileOutlined,
} from "@ant-design/icons";
import { simTradingApi, type SimPosition } from "../services/macroNewsApi";

const { Text } = Typography;

function pnlSpan(v: number) {
  return <span style={{ color: v >= 0 ? "#52c41a" : "#ff4d4f" }}>{v >= 0 ? "+" : ""}{v.toLocaleString()}</span>;
}

export default function Trading() {
  const [positions, setPositions] = useState<SimPosition[]>([]);
  const [totalPnl, setTotalPnl] = useState(0);
  const [history, setHistory] = useState<any[]>([]);
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [openForm] = Form.useForm();
  const [openTarget, setOpenTarget] = useState<any | null>(null);

  const loadPositions = useCallback(async () => {
    try {
      const d = await simTradingApi.positions();
      setPositions(d.positions || []);
      setTotalPnl(d.total_pnl || 0);
    } catch { /* 后端未连接 */ }
  }, []);

  const loadHistory = useCallback(async () => {
    try { const d = await simTradingApi.history(); setHistory(d.history || []); } catch { /* */ }
  }, []);

  const loadWatch = useCallback(async () => {
    try { const d = await simTradingApi.watchlist(); setWatchlist(d.watchlist || []); } catch { /* */ }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.allSettled([loadPositions(), loadHistory(), loadWatch()]).finally(() => setLoading(false));
    const t = setInterval(loadPositions, 5000);  // 持仓实时价 5s 刷新
    return () => clearInterval(t);
  }, [loadPositions, loadHistory, loadWatch]);

  const closePos = async (id: string) => {
    try { await simTradingApi.close(id); message.success("已平仓"); loadPositions(); loadHistory(); }
    catch { message.error("平仓失败"); }
  };

  const removeWatch = async (id: string) => {
    try { await simTradingApi.removeWatch(id); message.success("已移除"); loadWatch(); }
    catch { message.error("操作失败"); }
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
      loadPositions();
    } catch { message.error("开仓失败"); }
  };

  const posColumns = [
    { title: "合约", dataIndex: "symbol", key: "symbol",
      render: (v: string, r: SimPosition) => <Space direction="vertical" size={0}><Text strong>{v}</Text><Text type="secondary" style={{ fontSize: 11 }}>{r.product_name}</Text></Space> },
    { title: "方向", dataIndex: "direction", key: "direction",
      render: (v: string) => <Tag color={v === "long" ? "red" : "green"}>{v === "long" ? "多头 ▲" : "空头 ▼"}</Tag> },
    { title: "数量", dataIndex: "qty", key: "qty" },
    { title: "开仓价", dataIndex: "entry_price", key: "entry_price" },
    { title: "现价", dataIndex: "current_price", key: "current_price",
      render: (v: number, r: SimPosition) => <Space size={4}><b>{v}</b><Tag style={{ fontSize: 10 }}>{r.quote_source}</Tag></Space> },
    { title: "浮动盈亏", dataIndex: "pnl", key: "pnl", sorter: (a: SimPosition, b: SimPosition) => a.pnl - b.pnl, render: pnlSpan },
    { title: "盈亏%", dataIndex: "pnl_pct", key: "pnl_pct",
      render: (v: number) => <span style={{ color: v >= 0 ? "#52c41a" : "#ff4d4f" }}>{v >= 0 ? "+" : ""}{v}%</span> },
    { title: "操作", key: "actions",
      render: (_: any, r: SimPosition) => (
        <Popconfirm title="确认平仓?" onConfirm={() => closePos(r.id)}>
          <Button size="small" danger icon={<CloseCircleOutlined />}>平仓</Button>
        </Popconfirm>
      ) },
  ];

  const watchColumns = [
    { title: "信号", dataIndex: "symbol", key: "symbol",
      render: (v: string, r: any) => <Space direction="vertical" size={0}><Text strong>{v} {r.product_name}</Text><Text type="secondary" style={{ fontSize: 11 }}>{"⭐".repeat(r.star_rating || 0)}</Text></Space> },
    { title: "方向", dataIndex: "direction", key: "direction",
      render: (v: string) => <Tag color={v === "BUY" ? "green" : v === "SELL" ? "red" : "gold"}>{v === "BUY" ? "做多" : v === "SELL" ? "做空" : "观望"}</Tag> },
    { title: "建议入场", dataIndex: "entry_price", key: "entry_price" },
    { title: "止盈", dataIndex: "take_profit", key: "take_profit", render: (v: number) => <span style={{ color: "#52c41a" }}>{v}</span> },
    { title: "止损", dataIndex: "stop_loss", key: "stop_loss", render: (v: number) => <span style={{ color: "#ff4d4f" }}>{v}</span> },
    { title: "操作", key: "actions",
      render: (_: any, r: any) => (
        <Space>
          <Button size="small" type="primary" ghost onClick={() => { setOpenTarget(r); openForm.setFieldsValue({ price: r.entry_price, qty: 1, stop_loss: r.stop_loss, take_profit: r.take_profit }); }}>模拟开仓</Button>
          <Button size="small" onClick={() => removeWatch(r.id)}>移除</Button>
        </Space>
      ) },
  ];

  const histColumns = [
    { title: "合约", dataIndex: "symbol", key: "symbol",
      render: (v: string, r: any) => <Text strong>{v} {r.product_name}</Text> },
    { title: "方向", dataIndex: "direction", key: "direction",
      render: (v: string) => <Tag color={v === "long" ? "red" : "green"}>{v === "long" ? "多" : "空"}</Tag> },
    { title: "开仓价", dataIndex: "entry_price", key: "entry_price" },
    { title: "平仓价", dataIndex: "close_price", key: "close_price" },
    { title: "数量", dataIndex: "qty", key: "qty" },
    { title: "盈亏", dataIndex: "pnl", key: "pnl", render: pnlSpan },
    { title: "平仓时间", dataIndex: "close_time", key: "close_time", render: (v: string) => v?.slice(0, 19).replace("T", " ") },
  ];

  const totalCost = positions.reduce((s, p) => s + p.entry_price * p.qty * (p.multiplier || 1), 0);

  return (
    <div>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>模拟交易</h2>
        <Button icon={<ReloadOutlined />} onClick={() => { loadPositions(); loadHistory(); loadWatch(); }}>刷新</Button>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}>
            <Statistic title="浮动盈亏" value={totalPnl} precision={0} suffix="¥"
              prefix={totalPnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              valueStyle={{ color: totalPnl >= 0 ? "#52c41a" : "#ff4d4f" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}><Statistic title="持仓数" value={positions.length} prefix={<StockOutlined />} valueStyle={{ color: "#4096ff" }} /></Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}><Statistic title="持仓市值" value={totalCost} precision={0} suffix="¥" /></Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}><Statistic title="关注信号" value={watchlist.length} prefix={<StarOutlined />} valueStyle={{ color: "#faad14" }} /></Card>
        </Col>
      </Row>

      <Card bordered={false}>
        <Tabs
          defaultActiveKey="positions"
          items={[
            {
              key: "positions", label: <span><StockOutlined /> 持仓 (实时)</span>,
              children: positions.length === 0 ? <Empty description="暂无持仓, 从关注列表或信号提醒开仓" /> :
                <Table dataSource={positions} columns={posColumns} rowKey="id" loading={loading} pagination={false} size="middle" />,
            },
            {
              key: "watch", label: <span><StarOutlined /> 关注列表</span>,
              children: watchlist.length === 0 ? <Empty description="暂无收藏信号, 去新闻宏观页收藏" /> :
                <Table dataSource={watchlist} columns={watchColumns} rowKey="id" pagination={false} size="middle" />,
            },
            {
              key: "orders", label: <span><ProfileOutlined /> 挂单</span>,
              children: <Empty description="限价挂单 (撮合引擎) 暂未启用 — 当前为市价模拟开仓" image={Empty.PRESENTED_IMAGE_SIMPLE} />,
            },
            {
              key: "history", label: <span><HistoryOutlined /> 历史成交</span>,
              children: history.length === 0 ? <Empty description="暂无历史成交" /> :
                <Table dataSource={history} columns={histColumns} rowKey={(r) => r.id + r.close_time} pagination={{ pageSize: 10 }} size="middle" />,
            },
          ]}
        />
      </Card>

      <Modal title="模拟开仓" open={!!openTarget} onOk={submitOpen} onCancel={() => setOpenTarget(null)} okText="确认开仓" cancelText="取消">
        {openTarget && (
          <Form form={openForm} layout="vertical">
            <Text>品种: <b>{openTarget.symbol} {openTarget.product_name}</b> · 方向: <b>{openTarget.direction === "SELL" ? "做空" : "做多"}</b></Text>
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
