import { useState, useEffect, useMemo } from "react";
import {
  Card, Table, Tag, Typography, Input, Select, Space, Statistic, Row, Col, Spin, Empty,
} from "antd";
import { AppstoreOutlined, SearchOutlined } from "@ant-design/icons";
import { strategyApi } from "../services/strategyApi";

const { Title, Text } = Typography;

const TYPE_CN: Record<string, string> = {
  trend: "趋势跟踪", momentum: "动量", breakout: "突破", mean_reversion: "均值回归",
  arbitrage: "套利/Carry", reversal: "反转", filter: "过滤/辅助", layer: "分层叠加", other: "其他",
};
const TYPE_COLOR: Record<string, string> = {
  trend: "blue", momentum: "purple", breakout: "geekblue", mean_reversion: "cyan",
  arbitrage: "gold", reversal: "magenta", filter: "default", layer: "green", other: "default",
};
const REGIME_CN: Record<string, string> = {
  trending: "趋势市", ranging: "震荡市", volatile: "高波动", crash: "崩盘",
  recovery: "复苏", all: "全适应",
};

export default function StrategyLibrary() {
  const [grouped, setGrouped] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const d = await strategyApi.catalogGrouped();
        if (d?.types) setGrouped(d);
      } catch { /* 后端未启动 */ } finally { setLoading(false); }
    })();
  }, []);

  const total = grouped?.total || 0;
  const types: string[] = grouped ? Object.keys(grouped.types) : [];

  const visibleTypes = useMemo(() => {
    if (!grouped) return [];
    return types.filter((t) => typeFilter === "all" || t === typeFilter);
  }, [grouped, typeFilter, types]);

  const columns = [
    { title: "策略", dataIndex: "chinese_name", key: "cn",
      render: (t: string, r: any) => (
        <Space direction="vertical" size={0}>
          <Text strong>{t}</Text>
          <Text type="secondary" style={{ fontSize: 11 }}>{r.name}</Text>
        </Space>
      ) },
    { title: "夏普", dataIndex: "sharpe", key: "sharpe", width: 90,
      sorter: (a: any, b: any) => a.sharpe - b.sharpe,
      render: (v: number) => <Text style={{ color: v > 0 ? "#52c41a" : v < 0 ? "#ff4d4f" : "#888" }}>{v.toFixed(2)}</Text> },
    { title: "胜率", dataIndex: "win_rate", key: "wr", width: 80,
      render: (v: number) => `${(v * 100).toFixed(0)}%` },
    { title: "交易数", dataIndex: "total_trades", key: "tr", width: 80 },
    { title: "适合市态", dataIndex: "regime_fit", key: "rf",
      render: (rs: string[]) => rs.map((r) => <Tag key={r}>{REGIME_CN[r] || r}</Tag>) },
    { title: "周期", dataIndex: "timeframes", key: "tf",
      render: (tfs: string[]) => (tfs || []).join(", ") },
    { title: "状态", dataIndex: "is_active", key: "act", width: 70,
      render: (a: boolean) => a ? <Tag color="green">活跃</Tag> : <Tag>停用</Tag> },
  ];

  const filterRows = (rows: any[]) =>
    search ? rows.filter((r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      (r.chinese_name || "").includes(search)) : rows;

  return (
    <div>
      <Title level={3}><AppstoreOutlined /> 策略军火库</Title>
      <Text type="secondary">全部已注册策略，按类型分组。表现数据由锦标赛/监控回填。</Text>

      <Row gutter={16} style={{ margin: "16px 0" }}>
        <Col xs={12} sm={6}><Card size="small"><Statistic title="策略总数" value={total} /></Card></Col>
        <Col xs={12} sm={6}><Card size="small"><Statistic title="策略分类" value={types.length} /></Card></Col>
      </Row>

      <Card style={{ marginBottom: 16 }}>
        <Space wrap>
          <span>分类:</span>
          <Select
            value={typeFilter} style={{ width: 160 }} onChange={setTypeFilter}
            options={[{ value: "all", label: "全部" },
              ...types.map((t) => ({ value: t, label: TYPE_CN[t] || t }))]}
          />
          <Input
            placeholder="搜索策略名..." prefix={<SearchOutlined />} allowClear
            value={search} onChange={(e) => setSearch(e.target.value)} style={{ width: 240 }}
          />
        </Space>
      </Card>

      {loading ? <Spin /> : !grouped ? <Empty description="后端未连接" /> :
        visibleTypes.map((t) => {
          const info = grouped.types[t];
          const rows = filterRows(info.strategies.map((s: any, i: number) => ({ ...s, key: i })));
          if (!rows.length) return null;
          return (
            <Card
              key={t}
              title={<Space><Tag color={TYPE_COLOR[t]}>{TYPE_CN[t] || t}</Tag>
                <Text>{info.count} 个</Text>
                <Text type="secondary" style={{ fontSize: 12 }}>活跃 {info.active} · 停用 {info.inactive}</Text></Space>}
              style={{ marginBottom: 16 }}
            >
              <Table dataSource={rows} columns={columns} size="small" pagination={false} />
            </Card>
          );
        })}
    </div>
  );
}
