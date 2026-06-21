import { useEffect, useState } from "react";
import {
  Card, Table, Tag, Typography, Statistic, Spin, Row, Col, Button, Progress, Empty, Tooltip, message, Modal, Input, InputNumber, Space,
} from "antd";
import {
  TrophyOutlined, FireOutlined, RiseOutlined, FallOutlined,
  CrownOutlined, GoldOutlined, ThunderboltOutlined, SafetyCertificateOutlined,
} from "@ant-design/icons";
import { getTournamentStandings, runTournamentBacktest, promoteCandidates, getLifecycle, graduateStrategy } from "../api/client";
import type { TournamentEntry } from "../api/client";
import { useTournamentStore } from "../store/useAppStore";

const { Text, Title } = Typography;

const MOCK_STANDINGS: TournamentEntry[] = [
  { rank: 1, strategy_name: "Alpha因子组合", score: 92.5, sharpe: 2.10, total_return: 0.521, trades: 89 },
  { rank: 2, strategy_name: "海龟交易法则", score: 88.1, sharpe: 1.95, total_return: 0.41, trades: 156 },
  { rank: 3, strategy_name: "双均线趋势跟踪", score: 85.3, sharpe: 1.82, total_return: 0.342, trades: 203 },
  { rank: 4, strategy_name: "套利动量策略", score: 79.8, sharpe: 1.67, total_return: 0.28, trades: 67 },
  { rank: 5, strategy_name: "RSI均值回归", score: 72.4, sharpe: 1.45, total_return: 0.221, trades: 178 },
  { rank: 6, strategy_name: "布林带突破", score: 65.2, sharpe: 0.95, total_return: 0.15, trades: 45 },
  { rank: 7, strategy_name: "统计套利策略", score: 58.9, sharpe: 0.78, total_return: 0.09, trades: 112 },
  { rank: 8, strategy_name: "动量突破策略", score: 52.1, sharpe: 0.61, total_return: 0.05, trades: 88 },
];

const rankColors: Record<number, string> = {
  1: "#ffd666",
  2: "#b37feb",
  3: "#4096ff",
};

const columns = [
  {
    title: "排名", dataIndex: "rank", key: "rank", width: 70,
    render: (v: number) => {
      if (v <= 3) {
        const icons = [<CrownOutlined key={1} />, <GoldOutlined key={2} />, <GoldOutlined key={3} />];
        return (
          <div style={{ fontSize: 20, color: rankColors[v] }}>
            {icons[v - 1]}
            <span style={{ marginLeft: 6, fontSize: 14, fontWeight: 600 }}>{v}</span>
          </div>
        );
      }
      return <Text strong>{v}</Text>;
    },
  },
  {
    title: "策略名称", dataIndex: "strategy_name", key: "strategy_name",
    render: (v: string) => <Text strong>{v}</Text>,
  },
  {
    title: "综合评分", dataIndex: "score", key: "score",
    sorter: (a: any, b: any) => a.score - b.score,
    render: (v: number) => (
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <Progress
          percent={v}
          size="small"
          strokeColor={v >= 80 ? "#00d4aa" : v >= 60 ? "#ffd666" : "#ff4d6a"}
          style={{ width: 100, margin: 0 }}
          showInfo={false}
        />
        <Tag color={v >= 80 ? "green" : v >= 60 ? "gold" : "red"}>{v.toFixed(1)}</Tag>
      </div>
    ),
  },
  {
    title: "夏普比率", dataIndex: "sharpe", key: "sharpe",
    sorter: (a: any, b: any) => a.sharpe - b.sharpe,
    render: (v: number) => (
      <span className={v >= 1.5 ? "text-green" : v >= 0 ? "text-yellow" : "text-red"}>
        {v.toFixed(2)}
      </span>
    ),
  },
  {
    title: "累计收益", dataIndex: "total_return", key: "total_return",
    sorter: (a: any, b: any) => a.total_return - b.total_return,
    render: (v: number) => (
      <span className={v >= 0 ? "text-green" : "text-red"}>
        {(v * 100).toFixed(1)}%
      </span>
    ),
  },
  {
    title: "交易次数", dataIndex: "trades", key: "trades",
  },
];

