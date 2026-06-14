import { useEffect, useState } from "react";
import {
  Card, Table, Tag, Typography, Statistic, Spin, Row, Col, Button, Progress, Empty, Tooltip,
} from "antd";
import {
  TrophyOutlined, FireOutlined, RiseOutlined, FallOutlined,
  CrownOutlined, GoldOutlined,
} from "@ant-design/icons";
import { getTournamentStandings } from "../api/client";
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

  useEffect(() => {
    setStatus("loading");
    getTournamentStandings()
      .then((res) => setStandings(res.data))
      .catch(() => setStandings(MOCK_STANDINGS))
      .finally(() => setStatus("success"));
  }, []);

  const topScore = standings[0]?.score ?? 0;
  const avgSharpe = standings.length > 0
    ? standings.reduce((s, e) => s + e.sharpe, 0) / standings.length
    : 0;

  return (
    <Spin spinning={status === "loading"}>
      <div className="page-header">
        <h2>
          <TrophyOutlined style={{ color: "#ffd666", marginRight: 8 }} />
          策略锦标赛
        </h2>
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
    </Spin>
  );
}
