import { useState, useEffect } from "react";
import { Card, Table, Typography, Tag, Button, Space, Empty, message } from "antd";
import { SyncOutlined } from "@ant-design/icons";
import { feedbackApi } from "../services/phase4Api";

const { Title, Text } = Typography;

export default function Feedback() {
  const [history, setHistory] = useState<any[]>([]);
  const [rankings, setRankings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [h, r] = await Promise.all([feedbackApi.history(), feedbackApi.rankings()]);
      setHistory(h?.history || []);
      setRankings(r?.rankings || []);
    } catch (e: any) {
      message.error("加载失败: " + (e?.message || ""));
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  return (
    <div>
      <Title level={3}>🔄 反馈闭环</Title>
      <Text type="secondary">锦标赛结果回流到策略目录:表现回填、明星/下线判定、(可选)ML 重训。</Text>
      <Space style={{ display: "block", margin: "12px 0" }}>
        <Button icon={<SyncOutlined />} onClick={load} loading={loading}>刷新</Button>
      </Space>

      <Card title="策略表现排名 (锦标赛回填后)" style={{ marginBottom: 16 }}>
        {rankings.length ? (
          <Table
            dataSource={rankings.map((r, i) => ({ ...r, key: i, rank: i + 1 }))}
            size="small" pagination={{ pageSize: 10 }}
            columns={[
              { title: "#", dataIndex: "rank", width: 50 },
              { title: "策略", dataIndex: "chinese_name",
                render: (t, r: any) => <Space direction="vertical" size={0}>
                  <Text strong>{t}</Text><Text type="secondary" style={{ fontSize: 11 }}>{r.name}</Text></Space> },
              { title: "夏普", dataIndex: "sharpe",
                render: (v: number) => <Text style={{ color: v > 0 ? "#52c41a" : v < 0 ? "#ff4d4f" : "#888" }}>{v.toFixed(2)}</Text> },
              { title: "胜率", dataIndex: "win_rate", render: (v: number) => `${(v * 100).toFixed(0)}%` },
              { title: "交易数", dataIndex: "total_trades" },
              { title: "状态", dataIndex: "is_active",
                render: (a: boolean) => a ? <Tag color="green">活跃</Tag> : <Tag color="red">下线</Tag> },
            ]}
          />
        ) : <Empty description="暂无表现数据 (需先跑锦标赛并回流)" />}
      </Card>

      <Card title="反馈历史">
        {history.length ? (
          <Table
            dataSource={history.map((h, i) => ({ ...h, key: i }))}
            size="small" pagination={{ pageSize: 10 }}
            columns={[
              { title: "时间", dataIndex: "timestamp", render: (t: string) => t?.slice(0, 19) },
              { title: "赛事", dataIndex: "tournament_id" },
              { title: "策略数", dataIndex: "n_strategies" },
              { title: "最佳", dataIndex: "top_strategy",
                render: (t, r: any) => <Text>{t} ({r.top_sharpe?.toFixed(2)})</Text> },
              { title: "明星", dataIndex: "strategies_starred",
                render: (s: string[]) => s?.length || 0 },
              { title: "下线", dataIndex: "strategies_retired",
                render: (s: string[]) => <Text type={s?.length ? "danger" : "secondary"}>{s?.length || 0}</Text> },
            ]}
          />
        ) : <Empty description="暂无反馈记录" />}
      </Card>
    </div>
  );
}