export default function Tournament() {
  const { standings, setStandings, status, setStatus } = useTournamentStore();
  const [running, setRunning] = useState(false);
  const [promoting, setPromoting] = useState(false);
  const [lifecycle, setLifecycle] = useState<{ champions: any[]; challengers: any[]; retired: any[] }>({ champions: [], challengers: [], retired: [] });
  const [gradTarget, setGradTarget] = useState<any | null>(null);
  const [approver, setApprover] = useState("");
  const [allocation, setAllocation] = useState(0.1);

  const load = () => {
    setStatus("loading");
    getTournamentStandings()
      .then((res) => setStandings(res.data))
      .catch(() => setStandings(MOCK_STANDINGS))
      .finally(() => setStatus("success"));
  };

  const loadLifecycle = () => {
    getLifecycle().then((res) => setLifecycle(res.data)).catch(() => {});
  };

  useEffect(() => { load(); loadLifecycle(); }, []);

  const runBacktest = async () => {
    setRunning(true);
    message.loading({ content: "正在对全部策略跑真实回测 (可能数十秒)...", key: "bt", duration: 0 });
    try {
      const res = await runTournamentBacktest();
      const d = res.data;
      message.success({
        content: `回测完成: ${d.strategies_with_trades} 个策略有成交, 冠军 ${d.top_strategy} (夏普 ${d.top_sharpe?.toFixed?.(2) ?? d.top_sharpe}), 下线 ${d.retired?.length ?? 0}`,
        key: "bt", duration: 5,
      });
      load();
    } catch {
      message.error({ content: "回测失败, 检查后端", key: "bt" });
    } finally { setRunning(false); }
  };

  const runPromote = async () => {
    setPromoting(true);
    message.loading({ content: "晋升验证中: 对排行榜策略跑样本外 walk-forward (较慢)...", key: "pm", duration: 0 });
    try {
      const res = await promoteCandidates();
      const d = res.data;
      message.success({
        content: `验证完成: 评估 ${d.evaluated}, 晋级 ${d.promoted?.length ?? 0}, 市态冠军 ${Object.keys(d.champions_by_regime || {}).join("/") || "无"}`,
        key: "pm", duration: 6,
      });
      loadLifecycle();
    } catch {
      message.error({ content: "晋升验证失败 (需先跑回测有候选)", key: "pm" });
    } finally { setPromoting(false); }
  };

  const doGraduate = async () => {
    if (!gradTarget || !approver.trim()) { message.warning("请填写批准人"); return; }
    try {
      const res = await graduateStrategy(gradTarget.name, approver.trim(), allocation);
      if (res.data.ok) { message.success(`${gradTarget.name} 已毕业为 champion`); loadLifecycle(); }
      else message.error(res.data.reason || "毕业失败");
    } catch { message.error("毕业请求失败"); }
    finally { setGradTarget(null); setApprover(""); }
  };

  const topScore = standings[0]?.score ?? 0;
  const avgSharpe = standings.length > 0
    ? standings.reduce((s, e) => s + e.sharpe, 0) / standings.length
    : 0;

  const lifecycleColumns = [
    { title: "策略", dataIndex: "name", key: "name", render: (v: string) => <Text strong>{v}</Text> },
    { title: "状态", dataIndex: "status", key: "status",
      render: (v: string) => <Tag color={v === "champion" ? "gold" : v === "challenger" ? "blue" : "default"}>{v === "champion" ? "冠军" : v === "challenger" ? "考察中" : "已下线"}</Tag> },
    { title: "市态", dataIndex: "regime", key: "regime", render: (v: string) => <Tag>{v}</Tag> },
    { title: "评估次数", dataIndex: "n_evals", key: "n_evals" },
    { title: "通过率", dataIndex: "pass_rate", key: "pass_rate", render: (v: number) => `${(v * 100).toFixed(0)}%` },
    { title: "平均OOS夏普", dataIndex: "avg_oos_sharpe", key: "avg_oos_sharpe",
      render: (v: number) => <span className={v >= 0.3 ? "text-green" : "text-red"}>{v.toFixed(2)}</span> },
    { title: "分配", dataIndex: "allocation", key: "allocation", render: (v: number) => v > 0 ? `${(v * 100).toFixed(0)}%` : "-" },
    { title: "操作", key: "actions",
      render: (_: any, r: any) => r.status === "challenger" ? (
        <Tooltip title={r.eligible ? "达标, 可毕业" : "未达毕业门槛"}>
          <Button size="small" type="primary" ghost disabled={!r.eligible}
            onClick={() => { setGradTarget(r); setAllocation(0.1); }}>批准毕业</Button>
        </Tooltip>
      ) : null },
  ];

  const allLifecycle = [...lifecycle.champions, ...lifecycle.challengers, ...lifecycle.retired];

  return (
    <Spin spinning={status === "loading"}>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>
          <TrophyOutlined style={{ color: "#ffd666", marginRight: 8 }} />
          策略锦标赛
        </h2>
        <Space>
          <Button type="primary" icon={<ThunderboltOutlined />} loading={running} onClick={runBacktest}>
            跑真实回测
          </Button>
          <Button icon={<SafetyCertificateOutlined />} loading={promoting} onClick={runPromote}>
            晋升验证
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <Statistic title="参赛策略" value={standings.length} prefix={<FireOutlined />} valueStyle={{ color: "#4096ff" }} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <Statistic title="最高评分" value={topScore} precision={1} prefix={<CrownOutlined />} valueStyle={{ color: "#ffd666" }} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <Statistic title="平均夏普" value={avgSharpe} precision={2} valueStyle={{ color: avgSharpe >= 1 ? "#00d4aa" : "#ffd666" }} />
          </Card>
        </Col>
      </Row>

      <Card bordered={false}>
        <Table
          dataSource={standings}
          columns={columns}
          rowKey="rank"
          pagination={false}
          size="middle"
        />
      </Card>

      {/* Badge rules */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <div style={{ textAlign: "center" }}>
              <CrownOutlined style={{ fontSize: 32, color: "#ffd666", marginBottom: 8 }} />
              <div><Tag color="gold">金牌</Tag> 评分 ≥ 85</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <div style={{ textAlign: "center" }}>
              <GoldOutlined style={{ fontSize: 32, color: "#b37feb", marginBottom: 8 }} />
              <div><Tag color="purple">银牌</Tag> 评分 ≥ 70</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <div style={{ textAlign: "center" }}>
              <GoldOutlined style={{ fontSize: 32, color: "#4096ff", marginBottom: 8 }} />
              <div><Tag color="blue">铜牌</Tag> 评分 ≥ 60</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Champion/Challenger 生命周期 (阶段4) */}
      <Card
        title={<span><SafetyCertificateOutlined style={{ color: "#52c41a", marginRight: 8 }} />策略晋级生命周期 (Champion / Challenger)</span>}
        bordered={false}
        style={{ marginTop: 24 }}
        extra={<Text type="secondary" style={{ fontSize: 12 }}>新策略经"晋升验证"入考察 → 连续达标 → 人工批准毕业为冠军</Text>}
      >
        {allLifecycle.length === 0 ? (
          <Empty description="暂无考察/冠军策略, 点击上方「晋升验证」开始" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        ) : (
          <Table dataSource={allLifecycle} columns={lifecycleColumns} rowKey="name" pagination={false} size="small" />
        )}
      </Card>

      <Modal title="批准毕业为 Champion" open={!!gradTarget} onOk={doGraduate} onCancel={() => setGradTarget(null)} okText="确认毕业" cancelText="取消">
        {gradTarget && (
          <Space direction="vertical" style={{ width: "100%" }}>
            <Text>策略: <b>{gradTarget.name}</b> · 平均OOS夏普 <b>{gradTarget.avg_oos_sharpe}</b> · 通过率 <b>{(gradTarget.pass_rate * 100).toFixed(0)}%</b></Text>
            <Text type="secondary" style={{ fontSize: 12 }}>毕业后该策略获得资金分配权重 (记录性, 无真实下单)。这是人工安全闸门。</Text>
            <div><Text>批准人: </Text><Input value={approver} onChange={(e) => setApprover(e.target.value)} placeholder="你的名字" style={{ width: 200 }} /></div>
            <div><Text>资金分配权重: </Text><InputNumber value={allocation} onChange={(v) => setAllocation(v ?? 0.1)} min={0} max={1} step={0.05} /></div>
          </Space>
        )}
      </Modal>
    </Spin>
  );
}
