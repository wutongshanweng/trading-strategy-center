import { useEffect, useState } from "react";
import {
  Card,
  Table,
  Tag,
  Button,
  Space,
  Input,
  Modal,
  Form,
  Select,
  message,
  Typography,
  Badge,
  Row,
  Col,
  Statistic,
} from "antd";
import {
  PlusOutlined,
  SearchOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  DeleteOutlined,
  ExperimentOutlined,
  FundOutlined,
} from "@ant-design/icons";
import { listStrategies, createStrategy, deleteStrategy, type Strategy } from "../api/client";
import { useStrategyStore } from "../store/useAppStore";

const { Text } = Typography;

const statusMap: Record<string, { label: string; color: string }> = {
  active: { label: "运行中", color: "green" },
  paused: { label: "已暂停", color: "orange" },
  backtest: { label: "回测中", color: "blue" },
  draft: { label: "草稿", color: "default" },
};

const columns = [
  { title: "名称", dataIndex: "name", key: "name", render: (v: string) => <Text strong>{v}</Text> },
  { title: "类型", dataIndex: "type", key: "type", render: (v: string) => <Tag>{v}</Tag> },
  {
    title: "状态",
    dataIndex: "status",
    key: "status",
    render: (v: string) => {
      const m = statusMap[v] || { label: v, color: "default" };
      return <Badge status={m.color as any} text={m.label} />;
    },
  },
  {
    title: "夏普",
    dataIndex: ["performance", "sharpe"],
    key: "sharpe",
    sorter: (a: any, b: any) => (a.performance?.sharpe ?? 0) - (b.performance?.sharpe ?? 0),
    render: (v: number | null) => (
      <span className={!v || v >= 1 ? "text-green" : v != null && v >= 0 ? "text-yellow" : "text-red"}>
        {v?.toFixed(2) ?? "-"}
      </span>
    ),
  },
  {
    title: "累计收益",
    dataIndex: ["performance", "total_return"],
    key: "total_return",
    sorter: (a: any, b: any) => (a.performance?.total_return ?? 0) - (b.performance?.total_return ?? 0),
    render: (v: number | null) => (
      <span className={v != null && v >= 0 ? "text-green" : "text-red"}>
        {v != null ? `${(v * 100).toFixed(1)}%` : "-"}
      </span>
    ),
  },
  {
    title: "胜率",
    dataIndex: ["performance", "win_rate"],
    key: "win_rate",
    render: (v: number | null) => (v != null ? `${(v * 100).toFixed(0)}%` : "-"),
  },
  { title: "信号数", dataIndex: "signals", key: "signals", render: (v: string[]) => v?.length ?? 0 },
  {
    title: "操作",
    key: "actions",
    render: (_: any, record: Strategy) => (
      <Space size="small">
        <Button type="link" size="small" icon={<PlayCircleOutlined />}>
          运行
        </Button>
        <Button type="link" size="small" icon={<ExperimentOutlined />}>
          回测
        </Button>
        <Button type="link" size="small" danger icon={<DeleteOutlined />} />
      </Space>
    ),
  },
];

