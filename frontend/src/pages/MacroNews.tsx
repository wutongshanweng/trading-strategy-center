import { useEffect, useState, useCallback } from "react";
import {
  Card, Row, Col, Tag, Typography, Spin, Empty, Statistic, Button,
  Timeline, Space, message, Tooltip, Divider, Modal, InputNumber, Form, Popover,
  Table, Input, Select, Progress,
} from "antd";
import {
  ReloadOutlined, BellOutlined, ThunderboltOutlined, FundOutlined as FundIcon,
  CalendarOutlined, LinkOutlined, RiseOutlined, StarOutlined, StarFilled,
  GlobalOutlined, AlertOutlined, PlusOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { macroNewsApi, alertApi, simTradingApi, type AlertSignal } from "../services/macroNewsApi";
import { newsApi, NewsItem } from "../services/newsApi";
import { marketApi, PlatformPost } from "../services/marketApi";

const { Title, Text, Paragraph } = Typography;

const SENTI_BG: Record<string, string> = { "🟢": "#f6ffed", "🔴": "#fff1f0", "🟡": "#fffbe6" };
const DIR_CFG: Record<string, { cn: string; color: string; bg: string }> = {
  BUY: { cn: "做多", color: "#52c41a", bg: "#f6ffed" },
  SELL: { cn: "做空", color: "#ff4d4f", bg: "#fff1f0" },
  HOLD: { cn: "持有", color: "#faad14", bg: "#fffbe6" },
  WATCH: { cn: "观望", color: "#faad14", bg: "#fffbe6" },
};

const SENTIMENT_STYLE = (label: string) => ({
  color: label === "positive" ? "#3f8600" : label === "negative" ? "#cf1322" : "#999",
});

const PLATFORM_OPTIONS = [
  { value: "xueqiu", label: "雪球", icon: "📈" },
  { value: "github", label: "GitHub", icon: "🐙" },
  { value: "twitter", label: "Twitter", icon: "🐦" },
  { value: "reddit", label: "Reddit", icon: "🔴" },
  { value: "hackernews", label: "HN", icon: "⚡" },
];

const DEFAULT_SOURCES = [
  { name: "36氪", url: "https://36kr.com/feed", icon: "📰" },
  { name: "虎嗅", url: "https://www.huxiu.com/rss/0.xml", icon: "🐯" },
  { name: "少数派", url: "https://sspai.com/feed", icon: "✍️" },
  { name: "财联社", url: "https://www.cls.cn/rss", icon: "💰" },
  { name: "极客公园", url: "https://www.geekpark.net/rss", icon: "🚀" },
];

function stars(n: number) {
  return "⭐".repeat(Math.max(0, Math.min(5, n)));
}

interface NormalizedNewsItem extends NewsItem { raw?: any; }

export default function MacroNews() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [dash, setDash] = useState<any>(null);
  const [signals, setSignals] = useState<AlertSignal[]>([]);
  const [sigLoading, setSigLoading] = useState(false);
  const [watchIds, setWatchIds] = useState<Set<string>>(new Set());
  const [openForm] = Form.useForm();
  const [openTarget, setOpenTarget] = useState<AlertSignal | null>(null);
  const [allNews, setAllNews] = useState<NewsItem[]>([]);

  // ───── 新闻聚合功能 (来自 NewsAggregator) ─────
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
  const [activeTab, setActiveTab] = useState("dashboard");
  const [llmEnabled, setLlmEnabled] = useState(false);

  const loadDash = useCallback(async () => {
    setLoading(true);
    try {
      const d = await macroNewsApi.dashboard();
      setDash(d);
    } catch { /* 后端未连接 */ } finally { setLoading(false); }
  }, []);

  const loadSignals = useCallback(async () => {
    setSigLoading(true);
    try {
      const d = await alertApi.list(20);
      setSignals(d.signals || []);
    } catch { /* 后端未连接 */ } finally { setSigLoading(false); }
  }, []);

  const loadWatch = useCallback(async () => {
    try {
      const d = await simTradingApi.watchlist();
      setWatchIds(new Set((d.watchlist || []).map((w: any) => w.id)));
    } catch { /* ignore */ }
  }, []);

  const loadAggNews = useCallback(async () => {
    try {
      const [nRes, sRes, pRes, msRes, srcRes] = await Promise.all([
        newsApi.list({ limit: 60 }),
        newsApi.stats(),
        marketApi.posts({ limit: 20 }),
        marketApi.sentiment(),
        newsApi.sources(),
      ]);
      const all: NewsItem[] = nRes.data;
      const RELEVANT = /交易|期货|期权|股票|基金|债券|外汇|黄金|原油|经济|宏观|GDP|通胀|利率|美联储|央行|银保监会|证监会|政策|公告|业绩|营收|利润|分红|AI|人工智能|科技|芯片|算力|模型|深度学习|量化|对冲|市场|板块|概念|行情/i;
      const EXCLUDED_SOURCES = /IT之家|少数派/i;
      setAllNews(all.filter(n => !EXCLUDED_SOURCES.test(n.source) && RELEVANT.test(n.title + " " + n.summary)));
      setStats(sRes.data);
      setPosts(pRes.data.posts || []);
      setMarketSentiment(msRes.data);
      setRssSources(srcRes.data.sources || []);
      setLlmEnabled(all.some((n: NewsItem) => n.sentiment_score > 10));
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    loadDash();
    loadSignals();
    loadWatch();
    loadAggNews();
    const t1 = setInterval(loadDash, 300000);   // 5min (快讯+仪表盘)
    const t2 = setInterval(loadSignals, 300000);  // 5min (交易信号)
    const t3 = setInterval(loadAggNews, 300000);   // 5min (聚合新闻)
    return () => { clearInterval(t1); clearInterval(t2); clearInterval(t3); };
  }, [loadDash, loadSignals, loadWatch, loadAggNews]);

  const refreshSignals = async () => {
    setSigLoading(true);
    try {
      await alertApi.refresh();
      await loadSignals();
      message.success("信号已刷新");
    } catch { message.error("刷新失败"); } finally { setSigLoading(false); }
  };

  const toggleWatch = async (sig: AlertSignal) => {
    try {
      if (watchIds.has(sig.id)) {
        await simTradingApi.removeWatch(sig.id);
        setWatchIds((s) => { const n = new Set(s); n.delete(sig.id); return n; });
        message.success("已取消收藏");
      } else {
        await simTradingApi.addWatch(sig);
        setWatchIds((s) => new Set(s).add(sig.id));
        message.success("已收藏");
      }
    } catch { message.error("操作失败"); }
  };

  const submitOpen = async () => {
    const v = await openForm.validateFields();
    if (!openTarget) return;
    try {
      await simTradingApi.open({
        symbol: openTarget.symbol,
        direction: openTarget.direction === "SELL" ? "short" : "long",
        price: v.price, qty: v.qty, stop_loss: v.stop_loss, take_profit: v.take_profit,
      });
      message.success("模拟开仓成功");
      setOpenTarget(null);
    } catch { message.error("开仓失败"); }
  };

  // ───── 新闻聚合功能 (来自 NewsAggregator) ─────
  const handleFetchRss = async () => {
    if (!rssUrl) { message.warning("请输入RSS地址"); return; }
    setFetching(true);
    try {
      await newsApi.subscribe(rssUrl, rssName);
      const res = await newsApi.fetchRss(rssName || undefined);
      message.success(`抓取到 ${res.data.fetched} 条`);
      loadAggNews();
    } catch { message.error("抓取失败"); }
    finally { setFetching(false); }
  };

  const handleSearch = async () => {
    if (!searchQuery) return;
    setLoading(true);
    try {
      const res = await marketApi.search(searchQuery, searchPlatforms);
      setPosts(res.data.results || []);
    } finally { setLoading(false); }
  };

  const handleQuickSource = async (source: typeof DEFAULT_SOURCES[0]) => {
    setFetching(true);
    try {
      await newsApi.subscribe(source.url, source.name);
      const res = await newsApi.fetchRss(source.name);
      message.success(`${source.name}: 抓取到 ${res.data.fetched} 条`);
      loadAggNews();
    } catch { message.error(`${source.name} 抓取失败`); }
    finally { setFetching(false); }
  };

  const filteredNews = allNews.filter(item => {
    if (sentimentFilter && item.sentiment_label !== sentimentFilter) return false;
    if (sourceFilter && item.source !== sourceFilter) return false;
    return true;
  });

  const uniqueSources = [...new Set(allNews.map(n => n.source))];

  // 统一新闻格式
  function normalizeNews(n: any): NormalizedNewsItem {
    if (n.sentiment_score !== undefined) {
      return n as NormalizedNewsItem;
    }
    // 东方财富格式转换
    const labelMap: Record<string, { score: number; label: string }> = {
      "🟢": { score: 0.8, label: "positive" },
      "🟡": { score: 0.5, label: "neutral" },
      "🔴": { score: 0.2, label: "negative" },
    };
    const mapped = labelMap[n.label] || { score: 0.5, label: "neutral" };
    return {
      id: n.id || n.url || Math.random().toString(),
      url: n.url || "",
      source: "东方财富",
      title: n.title || "",
      summary: n.content || n.title || "",
      published_at: n.timestamp || "",
      sentiment_score: mapped.score,
      sentiment_label: mapped.label,
      tags: n.products || [],
      raw: n,
    };
  }

  const normalizedNews = [...(dash?.news?.items || []), ...allNews].map(normalizeNews)
    .sort((a, b) => (new Date(b.published_at).getTime() || 0) - (new Date(a.published_at).getTime() || 0));

  const macro = dash?.macro?.indicators || [];
  const events = dash?.calendar?.events || [];
  const linkage = dash?.linkage || {};
  const outlook = dash?.outlook?.outlook || [];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Title level={3} style={{ margin: 0 }}><FundIcon /> 新闻宏观仪表盘</Title>
        <Space>
          {llmEnabled && (
            <Tag color="purple"><GlobalOutlined /> LLM情感分析已启用</Tag>
          )}
          <Text type="secondary">{dash?.news?.updated_at ? `快讯更新 ${fmtTime(dash.news.updated_at)}` : ""}</Text>
          <Button icon={<ReloadOutlined />} onClick={async () => { setLoading(true); try { await macroNewsApi.refreshNews(); } catch {} loadDash(); loadAggNews(); } } loading={loading}>刷新全部</Button>
        </Space>
      </div>
      <Text type="secondary">市场快讯 + 宏观趋势 + 品种联动 + 远期展望。页面每 5 分钟自动刷新, 信号每 5 分钟刷新。</Text>
      <Divider style={{ margin: "12px 0" }} />

      {/* ───── 页面Tab导航 (快选) ───── */}
      <Space style={{ marginBottom: 16 }}>
        <Button type={activeTab === "dashboard" ? "primary" : "default"} onClick={() => setActiveTab("dashboard")}>
          <BellOutlined /> 仪表盘
        </Button>
        <Button type={activeTab === "news" ? "primary" : "default"} onClick={() => setActiveTab("news")}>
          <FundIcon /> 新闻流
        </Button>
        <Button type={activeTab === "cross" ? "primary" : "default"} onClick={() => setActiveTab("cross")}>
          <GlobalOutlined /> 跨平台
        </Button>
      </Space>

      {/* ───── 新闻流 Tab 内容 ───── */}
      {activeTab === "news" && (
        <>
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={12} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Input
                placeholder="搜索新闻..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onPressEnter={handleSearch}
                prefix={<GlobalOutlined />}
              />
            </Col>
            <Col span={6}>
              <Select
                mode="multiple"
                placeholder="情感筛选"
                value={sentimentFilter ? [sentimentFilter] : []}
                onChange={v => setSentimentFilter(v[0] || undefined)}
                allowClear
                style={{ width: "100%" }}
                options={[
                  { value: "positive", label: "🟢 正向" },
                  { value: "neutral", label: "🟡 中性" },
                  { value: "negative", label: "🔴 负向" },
                ]}
              />
            </Col>
            <Col span={6}>
              <Select
                placeholder="来源筛选"
                value={sourceFilter}
                onChange={setSourceFilter}
                allowClear
                style={{ width: "100%" }}
                options={uniqueSources.map(s => ({ value: s, label: s }))}
              />
            </Col>
            <Col span={4}>
              <Button type="primary" onClick={handleSearch}>搜索</Button>
            </Col>
          </Row>
          {filteredNews.length === 0 ? (
            <Empty description="暂无匹配新闻" />
          ) : (
            <Table
              size="small"
              dataSource={filteredNews}
              rowKey="id"
              pagination={{ pageSize: 20, showSizeChanger: false }}
              columns={[
                { title: "时间", dataIndex: "published_at", width: 140, render: t => t ? new Date(t).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" }) : "—" },
                { title: "来源", dataIndex: "source", width: 100 },
                { title: "标题", dataIndex: "title", ellipsis: true, render: (t, r) => (
                  <a href={r.url} target="_blank" rel="noopener noreferrer">{t}</a>
                )},
                { title: "情感", dataIndex: "sentiment_label", width: 80, render: l => (
                  <Tag color={l === "positive" ? "green" : l === "negative" ? "red" : "default"}>
                    {l === "positive" ? "🟢" : l === "negative" ? "🔴" : "🟡"} {l}
                  </Tag>
                )},
                { title: "分", dataIndex: "sentiment_score", width: 50, render: s => s?.toFixed(2) || "—" },
              ]}
            />
          )}
        </Card>

        {/* ───── 订阅管理 (新闻流Tab内) ───── */}
        <Card size="small" title={<><AlertOutlined /> 订阅管理</>} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={24} lg={12}>
              <Card size="small" title="添加RSS订阅">
                <Space direction="vertical" style={{ width: "100%" }}>
                  <Input
                    placeholder="订阅名称"
                    value={rssName}
                    onChange={e => setRssName(e.target.value)}
                    prefix={<PlusOutlined />}
                  />
                  <Input
                    placeholder="RSS地址 (如 https://example.com/feed)"
                    value={rssUrl}
                    onChange={e => setRssUrl(e.target.value)}
                    prefix={<LinkOutlined />}
                  />
                  <Button type="primary" onClick={handleFetchRss} loading={fetching} icon={<ReloadOutlined />}>
                    抓取RSS
                  </Button>
                </Space>
              </Card>
            </Col>
            <Col span={24} lg={12}>
              <Card size="small" title="快速订阅">
                <Space wrap size={8}>
                  {DEFAULT_SOURCES.map(src => (
                    <Button key={src.name} size="small" onClick={() => handleQuickSource(src)} loading={fetching}>
                      {src.icon} {src.name}
                    </Button>
                  ))}
                </Space>
                <Divider style={{ margin: "12px 0" }} />
                <Text type="secondary" style={{ fontSize: 12 }}>当前订阅源 ({rssSources.length}):</Text>
                <div style={{ marginTop: 8 }}>
                  {rssSources.length === 0 ? (
                    <Text type="secondary">暂无订阅源</Text>
                  ) : (
                    <Space wrap size={4}>
                      {rssSources.map(s => (
                        <Tag key={s.url} color="blue" closable
                          onClose={async () => {
                            try {
                              await newsApi.unsubscribe(s.url);
                              loadAggNews();
                              message.success(`已取消订阅: ${s.name}`);
                            } catch { message.error("取消失败"); }
                          }}>
                          {s.name}
                        </Tag>
                      ))}
                    </Space>
                  )}
                </div>
              </Card>
            </Col>
          </Row>
        </Card>
        </>
      )}

      {/* ───── 跨平台 Tab 内容 ───── */}
      {activeTab === "cross" && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={12} style={{ marginBottom: 16 }}>
            <Col span={12}>
              <Input
                placeholder="输入关键词搜索..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onPressEnter={handleSearch}
                prefix={<GlobalOutlined />}
              />
            </Col>
            <Col span={8}>
              <Select
                mode="multiple"
                placeholder="选择平台"
                value={searchPlatforms}
                onChange={setSearchPlatforms}
                style={{ width: "100%" }}
                options={PLATFORM_OPTIONS}
              />
            </Col>
            <Col span={4}>
              <Button type="primary" onClick={handleSearch} loading={loading}>搜索</Button>
            </Col>
          </Row>
          {posts.length === 0 ? (
            <Empty description="输入关键词选择平台后搜索" />
          ) : (
            <Table
              size="small"
              dataSource={posts}
              rowKey="id"
              pagination={{ pageSize: 20, showSizeChanger: false }}
              columns={[
                { title: "平台", dataIndex: "platform", width: 100, render: p => {
                  const opt = PLATFORM_OPTIONS.find(o => o.value === p);
                  return <Tag>{opt?.icon} {opt?.label || p}</Tag>;
                }},
                { title: "标题", dataIndex: "title", ellipsis: true, render: (t, r) => (
                  <a href={r.url} target="_blank" rel="noopener noreferrer">{t}</a>
                )},
                { title: "作者", dataIndex: "author", width: 120 },
                { title: "时间", dataIndex: "published_at", width: 140, render: t => t ? new Date(t).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" }) : "—" },
                { title: "互动", dataIndex: "interactions", width: 80 },
              ]}
            />
          )}
        </Card>
      )}

      {loading && !dash ? <div style={{ textAlign: "center", padding: 60 }}><Spin size="large" /></div> :
      <Row gutter={16}>
        {/* ───── 左栏 60% ───── */}
        <Col xs={24} lg={14}>
          {/* 实时快讯 */}
          <Card size="small" title={<><BellOutlined /> 快讯 · 东方财富/36Kr/虎嗅/财联社/极客公园</>} style={{ marginBottom: 16 }}
            styles={{ body: { maxHeight: 360, overflowY: "auto" } }}>
            {normalizedNews.length === 0 ? <Empty description="暂无新闻" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
              <Timeline
                items={normalizedNews.slice(0, 30).map((n) => ({
                  color: n.sentiment_score >= 0.6 ? "green" : n.sentiment_score <= 0.4 ? "red" : "gold",
                  children: (
                    <div style={{ background: SENTI_BG[n.sentiment_score >= 0.6 ? "🟢" : n.sentiment_score <= 0.4 ? "🔴" : "🟡"] || "transparent", padding: "4px 8px", borderRadius: 4 }}>
                      <Popover
                        title={<span>{n.title}</span>}
                        overlayStyle={{ maxWidth: 460 }}
                        trigger="hover"
                        content={<NewsPopoverContent n={n} />}>
                        <Text style={{ fontSize: 13, cursor: "pointer" }}>{n.title}</Text>
                      </Popover>
                      <div>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {n.published_at ? new Date(n.published_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }).replace(/\//g, "-") : "—"} · {n.source}
                        </Text>
                        {(n.tags || []).map((t: string) => <Tag key={t} color="blue" style={{ marginLeft: 4, fontSize: 10 }}>{t}</Tag>)}
                      </div>
                    </div>
                  ),
                }))}
              />}
          </Card>

          {/* 宏观指标看板 */}
          <Card size="small" title={<><RiseOutlined /> 宏观指标看板</>} style={{ marginBottom: 16 }}>
            {macro.length === 0 ? <Empty description="暂无宏观数据" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
              <Row gutter={[12, 12]}>
                {macro.map((m: any) => (
                  <Col xs={12} sm={8} key={m.code}>
                    <Card size="small" style={{ textAlign: "center" }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>{m.name}</Text>
                      <div style={{ fontSize: 20, fontWeight: 600 }}>
                        {m.available ? m.value : "—"}
                        <span style={{ fontSize: 14, marginLeft: 4,
                          color: m.trend === "↑" ? "#52c41a" : m.trend === "↓" ? "#ff4d4f" : "#999" }}>
                          {m.trend}
                        </span>
                      </div>
                      <Text type="secondary" style={{ fontSize: 11 }}>
                        {m.change != null ? `${m.change > 0 ? "+" : ""}${m.change}` : ""} {m.date?.slice(0, 7)}
                      </Text>
                    </Card>
                  </Col>
                ))}
              </Row>}
          </Card>

          {/* 宏观事件日历 */}
          <Card size="small" title={<><CalendarOutlined /> 宏观事件日历 (近 14 天)</>} style={{ marginBottom: 16 }}>
            {events.length === 0 ? <Empty description="近期无重大事件" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
              <Timeline
                items={events.map((e: any) => ({
                  color: "blue",
                  children: (
                    <Space>
                      <Text strong>{e.date?.slice(5)}</Text>
                      <Tag>{e.country}</Tag>
                      <Text>{e.event}</Text>
                      {(e.affects || []).slice(0, 4).map((p: string) => <Tag key={p} color="geekblue" style={{ fontSize: 10 }}>{p}</Tag>)}
                    </Space>
                  ),
                }))}
              />}
          </Card>
        </Col>

        {/* ───── 右栏 40% ───── */}
        <Col xs={24} lg={10}>
          <Card size="small"
            title={<><ThunderboltOutlined /> 交易信号提醒</>}
            extra={<Button size="small" icon={<ReloadOutlined />} onClick={refreshSignals} loading={sigLoading}>扫描</Button>}
            style={{ marginBottom: 16 }}>
            {sigLoading && signals.length === 0 ? <div style={{ textAlign: "center", padding: 30 }}><Spin /></div> :
              signals.length === 0 ? <Empty description="暂无活跃信号" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
              <Space direction="vertical" style={{ width: "100%" }} size={10}>
                {signals.map((s) => {
                  const cfg = DIR_CFG[s.direction] || DIR_CFG.WATCH;
                  return (
                    <Card key={s.id} size="small" hoverable
                      style={{ background: cfg.bg, borderLeft: `4px solid ${cfg.color}` }}
                      styles={{ body: { padding: 12 } }}
                      onClick={() => navigate(`/signal/${s.id}`)}>
                      <div style={{ display: "flex", justifyContent: "space-between" }}>
                        <Text strong style={{ color: cfg.color }}>
                          {s.symbol} {s.product_name} {cfg.cn}
                        </Text>
                        <Text>{stars(s.star_rating)}</Text>
                      </div>
                      <div style={{ fontSize: 12, margin: "4px 0" }}>
                        入场 <b>{s.entry_price}</b> · 止盈 <span style={{ color: "#52c41a" }}>{s.take_profit}</span> · 止损 <span style={{ color: "#ff4d4f" }}>{s.stop_loss}</span>
                      </div>
                      <Text type="secondary" style={{ fontSize: 11 }}>{s.reason}</Text>
                      <div style={{ marginTop: 8 }} onClick={(e) => e.stopPropagation()}>
                        <Space>
                          <Button size="small" type="primary" ghost
                            onClick={() => { setOpenTarget(s); openForm.setFieldsValue({ price: s.entry_price, qty: 1, stop_loss: s.stop_loss, take_profit: s.take_profit }); }}>
                            📈 模拟开仓
                          </Button>
                          <Tooltip title={watchIds.has(s.id) ? "取消收藏" : "收藏关注"}>
                            <Button size="small" icon={watchIds.has(s.id) ? <StarFilled style={{ color: "#faad14" }} /> : <StarOutlined />}
                              onClick={() => toggleWatch(s)}>收藏</Button>
                          </Tooltip>
                        </Space>
                      </div>
                    </Card>
                  );
                })}
              </Space>}
          </Card>
        </Col>
      </Row>}

      {/* ───── 联动分析 + 远期展望 ───── */}
      {dash && (
        <Card size="small" title={<><LinkOutlined /> 联动分析 + 远期趋势展望</>} style={{ marginTop: 4 }}>
          <Row gutter={24}>
            <Col xs={24} md={8}>
              <Text strong>当前市态: </Text>
              <Tag color="processing" style={{ fontSize: 14 }}>{linkage.market_state || "—"}</Tag>
              <Paragraph type="secondary" style={{ fontSize: 12, marginTop: 8 }}>{linkage.state_reason}</Paragraph>
            </Col>
            <Col xs={24} md={8}>
              <Text strong>新闻影响品种</Text>
              <div style={{ marginTop: 8 }}>
                {(linkage.news_impact || []).length === 0 ? <Text type="secondary">无品种相关新闻</Text> :
                  (linkage.news_impact || []).map((n: any) => (
                    <div key={n.product} style={{ fontSize: 13 }}>
                      {n.label} {n.product_cn}({n.product}) · {n.count} 条
                    </div>
                  ))}
              </div>
            </Col>
            <Col xs={24} md={8}>
              <Text strong>宏观 → 品种关联度</Text>
              <div style={{ marginTop: 8 }}>
                {(linkage.linkages || []).slice(0, 6).map((l: any, i: number) => (
                  <div key={i} style={{ fontSize: 13 }}>
                    {l.indicator}{l.trend} → {l.product_cn} <b style={{ color: l.corr > 0 ? "#52c41a" : "#ff4d4f" }}>{l.corr > 0 ? "+" : ""}{l.corr}</b>
                  </div>
                ))}
              </div>
            </Col>
          </Row>
          <Divider style={{ margin: "12px 0" }} />
          <Text strong><RiseOutlined /> 远期趋势</Text>
          <div style={{ marginTop: 8 }}>
            {outlook.map((o: any, i: number) => (
              <Paragraph key={i} style={{ marginBottom: 4, fontSize: 13 }}>• {o.text}</Paragraph>
            ))}
          </div>
        </Card>
      )}

      <Modal title="模拟开仓" open={!!openTarget} onOk={submitOpen} onCancel={() => setOpenTarget(null)} okText="确认开仓" cancelText="取消">
        {openTarget && (
          <Form form={openForm} layout="vertical">
            <Text>品种: <b>{openTarget.symbol} {openTarget.product_name}</b> · 方向: <b>{DIR_CFG[openTarget.direction]?.cn}</b></Text>
            <Form.Item name="price" label="开仓价" rules={[{ required: true }]} style={{ marginTop: 12 }}>
              <InputNumber style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="qty" label="数量 (手)" rules={[{ required: true }]}>
              <InputNumber style={{ width: "100%" }} min={1} />
            </Form.Item>
            <Row gutter={12}>
              <Col span={12}><Form.Item name="take_profit" label="止盈"><InputNumber style={{ width: "100%" }} /></Form.Item></Col>
              <Col span={12}><Form.Item name="stop_loss" label="止损"><InputNumber style={{ width: "100%" }} /></Form.Item></Col>
            </Row>
          </Form>
        )}
      </Modal>
    </div>
  );
}

function stripHtml(html: string) {
  return html.replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ").replace(/\s+/g, " ").trim();
}

function fmtTime(iso: string) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "—";
  return d.toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" });
}

function getSummary(n: NormalizedNewsItem): string {
  // 东财 items: raw.content 已是纯文本摘要，直接用
  if (n.raw?.content) return n.raw.content;
  // RSS items: summary 可能是 HTML，先去标签
  const raw = stripHtml(n.summary || "");
  return raw || n.title || "";
}

function NewsPopoverContent({ n }: { n: NormalizedNewsItem }) {
  const sentTag = n.sentiment_label === "positive" ? "green" : n.sentiment_label === "negative" ? "red" : "default";
  const summary = getSummary(n);
  return (
    <div style={{ maxWidth: 440 }}>
      <Paragraph style={{ marginBottom: 8, whiteSpace: "pre-wrap", maxHeight: 280, overflowY: "auto" }}>
        {summary.slice(0, 100)}{summary.length > 100 ? "…" : ""}
      </Paragraph>
      <Space wrap size={4}>
        <Tag color={sentTag}>{n.sentiment_label} {n.sentiment_score.toFixed(2)}</Tag>
        {(n.tags || []).slice(0, 4).map((t: string) => <Tag key={t} color="blue">{t}</Tag>)}
        <Text type="secondary" style={{ fontSize: 11 }}>{n.source}</Text>
        <Text type="secondary" style={{ fontSize: 11 }}>{new Date(n.published_at).toLocaleString("zh-CN", { timeZone: "Asia/Shanghai" })}</Text>
      </Space>
    </div>
  );
}
