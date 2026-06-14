import { useEffect, useState, useRef } from "react";
import {
  Card, Row, Col, Statistic, Table, Tag, Typography, Spin,
  Progress, Timeline, Badge, Space,
} from "antd";
import {
  CheckCircleOutlined, CloseCircleOutlined,
  SyncOutlined, DashboardOutlined,
  RiseOutlined, FallOutlined, ApiOutlined, SafetyOutlined,
  LineChartOutlined, BellOutlined, ThunderboltOutlined,
} from "@ant-design/icons";

const { Text, Title } = Typography;

// ─── Mock Data ───────────────────────────────────────────────────

const METRICS = {
  system: {
    cpu: 45.2,
    memory: 62.8,
    uptime_hours: 24.5,
    active_connections: 3,
    queue_depth: 12,
    api_latency_ms: 128,
  },
  trading: {
    total_trades_today: 47,
    win_rate: 0.632,
    daily_pnl: 12580,
    max_drawdown: 0.032,
    sharpe_ratio: 1.85,
    positions_count: 5,
  },
  risk: {
    var_95: 0.015,
    cvar_95: 0.022,
    volatility: 0.018,
    kelly_fraction: 0.35,
    exposure_pct: 42.5,
  },
};

const ACTIVE_ALERTS = [
  { key: "1", severity: "critical", rule: "High CPU Usage", metric: "cpu", value: 92, threshold: 80, time: "2 min ago" },
  { key: "2", severity: "warning", rule: "Low Memory", metric: "memory", value: 18, threshold: 20, time: "5 min ago" },
  { key: "3", severity: "warning", rule: "High Drawdown", metric: "drawdown", value: 0.052, threshold: 0.05, time: "15 min ago" },
  { key: "4", severity: "info", rule: "Strategy Update", metric: "strategy", value: 14, threshold: 0, time: "1 hour ago" },
];

const RECENT_EVENTS = [
  { time: "13:45:22", event: "Trade Executed: BUY AAPL @ $185.20", type: "trade" },
  { time: "13:42:10", event: "Alert Resolved: High CPU Usage", type: "resolve" },
  { time: "13:38:05", event: "Position Closed: SELL GOOG @ $175.50", type: "trade" },
  { time: "13:30:00", event: "Risk Check: VaR within limits", type: "info" },
  { time: "13:15:45", event: "Strategy Optimized: Alpha组合 v2.1", type: "info" },
  { time: "13:00:00", event: "Market Regime: TRENDING", type: "regime" },
];

const SEVERITY_COLORS: Record<string, string> = {
  critical: "red",
  warning: "gold",
  info: "blue",
};

// ─── Metric Card ─────────────────────────────────────────────────

function MetricCard({ title, value, suffix, color, icon }: {
  title: string; value: string | number; suffix?: string; color?: string; icon?: React.ReactNode;
}) {
  return (
    <Card size="small" bordered={false} hoverable>
      <Statistic
        title={<Space>{icon}{title}</Space>}
        value={value}
        suffix={suffix}
        valueStyle={{ color: color || "#1677ff", fontSize: 24 }}
      />
    </Card>
  );
}

// ─── Health Status ───────────────────────────────────────────────

