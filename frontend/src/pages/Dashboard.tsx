import { useEffect, useState, useRef } from "react";
import { Row, Col, Card, Statistic, Table, Typography, Tag, Spin, Empty, Space } from "antd";
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  FundOutlined,
  RiseOutlined,
  FallOutlined,
  SwapOutlined,
  TrophyOutlined,
} from "@ant-design/icons";
import { createChart, ColorType, IChartApi, type Time } from "lightweight-charts";
import { listStrategies, getMarketData, getTournamentStandings, getMarketIndices, IndexQuote } from "../api/client";
import type { Strategy, TournamentEntry } from "../api/client";

const { Title, Text } = Typography;

/* ── Mock data for development (backend may not be running) ── */
const MOCK_EQUITY = Array.from({ length: 200 }, (_, i) => ({
  time: (new Date(2024, 0, i + 1).getTime() / 1000) as number,
  value: 1000000 * (1 + (Math.random() - 0.5) * 0.6 + i * 0.0015),
}));

const MOCK_VOLUME = Array.from({ length: 200 }, (_, i) => ({
  time: (new Date(2024, 0, i + 1).getTime() / 1000) as number,
  value: Math.floor(Math.random() * 50000 + 10000),
}));

const MOCK_CANDLES = Array.from({ length: 200 }, (_, i) => {
  const base = 5000 + Math.sin(i / 10) * 200 + Math.random() * 50;
  return {
    time: (new Date(2024, 0, i + 1).getTime() / 1000) as number,
    open: base + (Math.random() - 0.5) * 30,
    high: base + Math.random() * 40 + 20,
    low: base - Math.random() * 40 - 20,
    close: base + (Math.random() - 0.5) * 30,
  };
});

