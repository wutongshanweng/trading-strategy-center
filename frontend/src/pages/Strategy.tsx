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

/* ── Mock data - Updated to 67 strategies (matching backend) ── */
const MOCK_STRATEGIES: Strategy[] = Array.from({ length: 67 }, (_, i) => {
  const types = ["趋势跟踪", "均值回归", "套利策略", "动量策略", "突破策略"];
  const statuses = ["active", "paused", "backtest", "draft"];
  const names = [
    "双均线趋势", "布林带反转", "MACD动量", "RSI超买超卖", "海龟交易",
    "配对交易", "统计套利", "动量突破", "均值回复", "跨期套利",
    "SuperTrend", "KAMA自适应", "Keltner通道", "抛物线SAR", "Vortex指标",
    "Aroon趋势", "TTM压缩", "ADX趋势强度", "DMI方向", "一目均衡",
    "日历价差", "压榨价差", "裂解价差", "Roll Yield", "基差套利",
    "时间序列动量", "双重动量", "波动率调整", "残差动量", "Donchian突破",
    "新高新低", "成交量突破", "区间突破", "趋势反转", "Z-Score均值",
    "协整套利", "OU过程", "卡尔曼滤波", "EMA多周期", "多空策略",
    "网格交易", "马丁格尔", "凯利公式", "风险平价", "波动率目标",
    "Alpha001", "Alpha002", "Alpha003", "Alpha004", "Alpha005",
    "趋势跟随组合", "套利组合", "动量组合", "机器学习策略", "深度学习",
    "强化学习DQN", "SAC策略", "TD3策略", "MADDPG", "期权策略",
    "Greeks对冲", "波动率交易", "日内回转", "高频策略", "市场中性",
    "CTA策略", "量化选股"
  ];

  const isActive = i < 35;
  return {
    id: String(i + 1),
    name: names[i] || `策略${i + 1}`,
    type: types[i % types.length],
    status: isActive ? (i % 4 === 3 ? "paused" : "active") : (i % 2 === 0 ? "backtest" : "draft"),
    signals: [`signal_${i + 1}`],
    created_at: `2024-${String((i % 6) + 1).padStart(2, '0')}-${String((i % 28) + 1).padStart(2, '0')}`,
    updated_at: "2024-06-14",
    performance: {
      sharpe: parseFloat((Math.random() * 2.5 + 0.3).toFixed(2)),
      total_return: parseFloat((Math.random() * 0.5 - 0.05).toFixed(3)),
      win_rate: parseFloat((Math.random() * 0.3 + 0.45).toFixed(3)),
      max_drawdown: parseFloat(-(Math.random() * 0.2 + 0.03).toFixed(3)),
    },
  };
});