function HealthIndicator({ label, healthy }: { label: string; healthy: boolean }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
      {healthy
        ? <CheckCircleOutlined style={{ color: "#52c41a", fontSize: 16 }} />
        : <CloseCircleOutlined style={{ color: "#ff4d4f", fontSize: 16 }} />
      }
      <Text>{label}</Text>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────

export default function Monitoring() {
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(() => {
        // In real app, fetch data from API
      }, 5000);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [autoRefresh]);

  const alertColumns = [
    {
      title: "", dataIndex: "severity", key: "severity", width: 40,
      render: (v: string) => <Badge color={SEVERITY_COLORS[v]} />,
    },
    {
      title: "规则", dataIndex: "rule", key: "rule",
      render: (v: string, r: any) => (
        <Space>
          <Tag color={SEVERITY_COLORS[r.severity]}>{r.severity.toUpperCase()}</Tag>
          <Text strong>{v}</Text>
        </Space>
      ),
    },
    { title: "指标", dataIndex: "metric", key: "metric" },
    {
      title: "当前值", dataIndex: "value", key: "value",
      render: (v: number, r: any) => (
        <Text type={v > r.threshold ? "danger" : undefined}>{v}</Text>
      ),
    },
    { title: "阈值", dataIndex: "threshold", key: "threshold" },
    { title: "时间", dataIndex: "time", key: "time" },
  ];

  return (
    <Spin spinning={loading}>
      <div className="page-header">
        <h2>
          <DashboardOutlined style={{ marginRight: 8 }} />
          系统监控面板
          <Tag style={{ marginLeft: 12 }}>
            <SyncOutlined spin={autoRefresh} /> 实时
          </Tag>
        </h2>
      </div>

      {/* ─── System Health ─── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={24}>
          <Card title={<Space><SafetyOutlined />系统健康</Space>} size="small" bordered={false}>
            <Row gutter={16}>
              <Col span={6}><HealthIndicator label="API 服务" healthy /></Col>
              <Col span={6}><HealthIndicator label="数据库连接" healthy /></Col>
              <Col span={6}><HealthIndicator label="Celery Worker" healthy /></Col>
              <Col span={6}><HealthIndicator label="Redis 缓存" healthy /></Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* ─── Metrics ─── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <MetricCard title="CPU 使用率" value={METRICS.system.cpu} suffix="%" color={METRICS.system.cpu > 80 ? "#ff4d4f" : "#52c41a"} icon={<ThunderboltOutlined />} />
        </Col>
        <Col xs={24} sm={8}>
          <MetricCard title="内存使用率" value={METRICS.system.memory} suffix="%" color={METRICS.system.memory > 80 ? "#ff4d4f" : "#1677ff"} icon={<ApiOutlined />} />
        </Col>
        <Col xs={24} sm={8}>
          <MetricCard title="API 延迟" value={METRICS.system.api_latency_ms} suffix="ms" color={METRICS.system.api_latency_ms > 500 ? "#ff4d4f" : "#52c41a"} icon={<SyncOutlined />} />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <MetricCard title="今日交易" value={METRICS.trading.total_trades_today} icon={<RiseOutlined />} />
        </Col>
        <Col xs={24} sm={8}>
          <MetricCard title="胜率" value={(METRICS.trading.win_rate * 100).toFixed(1)} suffix="%" color="#52c41a" icon={<LineChartOutlined />} />
        </Col>
        <Col xs={24} sm={8}>
          <MetricCard title="日内 PnL" value={METRICS.trading.daily_pnl > 0 ? `+${METRICS.trading.daily_pnl.toLocaleString()}` : METRICS.trading.daily_pnl.toLocaleString()} color={METRICS.trading.daily_pnl >= 0 ? "#52c41a" : "#ff4d4f"} icon={METRICS.trading.daily_pnl >= 0 ? <RiseOutlined /> : <FallOutlined />} />
        </Col>
      </Row>

      {/* ─── Risk & Performance ─── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={6}>
          <Card size="small" title="VaR (95%)" bordered={false}>
            <Progress
              type="dashboard"
              percent={METRICS.risk.var_95 * 100}
              strokeColor={METRICS.risk.var_95 > 0.02 ? "#ff4d4f" : "#52c41a"}
              format={(p) => `${p?.toFixed(2)}%`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" title="CVaR (95%)" bordered={false}>
            <Progress
              type="dashboard"
              percent={METRICS.risk.cvar_95 * 100}
              strokeColor={METRICS.risk.cvar_95 > 0.03 ? "#faad14" : "#1677ff"}
              format={(p) => `${p?.toFixed(2)}%`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" title="波动率" bordered={false}>
            <Progress
              type="dashboard"
              percent={METRICS.risk.volatility * 100}
              strokeColor={METRICS.risk.volatility > 0.025 ? "#faad14" : "#1677ff"}
              format={(p) => `${p?.toFixed(2)}%`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" title="夏普比率" bordered={false}>
            <Progress
              type="dashboard"
              percent={Math.min(METRICS.trading.sharpe_ratio * 50, 100)}
              strokeColor={METRICS.trading.sharpe_ratio >= 1.5 ? "#52c41a" : "#faad14"}
              format={() => METRICS.trading.sharpe_ratio.toFixed(2)}
            />
          </Card>
        </Col>
      </Row>

      {/* ─── Alerts & Events ─── */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card
            title={<Space><BellOutlined />活跃告警 <Tag color="red">{ACTIVE_ALERTS.length}</Tag></Space>}
            size="small"
            bordered={false}
          >
            <Table
              dataSource={ACTIVE_ALERTS}
              columns={alertColumns}
              rowKey="key"
              pagination={false}
              size="small"
              showHeader={false}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card
            title={<Space><SyncOutlined />最近事件</Space>}
            size="small"
            bordered={false}
          >
            <Timeline
              items={RECENT_EVENTS.map((evt) => ({
                color: evt.type === "trade" ? "green" : evt.type === "resolve" ? "blue" : "gray",
                children: (
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <Text>{evt.event}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{evt.time}</Text>
                  </div>
                ),
              }))}
            />
          </Card>
        </Col>
      </Row>

      {/* ─── Quick Actions ─── */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="快速操作" size="small" bordered={false}>
            <Space wrap>
              <Tag color="blue" style={{ cursor: "pointer", padding: "4px 12px" }}>
                <SyncOutlined /> 刷新数据
              </Tag>
              <Tag color="green" style={{ cursor: "pointer", padding: "4px 12px" }}>
                <BellOutlined /> 测试告警
              </Tag>
              <Tag color="orange" style={{ cursor: "pointer", padding: "4px 12px" }}>
                <LineChartOutlined /> 生成报告
              </Tag>
              <Tag color="purple" style={{ cursor: "pointer", padding: "4px 12px" }}>
                <SafetyOutlined /> 运行压力测试
              </Tag>
            </Space>
          </Card>
        </Col>
      </Row>
    </Spin>
  );
}
