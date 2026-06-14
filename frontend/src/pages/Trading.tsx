import { useEffect, useState, useRef } from "react";
import {
  Row, Col, Card, Table, Tag, Button, Space, InputNumber, Select, Modal, Form,
  Typography, Statistic, Tabs, message, Badge, Tooltip,
} from "antd";
import {
  PlusOutlined, CloseCircleOutlined, StockOutlined,
  ArrowUpOutlined, ArrowDownOutlined, DollarOutlined,
} from "@ant-design/icons";
import { createChart, ColorType, IChartApi } from "lightweight-charts";
import { getPositions, getOrders, placeOrder, cancelOrder, getMarketData } from "../api/client";
import type { Position, Order } from "../api/client";
import { useTradingStore } from "../store/useAppStore";

const { Text, Title } = Typography;

/* ── Mock data ── */
const MOCK_POSITIONS: Position[] = [
  { symbol: "RB2401", direction: "long", volume: 100, entry_price: 3890, current_price: 3950, pnl: 6000, pnl_pct: 1.54, open_time: "2024-06-01 09:30" },
  { symbol: "CU2402", direction: "short", volume: 20, entry_price: 72000, current_price: 71500, pnl: 10000, pnl_pct: 0.69, open_time: "2024-06-03 10:15" },
  { symbol: "AU2406", direction: "long", volume: 50, entry_price: 552, current_price: 558, pnl: 3000, pnl_pct: 1.09, open_time: "2024-06-05 14:00" },
  { symbol: "MA2409", direction: "short", volume: 200, entry_price: 2610, current_price: 2635, pnl: -5000, pnl_pct: -0.96, open_time: "2024-06-07 09:45" },
];

const MOCK_ORDERS: Order[] = [
  { id: "ord001", symbol: "RB2401", side: "buy", type: "limit", price: 3920, volume: 50, filled: 0, status: "pending", created_at: "2024-06-10 10:30" },
  { id: "ord002", symbol: "CU2402", side: "sell", type: "market", price: 71500, volume: 10, filled: 10, status: "filled", created_at: "2024-06-10 10:25" },
  { id: "ord003", symbol: "AU2406", side: "buy", type: "limit", price: 550, volume: 30, filled: 0, status: "cancelled", created_at: "2024-06-09 14:00" },
  { id: "ord004", symbol: "MA2409", side: "sell", type: "limit", price: 2600, volume: 100, filled: 50, status: "pending", created_at: "2024-06-10 09:15" },
];

const MOCK_CANDLES = Array.from({ length: 100 }, (_, i) => {
  const base = 3900 + Math.sin(i / 8) * 80 + Math.random() * 20;
  return {
    time: (new Date(2024, 2, i + 1).getTime() / 1000) as any,
    open: base + (Math.random() - 0.5) * 20,
    high: base + Math.random() * 25 + 10,
    low: base - Math.random() * 25 - 10,
    close: base + (Math.random() - 0.5) * 20,
  };
});

/* ── Kline Chart ── */
function KlineChart({ data }: { data: typeof MOCK_CANDLES }) {
  const chartRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 400,
      layout: {
        background: { type: ColorType.Solid, color: "#1a1a2e" },
        textColor: "#8c8c8c",
      },
      grid: {
        vertLines: { color: "#2a2a2a" },
        horzLines: { color: "#2a2a2a" },
      },
      rightPriceScale: { borderColor: "#303030" },
      timeScale: { borderColor: "#303030" },
    });

    const candle = chart.addCandlestickSeries({
      upColor: "#00d4aa",
      downColor: "#ff4d6a",
      borderDownColor: "#ff4d6a",
      borderUpColor: "#00d4aa",
      wickDownColor: "#ff4d6a",
      wickUpColor: "#00d4aa",
    });
    candle.setData(data);
    chart.timeScale().fitContent();

    const handleResize = () => {
      if (chartRef.current) chart.applyOptions({ width: chartRef.current.clientWidth });
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [data]);

  return <div ref={chartRef} style={{ width: "100%", height: 400 }} />;
}

