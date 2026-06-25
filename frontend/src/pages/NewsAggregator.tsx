import { useEffect, useState } from "react";
import { Card, Table, Tag, Space, Button, Typography, Input, Spin, message, Row, Col, Statistic, List, Badge, Select, DatePicker, Tabs, Alert, Tooltip, Progress, Empty } from "antd";
import { FundOutlined, SyncOutlined, PlusOutlined, RiseOutlined, FallOutlined, GlobalOutlined, GithubOutlined, RedditOutlined, BellOutlined, FilterOutlined } from "@ant-design/icons";
import { newsApi, NewsItem } from "../services/newsApi";
import { marketApi, PlatformPost } from "../services/marketApi";

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;

const SENTIMENT_STYLE = (label: string) => ({
  color: label === "positive" ? "#3f8600" : label === "negative" ? "#cf1322" : "#999",
});

const SENTIMENT_COLOR = (score: number) => {
  if (score >= 7) return "green";
  if (score >= 5) return "blue";
  if (score >= 3) return "orange";
  return "red";
};

const DEFAULT_SOURCES = [
  { name: "36氪", url: "https://36kr.com/feed", icon: "📰" },
  { name: "虎嗅", url: "https://www.huxiu.com/rss/0.xml", icon: "🐯" },
  { name: "少数派", url: "https://sspai.com/feed", icon: "✍️" },
  { name: "IT之家", url: "https://www.ithome.com/rss/", icon: "💻" },
  { name: "财联社", url: "https://www.cls.cn/rss", icon: "💰" },
  { name: "极客公园", url: "https://www.geekpark.net/rss", icon: "🚀" },
];

const PLATFORM_OPTIONS = [
  { value: "xueqiu", label: "雪球", icon: "📈" },
  { value: "github", label: "GitHub", icon: "🐙" },
  { value: "twitter", label: "Twitter", icon: "🐦" },
  { value: "reddit", label: "Reddit", icon: "🔴" },
  { value: "hackernews", label: "HN", icon: "⚡" },
];