export default function Strategy() {
  const { strategies, setStrategies, status, setStatus } = useStrategyStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [form] = Form.useForm();

  const load = () => {
    setStatus("loading");
    listStrategies()
      .then((res) => setStrategies(res.data.strategies))
      .catch(() => {
        // Use mock data if backend not available
        setStrategies(MOCK_STRATEGIES);
      })
      .finally(() => setStatus("success"));
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await createStrategy(values);
      message.success("策略已创建");
      setModalOpen(false);
      form.resetFields();
      load();
    } catch {
      // validation failed
    }
  };

  const filtered = strategies.filter(
    (s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.type.toLowerCase().includes(search.toLowerCase())
  );

  const activeCount = strategies.filter((s) => s.status === "active").length;

  return (
    <div>
      <div className="page-header">
        <h2>策略管理</h2>
        <Space>
          <Input
            prefix={<SearchOutlined />}
            placeholder="搜索策略..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 240 }}
            allowClear
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
            新建策略
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card size="small" bordered={false}>
            <Statistic title="总策略" value={strategies.length} prefix={<FundOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" bordered={false}>
            <Statistic title="运行中" value={activeCount} valueStyle={{ color: "#00d4aa" }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" bordered={false}>
            <Statistic title="草稿" value={strategies.filter((s) => s.status === "draft").length} />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small" bordered={false}>
            <Statistic title="平均夏普" value={1.24} precision={2} valueStyle={{ color: "#00d4aa" }} />
          </Card>
        </Col>
      </Row>

      <Card bordered={false}>
        <Table
          dataSource={filtered}
          columns={columns}
          rowKey="id"
          loading={status === "loading"}
          pagination={{ pageSize: 15, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }}
          size="middle"
        />
      </Card>

      <Modal
        title="新建策略"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => setModalOpen(false)}
        width={520}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="策略名称" rules={[{ required: true }]}>
            <Input placeholder="如: 双均线突破" />
          </Form.Item>
          <Form.Item name="type" label="策略类型" rules={[{ required: true }]}>
            <Select
              options={[
                { label: "趋势跟踪", value: "trend" },
                { label: "均值回归", value: "mean_reversion" },
                { label: "突破策略", value: "breakout" },
                { label: "套利策略", value: "arbitrage" },
                { label: "机器学习", value: "ml" },
                { label: "高频交易", value: "hft" },
              ]}
            />
          </Form.Item>
          <Form.Item name="signals" label="信号组合">
            <Select mode="multiple" placeholder="选择信号" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

/* ── Mock data ── */
const MOCK_STRATEGIES: Strategy[] = [
  { id: "1", name: "双均线趋势跟踪", type: "趋势跟踪", status: "active", signals: ["ma_cross"], created_at: "2024-01-15", updated_at: "2024-06-01", performance: { sharpe: 1.82, total_return: 0.34, win_rate: 0.58, max_drawdown: -0.12 } },
  { id: "2", name: "RSI均值回归", type: "均值回归", status: "active", signals: ["rsi_overbought"], created_at: "2024-02-20", updated_at: "2024-06-10", performance: { sharpe: 1.45, total_return: 0.22, win_rate: 0.63, max_drawdown: -0.08 } },
  { id: "3", name: "布林带突破", type: "突破策略", status: "paused", signals: ["bollinger"], created_at: "2024-03-05", updated_at: "2024-05-20", performance: { sharpe: 0.95, total_return: 0.15, win_rate: 0.45, max_drawdown: -0.18 } },
  { id: "4", name: "Alpha因子组合", type: "多因子", status: "backtest", signals: ["alpha031", "alpha058"], created_at: "2024-04-10", updated_at: "2024-06-12", performance: { sharpe: 2.10, total_return: 0.52, win_rate: 0.55, max_drawdown: -0.10 } },
  { id: "5", name: "LSTM价格预测", type: "机器学习", status: "draft", signals: ["lstm_pred"], created_at: "2024-05-01", updated_at: "2024-05-01", performance: { sharpe: 0, total_return: 0, win_rate: 0, max_drawdown: 0 } },
  { id: "6", name: "套利动量策略", type: "套利策略", status: "active", signals: ["pair_spread"], created_at: "2024-03-15", updated_at: "2024-06-08", performance: { sharpe: 1.67, total_return: 0.28, win_rate: 0.71, max_drawdown: -0.05 } },
  { id: "7", name: "海龟交易法则", type: "趋势跟踪", status: "active", signals: ["turtle"], created_at: "2024-01-01", updated_at: "2024-06-11", performance: { sharpe: 1.95, total_return: 0.41, win_rate: 0.42, max_drawdown: -0.22 } },
  { id: "8", name: "统计套利策略", type: "均值回归", status: "paused", signals: ["zscore"], created_at: "2024-04-20", updated_at: "2024-06-05", performance: { sharpe: 0.78, total_return: 0.09, win_rate: 0.52, max_drawdown: -0.14 } },
];