/* ── Equity Curve Chart ── */
function EquityChart({ data }: { data: typeof MOCK_EQUITY }) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartApiRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;
    const chart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 300,
      layout: {
        background: { type: ColorType.Solid, color: "#1a1a2e" },
        textColor: "#8c8c8c",
      },
      grid: {
        vertLines: { color: "#2a2a2a" },
        horzLines: { color: "#2a2a2a" },
      },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: "#303030" },
      timeScale: { borderColor: "#303030" },
    });

    const line = chart.addLineSeries({
      color: "#00d4aa",
      lineWidth: 2,
      crosshairMarkerVisible: true,
      crosshairMarkerRadius: 4,
      priceFormat: { type: "custom", formatter: (v: number) => `¥${v.toLocaleString()}` },
    });
    line.setData(data as { time: Time; value: number }[]);
    chart.timeScale().fitContent();

    chartApiRef.current = chart;
    const handleResize = () => {
      if (chartRef.current) {
        chart.applyOptions({ width: chartRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [data]);

  return <div ref={chartRef} style={{ width: "100%", height: 300 }} />;
}

/* ── Top Strategies Table ── */
const columns = [
  { title: "排名", dataIndex: "rank", key: "rank", width: 60 },
  {
    title: "策略名称",
    dataIndex: "strategy_name",
    key: "strategy_name",
    render: (v: string) => <Text strong>{v}</Text>,
  },
  {
    title: "夏普比率",
    dataIndex: "sharpe",
    key: "sharpe",
    sorter: (a: any, b: any) => a.sharpe - b.sharpe,
    render: (v: number) => (
      <span style={{ color: v >= 1 ? "#00d4aa" : v >= 0 ? "#ffd666" : "#ff4d6a" }}>
        {v.toFixed(2)}
      </span>
    ),
  },
  {
    title: "累计收益",
    dataIndex: "total_return",
    key: "total_return",
    sorter: (a: any, b: any) => a.total_return - b.total_return,
    render: (v: number) => (
      <span className={v >= 0 ? "text-green" : "text-red"}>
        {(v * 100).toFixed(1)}%
      </span>
    ),
  },
  {
    title: "交易次数",
    dataIndex: "trades",
    key: "trades",
  },
  {
    title: "评分",
    dataIndex: "score",
    key: "score",
    sorter: (a: any, b: any) => a.score - b.score,
    render: (v: number) => (
      <Tag color={v >= 80 ? "green" : v >= 60 ? "gold" : "red"}>{v.toFixed(0)}</Tag>
    ),
  },
];

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [standings, setStandings] = useState<TournamentEntry[]>([]);
  const [indices, setIndices] = useState<IndexQuote[]>([]);

  useEffect(() => {
    Promise.allSettled([
      listStrategies(),
      getTournamentStandings(),
      getMarketIndices(),
    ]).then(([s, t, ix]) => {
      if (s.status === "fulfilled") setStrategies(s.value.data.strategies);
      if (t.status === "fulfilled") setStandings(t.value.data);
      if (ix.status === "fulfilled") setIndices(ix.value.data.indices);
      setLoading(false);
    });
  }, []);

  const totalPnl = strategies.reduce((sum, s) => sum + (s.performance?.total_return ?? 0), 0);
  const activeCount = strategies.filter((s) => s.status === "active").length;
  const avgSharpe =
    strategies.length > 0
      ? strategies.reduce((sum, s) => sum + (s.performance?.sharpe ?? 0), 0) / strategies.length
      : 0;

  return (
    <Spin spinning={loading} size="large">
      {/* ── Stats Row ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="总资产 (模拟)"
              value={12500000}
              precision={0}
              prefix="¥"
              valueStyle={{ color: "#00d4aa" }}
              suffix={
                <span style={{ fontSize: 14, color: "#00d4aa" }}>
                  <ArrowUpOutlined /> +2.8%
                </span>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="活跃策略"
              value={activeCount}
              prefix={<FundOutlined />}
              suffix={<span style={{ fontSize: 14, color: "#8c8c8c" }}>/ {strategies.length}</span>}
              valueStyle={{ color: "#4096ff" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="平均夏普"
              value={avgSharpe}
              precision={2}
              prefix={<RiseOutlined />}
              valueStyle={{ color: avgSharpe >= 1 ? "#00d4aa" : "#ffd666" }}
              suffix={
                <Tag color={avgSharpe >= 1 ? "green" : "gold"} style={{ marginLeft: 8 }}>
                  {avgSharpe >= 1 ? "优秀" : "一般"}
                </Tag>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="总交易量"
              value={8472}
              prefix={<SwapOutlined />}
              valueStyle={{ color: "#b37feb" }}
              suffix={<span style={{ fontSize: 14, color: "#8c8c8c" }}>笔</span>}
            />
          </Card>
        </Col>
      </Row>

      {/* ── Global Indices ── */}
      {indices.length > 0 && (
        <Row gutter={[8, 8]} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <Card size="small" title={<><FundOutlined /> 全球主要指数</>} extra={indices.some((ix: any) => ix.fallback) && <Tag color="warning" style={{ fontSize: 10 }}>参考值</Tag>} bordered={false}>
              <Row gutter={[8, 8]}>
                {indices.map((ix) => {
                  const isUp = ix.change_pct !== null && ix.change_pct >= 0;
                  const color = ix.change_pct === null ? "#999" : isUp ? "#ff4d6a" : "#00d4aa";
                  return (
                    <Col xs={12} sm={8} md={6} lg={4} key={ix.symbol}>
                      <Card size="small" hoverable style={{ background: "#141414", borderLeft: `3px solid ${color}`, borderRadius: 6 }}>
                        <Space direction="vertical" size={2} style={{ width: "100%" }}>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <Text style={{ fontSize: 12, fontWeight: 600, color: "#e0e0e0" }}>{ix.name}</Text>
                            <Tag style={{ fontSize: 9, lineHeight: "16px", height: 18 }}>{ix.region}</Tag>
                          </div>
                          <Text style={{ fontSize: 15, fontWeight: 700, fontFamily: "monospace", color: "#fff" }}>
                            {ix.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) ?? "--"}
                          </Text>
                          <span style={{ fontSize: 12, color }}>
                            {isUp ? "▲" : "▼"} {ix.change !== null ? ix.change.toFixed(2) : "--"} ({ix.change_pct !== null ? `${ix.change_pct >= 0 ? "+" : ""}${ix.change_pct.toFixed(2)}%` : "--"})
                          </span>
                        </Space>
                      </Card>
                    </Col>
                  );
                })}
              </Row>
            </Card>
          </Col>
        </Row>
      )}

      {/* ── Charts Row ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="权益曲线" bordered={false}>
            <EquityChart data={MOCK_EQUITY} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="快速统计" bordered={false}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Statistic
                  title="日收益"
                  value={1.24}
                  precision={2}
                  prefix={<ArrowUpOutlined />}
                  suffix="%"
                  valueStyle={{ color: "#00d4aa" }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="最大回撤"
                  value={-8.42}
                  precision={2}
                  prefix={<ArrowDownOutlined />}
                  suffix="%"
                  valueStyle={{ color: "#ff4d6a" }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="胜率"
                  value={62.5}
                  precision={1}
                  prefix={<TrophyOutlined />}
                  suffix="%"
                  valueStyle={{ color: "#ffd666" }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="总交易"
                  value={8472}
                  prefix={<SwapOutlined />}
                  valueStyle={{ color: "#b37feb" }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* ── Rankings ── */}
      <Card
        title={
          <span>
            <TrophyOutlined style={{ marginRight: 8, color: "#ffd666" }} />
            策略排行榜
          </span>
        }
        bordered={false}
      >
        {standings.length > 0 ? (
          <Table
            dataSource={standings.slice(0, 10)}
            columns={columns}
            rowKey="rank"
            pagination={false}
            size="middle"
          />
        ) : (
          <Empty description="暂无锦标赛数据，启动回测后生成" />
        )}
      </Card>
    </Spin>
  );
}