const positionColumns = [
  { title: "合约", dataIndex: "symbol", key: "symbol", render: (v: string) => <Text strong>{v}</Text> },
  {
    title: "方向", dataIndex: "direction", key: "direction",
    render: (v: string) => (
      <Tag color={v === "long" ? "red" : "green"}>{v === "long" ? "多头 ▲" : "空头 ▼"}</Tag>
    ),
  },
  { title: "持仓量", dataIndex: "volume", key: "volume" },
  { title: "开仓价", dataIndex: "entry_price", key: "entry_price", render: (v: number) => v.toFixed(1) },
  { title: "现价", dataIndex: "current_price", key: "current_price", render: (v: number) => v.toFixed(1) },
  {
    title: "盈亏", dataIndex: "pnl", key: "pnl",
    render: (v: number) => (
      <span className={v >= 0 ? "text-green" : "text-red"}>
        {v >= 0 ? "+" : ""}{v.toLocaleString()}
      </span>
    ),
    sorter: (a: any, b: any) => a.pnl - b.pnl,
  },
  {
    title: "盈亏%", dataIndex: "pnl_pct", key: "pnl_pct",
    render: (v: number) => (
      <span className={v >= 0 ? "text-green" : "text-red"}>
        {v >= 0 ? "+" : ""}{(v * 100).toFixed(2)}%
      </span>
    ),
    sorter: (a: any, b: any) => a.pnl_pct - b.pnl_pct,
  },
  { title: "开仓时间", dataIndex: "open_time", key: "open_time" },
  {
    title: "操作", key: "actions",
    render: () => <Button size="small" danger icon={<CloseCircleOutlined />}>平仓</Button>,
  },
];

const orderColumns = [
  { title: "ID", dataIndex: "id", key: "id", render: (v: string) => <Text code>{v}</Text> },
  { title: "合约", dataIndex: "symbol", key: "symbol" },
  {
    title: "方向", dataIndex: "side", key: "side",
    render: (v: string) => <Tag color={v === "buy" ? "red" : "green"}>{v === "buy" ? "买入" : "卖出"}</Tag>,
  },
  { title: "类型", dataIndex: "type", key: "type", render: (v: string) => <Tag>{v.toUpperCase()}</Tag> },
  { title: "价格", dataIndex: "price", key: "price", render: (v: number) => v.toFixed(1) },
  { title: "数量", dataIndex: "volume", key: "volume" },
  { title: "已成交", dataIndex: "filled", key: "filled" },
  {
    title: "状态", dataIndex: "status", key: "status",
    render: (v: string) => {
      const m: Record<string, { label: string; color: string }> = {
        pending: { label: "待成交", color: "processing" },
        filled: { label: "已成交", color: "success" },
        cancelled: { label: "已撤销", color: "default" },
        rejected: { label: "已拒绝", color: "error" },
      };
      return <Badge status={m[v]?.color as any} text={m[v]?.label ?? v} />;
    },
  },
  { title: "时间", dataIndex: "created_at", key: "created_at" },
  {
    title: "操作", key: "actions",
    render: (_: any, r: Order) =>
      r.status === "pending" ? (
        <Button size="small" onClick={() => cancelOrder(r.id)}>撤单</Button>
      ) : null,
  },
];