export default function NewsAggregator() {
  const [loading, setLoading] = useState(true);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [stats, setStats] = useState<{ total: number; avg_sentiment: number; by_source: Record<string, number> } | null>(null);
  const [posts, setPosts] = useState<PlatformPost[]>([]);
  const [marketSentiment, setMarketSentiment] = useState<{ total: number; positive: number; neutral: number; negative: number } | null>(null);
  const [rssUrl, setRssUrl] = useState("");
  const [rssName, setRssName] = useState("");
  const [rssSources, setRssSources] = useState<{ name: string; url: string }[]>([]);
  const [fetching, setFetching] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchPlatforms, setSearchPlatforms] = useState<string[]>(["github"]);
  const [sentimentFilter, setSentimentFilter] = useState<string | undefined>(undefined);
  const [sourceFilter, setSourceFilter] = useState<string | undefined>(undefined);
  const [activeTab, setActiveTab] = useState("news");
  const [llmEnabled, setLlmEnabled] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const nRes = await newsApi.list({ limit: 50 });
      const sRes = await newsApi.stats();
      const pRes = await marketApi.posts({ limit: 20 });
      const msRes = await marketApi.sentiment();
      const srcRes = await newsApi.sources();
      setNews(nRes.data);
      setStats(sRes.data);
      setPosts(pRes.data.posts || []);
      setMarketSentiment(msRes.data);
      setRssSources(srcRes.data.sources);
      // Check if LLM is available
      setLlmEnabled(nRes.data.some((n: NewsItem) => n.sentiment_score > 10));
    } catch (e) {
      console.error("Failed to load news data:", e);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleFetchRss = async () => {
    if (!rssUrl) { message.warning("请输入RSS地址"); return; }
    setFetching(true);
    try {
      await newsApi.subscribe(rssUrl, rssName);
      const res = await newsApi.fetchRss(rssName || undefined);
      message.success(`抓取到 ${res.data.fetched} 条`);
      load();
    } catch { message.error("抓取失败"); }
    finally { setFetching(false); }
  };

  const handleSearch = async () => {
    if (!searchQuery) return;
    setLoading(true);
    try {
      const res = await marketApi.search(searchQuery, searchPlatforms);
      setPosts(res.data.results);
    } finally { setLoading(false); }
  };

  const handleQuickSource = async (source: typeof DEFAULT_SOURCES[0]) => {
    setFetching(true);
    try {
      await newsApi.subscribe(source.url, source.name);
      const res = await newsApi.fetchRss(source.name);
      message.success(`${source.name}: 抓取到 ${res.data.fetched} 条`);
      load();
    } catch { message.error(`${source.name} 抓取失败`); }
    finally { setFetching(false); }
  };

  // Filter news by sentiment and source
  const filteredNews = news.filter(item => {
    if (sentimentFilter && item.sentiment_label !== sentimentFilter) return false;
    if (sourceFilter && item.source !== sourceFilter) return false;
    return true;
  });

  // Get unique sources for filter
  const uniqueSources = [...new Set(news.map(n => n.source))];

  const newsTab = (
    <Card
      size="small"
      title={<><FundOutlined /> 新闻流</>}
      extra={
        <Space size="small">
          <Select allowClear placeholder="情感" style={{ width: 80 }} onChange={v => setSentimentFilter(v || undefined)} size="small">
            <Select.Option value="positive">正向</Select.Option>
            <Select.Option value="neutral">中性</Select.Option>
            <Select.Option value="negative">负向</Select.Option>
          </Select>
          <Select allowClear placeholder="来源" style={{ width: 100 }} onChange={v => setSourceFilter(v || undefined)} size="small">
            {uniqueSources.map(s => <Select.Option key={s} value={s}>{s}</Select.Option>)}
          </Select>
        </Space>
      }
    >
      {loading ? <Spin /> : filteredNews.length === 0 ? (
        <Empty description="暂无新闻，请添加RSS源抓取" />
      ) : (
        <List
          size="small"
          dataSource={filteredNews}
          renderItem={(item) => (
            <List.Item key={item.id} style={{ padding: "10px 0" }}>
              <Space direction="vertical" size={4} style={{ width: "100%" }}>
                <Space>
                  <Tag color="blue">{item.source}</Tag>
                  <Text strong style={{ fontSize: 13 }}>{item.title}</Text>
                  <Tooltip title={`情感评分: ${item.sentiment_score}/10`}>
                    <Tag color={SENTIMENT_COLOR(item.sentiment_score)}>
                      {llmEnabled ? `🤖 ${item.sentiment_score}` : item.sentiment_score}
                    </Tag>
                  </Tooltip>
                  <Tag color={item.sentiment_label === "positive" ? "green" : item.sentiment_label === "negative" ? "red" : "default"}>
                    {item.sentiment_label === "positive" ? "正向" : item.sentiment_label === "negative" ? "负向" : "中性"}
                  </Tag>
                </Space>
                <Tooltip title={item.summary}>
                  <Text type="secondary" style={{ fontSize: 11, display: "block" }} ellipsis={{ tooltip: false }}>{item.summary}</Text>
                </Tooltip>
                <Text type="secondary" style={{ fontSize: 10 }}>
                  {item.published_at ? new Date(item.published_at).toLocaleString("zh-CN") : ""}
                </Text>
              </Space>
            </List.Item>
          )}
        />
      )}
    </Card>
  );

  const platformsTab = (
    <Card size="small" title={<><GlobalOutlined /> 跨平台舆情</>}>
      <Space direction="vertical" style={{ width: "100%" }}>
        <Space wrap>
          <Input.Search
            placeholder="搜索关键词"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onSearch={handleSearch}
            enterButton
            style={{ width: 300 }}
          />
          <Select
            mode="multiple"
            placeholder="选择平台"
            value={searchPlatforms}
            onChange={setSearchPlatforms}
            style={{ minWidth: 200 }}
          >
            {PLATFORM_OPTIONS.map(p => (
              <Select.Option key={p.value} value={p.value}>
                <Space>{p.icon} {p.label}</Space>
              </Select.Option>
            ))}
          </Select>
        </Space>
        <Text type="secondary" style={{ fontSize: 11 }}>
          支持平台: {PLATFORM_OPTIONS.map(p => p.label).join(", ")}
        </Text>
      </Space>
      <Table
        size="small"
        dataSource={posts}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        columns={[
          { title: "平台", dataIndex: "platform", width: 80, render: (v) => {
            const opt = PLATFORM_OPTIONS.find(p => p.value === v);
            return <Tag>{opt?.icon} {v}</Tag>;
          }},
          { title: "作者", dataIndex: "author", width: 100 },
          { title: "内容", dataIndex: "content", ellipsis: true },
          { title: "情感", dataIndex: "sentiment", width: 80, render: (v) => <Text style={SENTIMENT_STYLE(v)}>{v}</Text> },
          { title: "点赞", dataIndex: "likes", width: 60 },
          { title: "时间", dataIndex: "posted_at", width: 150, render: (v) => <Text type="secondary" style={{ fontSize: 11 }}>{new Date(v).toLocaleString("zh-CN")}</Text> },
        ]}
        style={{ marginTop: 12 }}
      />
    </Card>
  );

  const sourcesTab = (
    <Card size="small" title={<><BellOutlined /> RSS 订阅管理</>}>
      <Space direction="vertical" style={{ width: "100%" }}>
        <Row gutter={12}>
          <Col span={16}>
            <Input placeholder="RSS地址" value={rssUrl} onChange={e => setRssUrl(e.target.value)} />
          </Col>
          <Col span={4}>
            <Input placeholder="名称(可选)" value={rssName} onChange={e => setRssName(e.target.value)} />
          </Col>
          <Col span={4}>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleFetchRss} loading={fetching} block>
              订阅
            </Button>
          </Col>
        </Row>
      </Space>

      <div style={{ marginTop: 16 }}>
        <Text strong style={{ fontSize: 12 }}>快捷订阅:</Text>
        <Space wrap style={{ marginTop: 8 }}>
          {DEFAULT_SOURCES.map(src => (
            <Tooltip key={src.name} title={`订阅 ${src.url}`}>
              <Button
                size="small"
                onClick={() => handleQuickSource(src)}
                loading={fetching}
              >
                {src.icon} {src.name}
              </Button>
            </Tooltip>
          ))}
        </Space>
      </div>

      <List size="small" style={{ marginTop: 12 }} dataSource={rssSources}
        locale={{ emptyText: "暂无订阅源" }}
        renderItem={(src) => (
          <List.Item key={src.name} style={{ padding: "6px 0" }}>
            <Space>
              <Badge status="success" />
              <Text style={{ fontSize: 12 }}>{src.name || src.url}</Text>
              <Text type="secondary" style={{ fontSize: 10, maxWidth: 200 }} ellipsis={{ tooltip: src.url }}>{src.url}</Text>
            </Space>
          </List.Item>
        )}
      />
    </Card>
  );

  return (
    <div>
      <Space direction="vertical" size="large" style={{ width: "100%" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Title level={4} style={{ margin: 0 }}><FundOutlined /> 新闻聚合中心</Title>
          <Space>
            {llmEnabled && (
              <Tag color="purple" icon={<GlobalOutlined />}>🤖 LLM情感分析已启用</Tag>
            )}
            <Button icon={<SyncOutlined />} onClick={load} loading={loading}>刷新</Button>
          </Space>
        </div>

        {/* Stats */}
        {stats && (
          <Row gutter={12}>
            <Col span={4}><Card size="small"><Statistic title="新闻总数" value={stats.total} /></Card></Col>
            <Col span={4}>
              <Card size="small">
                <Statistic
                  title="情感均值"
                  value={stats.avg_sentiment}
                  suffix="/ 10"
                  precision={1}
                  valueStyle={SENTIMENT_STYLE(stats.avg_sentiment > 6 ? "positive" : stats.avg_sentiment < 4 ? "negative" : "neutral")}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card size="small">
                <Statistic title="舆情正向" value={marketSentiment?.positive ?? 0} prefix={<RiseOutlined />}
                  valueStyle={{ color: "#3f8600" }} />
              </Card>
            </Col>
            <Col span={4}>
              <Card size="small">
                <Statistic title="舆情中性" value={marketSentiment?.neutral ?? 0} />
              </Card>
            </Col>
            <Col span={4}>
              <Card size="small">
                <Statistic title="舆情负向" value={marketSentiment?.negative ?? 0} prefix={<FallOutlined />}
                  valueStyle={{ color: "#cf1322" }} />
              </Card>
            </Col>
            <Col span={4}>
              <Card size="small">
                <Statistic title="订阅源" value={rssSources.length} suffix="个" />
              </Card>
            </Col>
          </Row>
        )}

        {/* Sentiment Bar */}
        {marketSentiment && marketSentiment.total > 0 && (
          <Card size="small">
            <Text type="secondary" style={{ fontSize: 12, marginRight: 8 }}>舆情分布:</Text>
            <Progress
              percent={Math.round((marketSentiment.positive / marketSentiment.total) * 100)}
              size="small"
              style={{ width: 200, display: "inline-block" }}
              strokeColor="#52c41a"
            />
            <Text type="secondary" style={{ fontSize: 11 }}> 正向 {marketSentiment.positive} | 中性 {marketSentiment.neutral} | 负向 {marketSentiment.negative}</Text>
          </Card>
        )}

        {/* Tabs */}
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            { key: "news", label: "📰 新闻流", children: newsTab },
            { key: "platforms", label: "🌐 跨平台", children: platformsTab },
            { key: "sources", label: "🔔 订阅管理", children: sourcesTab },
          ]}
        />
      </Space>
    </div>
  );
}