export default function Trading() {
  const { positions, setPositions, orders, setOrders, status, setStatus } = useTradingStore();
  const [orderOpen, setOrderOpen] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    setStatus("loading");
    Promise.allSettled([getPositions(), getOrders()]).then(([p, o]) => {
      if (p.status === "fulfilled") setPositions(p.value.data);
      else setPositions(MOCK_POSITIONS);
      if (o.status === "fulfilled") setOrders(o.value.data);
      else setOrders(MOCK_ORDERS);
      setStatus("success");
    });
  }, []);

  const handleOrder = async () => {
    try {
      const values = await form.validateFields();
      await placeOrder(values);
      message.success("订单已提交");
      setOrderOpen(false);
      form.resetFields();
    } catch { /* validation */ }
  };

  const totalPnl = positions.reduce((s, p) => s + p.pnl, 0);
  const totalInvested = positions.reduce((s, p) => s + p.entry_price * p.volume, 0);

  return (
    <div>
      <div className="page-header">
        <h2>交易监控</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOrderOpen(true)}>
          下单
        </Button>
      </div>

      {/* Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}>
            <Statistic
              title="持仓盈亏"
              value={totalPnl}
              prefix={totalPnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              precision={0}
              valueStyle={{ color: totalPnl >= 0 ? "#00d4aa" : "#ff4d6a" }}
              suffix="¥"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}>
            <Statistic title="持仓合约" value={positions.length} prefix={<StockOutlined />} valueStyle={{ color: "#4096ff" }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}>
            <Statistic title="占用保证金" value={totalInvested} prefix="¥" precision={0} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card size="small" bordered={false}>
            <Statistic title="委托单数" value={orders.length} prefix={<DollarOutlined />} valueStyle={{ color: "#b37feb" }} />
          </Card>
        </Col>
      </Row>

      {/* Chart + Positions */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={14}>
          <Card title="RB2401 K线图" bordered={false} size="small">
            <KlineChart data={MOCK_CANDLES} />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="快速下单" bordered={false} size="small">
            <Form layout="vertical" size="small">
              <Form.Item label="合约">
                <Select defaultValue="RB2401" options={["RB2401", "CU2402", "AU2406", "MA2409", "SC2403"].map((s) => ({ label: s, value: s }))} />
              </Form.Item>
              <Row gutter={8}>
                <Col span={12}>
                  <Form.Item label="方向">
                    <Select defaultValue="buy" options={[{ label: "买入开仓", value: "buy" }, { label: "卖出开仓", value: "sell" }]} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="类型">
                    <Select defaultValue="limit" options={[{ label: "限价", value: "limit" }, { label: "市价", value: "market" }]} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={8}>
                <Col span={12}>
                  <Form.Item label="价格">
                    <InputNumber style={{ width: "100%" }} defaultValue={3920} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="数量">
                    <InputNumber style={{ width: "100%" }} defaultValue={10} />
                  </Form.Item>
                </Col>
              </Row>
              <Button type="primary" block icon={<PlusOutlined />}>提交委托</Button>
            </Form>
          </Card>
        </Col>
      </Row>

      {/* Positions Table */}
      <Card
        title={<span><ArrowUpOutlined style={{ color: "#00d4aa", marginRight: 8 }} />持仓列表</span>}
        bordered={false}
        style={{ marginBottom: 24 }}
      >
        <Table
          dataSource={positions}
          columns={positionColumns}
          rowKey="symbol"
          loading={status === "loading"}
          pagination={false}
          size="middle"
        />
      </Card>

      {/* Orders Table */}
      <Card
        title={<span><DollarOutlined style={{ marginRight: 8 }} />委托记录</span>}
        bordered={false}
      >
        <Table
          dataSource={orders}
          columns={orderColumns}
          rowKey="id"
          loading={status === "loading"}
          pagination={{ pageSize: 10 }}
          size="middle"
        />
      </Card>

      {/* Order Modal */}
      <Modal title="下单" open={orderOpen} onOk={handleOrder} onCancel={() => setOrderOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="symbol" label="合约" rules={[{ required: true }]}>
            <Select options={["RB2401", "CU2402", "AU2406", "MA2409"].map((s) => ({ label: s, value: s }))} />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="side" label="方向" rules={[{ required: true }]}>
                <Select options={[{ label: "买入", value: "buy" }, { label: "卖出", value: "sell" }]} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="type" label="类型" rules={[{ required: true }]}>
                <Select options={[{ label: "限价", value: "limit" }, { label: "市价", value: "market" }]} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="price" label="价格">
            <InputNumber style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="volume" label="数量" rules={[{ required: true }]}>
            <InputNumber style={{ width: "100%" }} min={1} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
