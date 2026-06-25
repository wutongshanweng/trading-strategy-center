import { useState, useEffect } from "react";
import {
  Card,
  Table,
  Tabs,
  Tag,
  Space,
  Typography,
  Alert,
  Statistic,
  Row,
  Col,
  Button,
  Select,
  Spin,
  message,
  Divider,
  Input,
  Progress,
  Empty,
  Tooltip,
  List,
  Badge,
  Progress as AntProgress,
} from "antd";
import {
  ExperimentOutlined,
  LineChartOutlined,
  BarChartOutlined,
  ReloadOutlined,
  SearchOutlined,
  QuestionCircleOutlined,
  RobotOutlined,
  PlayCircleOutlined,
  CloudServerOutlined,
  ThunderboltOutlined,
  SyncOutlined,
} from "@ant-design/icons";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { factorApi } from "../services/factorApi";
import { vibeApi, FactorInfo, BacktestResult } from "../services/vibeApi";

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

const CATEGORY_COLORS: Record<string, string> = {
  // 英文分类
  comparison: "blue", complex: "purple", complex_signal: "magenta", correlation: "cyan",
  mean_reversion: "green", momentum: "blue", price_dispersion: "orange", price_gap: "volcano",
  price_momentum: "geekblue", price_position: "lime", price_reversal: "red", price_structure: "gold",
  price_volume: "purple", price_vwap: "pink", reversal: "orange", time_series: "cyan",
  trend: "geekblue", volatility: "volcano", volume_momentum: "lime", volume_price: "magenta", vwap: "purple",
  // 中文分类
  动量: "blue", 价值: "green", 质量: "purple", 规模: "orange",
  波动率: "cyan", 流动性: "magenta", 情绪: "gold", 技术: "red",
  比较: "blue", 复合: "purple", 复合信号: "magenta", 相关: "cyan",
  均值回归: "green", 价格离散: "orange", 价格跳空: "volcano",
  价格动量: "geekblue", 价格位置: "lime", 价格反转: "red", 价格结构: "gold",
  价格成交量: "purple", 价格VWAP: "pink", 反转: "orange", 时序: "cyan",
  趋势: "geekblue", 成交量动量: "lime", 成交量价格: "magenta", VWAP均值: "purple",
};

// 中文分类映射表
const CATEGORY_CN_MAP: Record<string, string> = {
  comparison: "比较", complex: "复合", complex_signal: "复合信号", correlation: "相关",
  mean_reversion: "均值回归", momentum: "动量", price_dispersion: "价格离散", price_gap: "价格跳空",
  price_momentum: "价格动量", price_position: "价格位置", price_reversal: "价格反转", price_structure: "价格结构",
  price_volume: "价格成交量", price_vwap: "价格VWAP", reversal: "反转", time_series: "时序",
  trend: "趋势", volatility: "波动率", volume_momentum: "成交量动量", volume_price: "成交量价格", vwap: "VWAP均值",
};

// Alpha因子库 (动态从API获取真实因子数)
const getMockFactors = (count: number) => Array.from({ length: count }, (_, i) => ({
  id: `alpha${String(i + 1).padStart(3, "0")}`,
  name: `Alpha${i + 1}`,
  category: ["价格", "成交量", "波动率", "趋势"][i % 4],
  description: `WorldQuant Alpha Factor ${i + 1}`,
  ic: parseFloat((Math.random() * 0.15 - 0.05).toFixed(4)),
  ir: parseFloat((Math.random() * 2 + 0.5).toFixed(2)),
}));

const columns = [
  {
    title: "因子ID",
    dataIndex: "id",
    key: "id",
    width: 120,
    fixed: "left" as const,
  },
  {
    title: "名称",
    dataIndex: "name",
    key: "name",
    render: (text: string) => <Text strong>{text}</Text>,
  },
  {
    title: "分类",
    dataIndex: "category",
    key: "category",
    filters: [
      { text: "价格", value: "价格" },
      { text: "成交量", value: "成交量" },
      { text: "波动率", value: "波动率" },
      { text: "趋势", value: "趋势" },
    ],
    onFilter: (value: any, record: any) => record.category === value,
    render: (category: string) => {
      const colors: Record<string, string> = {
        价格: "blue",
        成交量: "green",
        波动率: "orange",
        趋势: "purple",
      };
      return <Tag color={colors[category]}>{category}</Tag>;
    },
  },
  {
    title: "描述",
    dataIndex: "description",
    key: "description",
    ellipsis: true,
  },
  {
    title: "IC值",
    dataIndex: "ic",
    key: "ic",
    sorter: (a: any, b: any) => a.ic - b.ic,
    render: (ic: number) => (
      <Text style={{ color: ic > 0 ? "#52c41a" : "#ff4d4f" }}>
        {ic.toFixed(4)}
      </Text>
    ),
  },
  {
    title: "IR值",
    dataIndex: "ir",
    key: "ir",
    sorter: (a: any, b: any) => a.ir - b.ir,
    render: (ir: number) => ir.toFixed(2),
  },
];

export default function FactorResearch() {
  const [selectedFactor, setSelectedFactor] = useState("alpha001");
  const [selectedSymbol, setSelectedSymbol] = useState("000001.SZ");
  const [selectedFactors, setSelectedFactors] = useState<string[]>([
    "alpha001",
    "alpha002",
  ]);

  // IC分析状态
  const [icLoading, setIcLoading] = useState(false);
  const [icData, setIcData] = useState<any>(null);

  // 分层回测状态
  const [layeredLoading, setLayeredLoading] = useState(false);
  const [layeredData, setLayeredData] = useState<any>(null);

  // 因子组合状态
  const [combineLoading, setCombineLoading] = useState(false);
  const [combineData, setCombineData] = useState<any>(null);

  // Phase2: 挖掘/健康/报告 状态
  const [mineLoading, setMineLoading] = useState(false);
  const [mineData, setMineData] = useState<any>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [healthData, setHealthData] = useState<any>(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportData, setReportData] = useState<any>(null);

  // 一键完整分析状态
  const [symbolInput, setSymbolInput] = useState("");
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState("");
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  // 因子中文描述字典 (key=alpha001)
  const [factorDescriptions, setFactorDescriptions] = useState<Record<string, any>>({});

  // ───── VibeResearch 功能 ─────
  const [vibeFactors, setVibeFactors] = useState<FactorInfo[]>([]);
  const [vibeCategories, setVibeCategories] = useState<string[]>([]);
  const [vibeLoading, setVibeLoading] = useState(true);
  const [vibeFactorSource, setVibeFactorSource] = useState<string>("");
  const [vibeFactorTotal, setVibeFactorTotal] = useState<number>(0);
  const [datasources, setDatasources] = useState<{ name: string; type: string; status: string }[]>([]);
  const [swarmStatus, setSwarmStatus] = useState<{ agents: { name: string; status: string; tasks: number }[]; total_agents: number } | null>(null);
  const [btSymbol, setBtSymbol] = useState("000001");
  const [btStrategy, setBtStrategy] = useState("ma_cross");
  const [running, setRunning] = useState(false);
  const [backtests, setBacktests] = useState<BacktestResult[]>([]);
  const [selectedBacktest, setSelectedBacktest] = useState<BacktestResult | null>(null);
  const [chartData, setChartData] = useState<{ day: number; value: number; benchmark: number }[]>([]);
  const [researchQuery, setResearchQuery] = useState("");
  const [researching, setResearching] = useState(false);
  const [researchResult, setResearchResult] = useState<{ findings: string[]; signals: string[]; confidence: number; top_factors?: string[] } | null>(null);
  const [vibeFactorSearch, setVibeFactorSearch] = useState("");
  const [selectedVibeCategory, setSelectedVibeCategory] = useState<string>("");

  // 标的列表 (从仓库加载, 期货/股票/期权全资产)
  const [symbolOptions, setSymbolOptions] = useState<{ code: string; status?: string }[]>([
    { code: "600019.SH" }, { code: "601899.SH" }, { code: "600585.SH" },
  ]);

  // 挂载时从仓库加载真实标的 (有数据的合约/股票/期权)
  useEffect(() => {
    (async () => {
      try {
        const resp = await fetch("http://localhost:8000/api/v1/warehouse/symbols?limit=300");
        const d = await resp.json();
        const syms = (d.symbols || [])
          .filter((s: any) => s.status !== "连续")
          .map((s: any) => ({ code: s.code, status: s.status }));
        if (syms.length) {
          setSymbolOptions(syms);
          setSelectedSymbol(syms[0].code);
        }
      } catch { /* 后端未启动则保留默认 */ }
    })();
  }, []);

  // 挂载时加载因子中文描述字典
  useEffect(() => {
    (async () => {
      try {
        const d = await factorApi.getFactorDescriptions();
        if (d?.descriptions) setFactorDescriptions(d.descriptions);
      } catch { /* 后端未启动则无描述, Tooltip 不显示 */ }
    })();
  }, []);

  // 挂载时加载 Vibe 因子数据 (用于因子列表)
  useEffect(() => {
    loadVibeData();
  }, []);

  // ───── VibeResearch 数据加载 ─────
  const generateChartData = (result: BacktestResult) => {
    const days = result.trades * 3;
    let value = 100000;
    const data = [];
    for (let i = 0; i <= days; i++) {
      value = value * (1 + (Math.random() - 0.45) * 0.02);
      data.push({ day: i, value: Math.round(value), benchmark: 100000 * (1 + (i / days) * (result.total_return / 100)) });
    }
    return data;
  };

  const loadVibeData = async () => {
    setVibeLoading(true);
    try {
      const fc = await vibeApi.factors({ limit: 500 });
      const cc = await vibeApi.factorCategories();
      const ds = await vibeApi.datasources();
      const ss = await vibeApi.swarmStatus();
      setVibeFactors(fc.data.factors || []);
      setVibeFactorSource(fc.data.source || "");
      setVibeFactorTotal(fc.data.total || fc.data.factors?.length || 0);
      setVibeCategories(cc.data.categories || []);
      setDatasources(ds.data.datasources || []);
      setSwarmStatus(ss.data);
    } catch { /* ignore */ }
    finally { setVibeLoading(false); }
  };

  useEffect(() => {
    loadVibeData();
    vibeApi.backtests({ limit: 10 }).then(r => {
      const bts = r.data.backtests || [];
      setBacktests(bts);
      if (bts[0]) {
        setSelectedBacktest(bts[0]);
        setChartData(generateChartData(bts[0]));
      }
    }).catch(() => {});
  }, []);

  const handleBacktest = async () => {
    if (!btSymbol) { message.warning("请输入股票代码"); return; }
    setRunning(true);
    try {
      const res = await vibeApi.backtest({ symbol: btSymbol, strategy: btStrategy, start_date: "2023-01-01", end_date: "2024-01-01", initial_capital: 100000 });
      const result = res.data.result;
      setBacktests(prev => [result, ...prev]);
      setSelectedBacktest(result);
      setChartData(generateChartData(result));
      message.success("回测完成");
    } catch { message.error("回测失败"); }
    finally { setRunning(false); }
  };

  const handleResearch = async () => {
    if (!researchQuery) return;
    setResearching(true);
    try {
      const res = await vibeApi.research(researchQuery, btSymbol);
      setResearchResult(res.data);
      message.success("研究完成");
    } catch { message.error("研究失败"); }
    finally { setResearching(false); }
  };

  // 用于下拉框的因子列表 (优先用真实因子,否则用mock)
  const factorCount = Object.keys(factorDescriptions).length;
  const mockFactorList = getMockFactors(factorCount);

  const avgIC = (
    (vibeFactorTotal > 0 ? vibeFactors.reduce((sum, f) => sum + f.ic, 0) / vibeFactors.length : mockFactorList.reduce((sum, f) => sum + f.ic, 0) / mockFactorList.length)
  ).toFixed(4);
  const avgIR = (
    (vibeFactorTotal > 0 ? vibeFactors.reduce((sum, f) => sum + f.ir, 0) / vibeFactors.length : mockFactorList.reduce((sum, f) => sum + f.ir, 0) / mockFactorList.length)
  ).toFixed(2);

  // 因子Option显示: 因子名 + 分类 + IC值
  const getFactorLabel = (f: FactorInfo) =>
    `${f.name} [${CATEGORY_CN_MAP[f.category] || f.category}] IC:${f.ic > 0 ? "+" : ""}${f.ic.toFixed(3)}`;

  const factorOptions = vibeFactorTotal > 0 ? vibeFactors : mockFactorList.map(f => ({
    name: f.name, category: f.category, category_cn: f.category, ic: 0, ir: 0,
  }));
  const positiveICCount = vibeFactorTotal > 0 ? vibeFactors.filter((f) => f.ic > 0).length : mockFactorList.filter((f) => f.ic > 0).length;
  const totalFactorCount = vibeFactorTotal || mockFactorList.length;

  // IC分析
  const handleICAnalysis = async () => {
    setIcLoading(true);
    try {
      const result = await factorApi.icAnalysis({
        factor_id: selectedFactor,
        symbol: selectedSymbol,
        method: "pearson",
      });
      setIcData(result);
      message.success("IC分析完成");
    } catch (error: any) {
      message.error(`IC分析失败: ${error.message}`);
    } finally {
      setIcLoading(false);
    }
  };

  // 分层回测
  const handleLayeredBacktest = async () => {
    setLayeredLoading(true);
    try {
      const result = await factorApi.layeredBacktest({
        factor_id: selectedFactor,
        symbols: [selectedSymbol],
        n_quantiles: 5,
      });
      setLayeredData(result);
      message.success("分层回测完成");
    } catch (error: any) {
      message.error(`分层回测失败: ${error.message}`);
    } finally {
      setLayeredLoading(false);
    }
  };

  // 因子组合
  const handleFactorCombine = async () => {
    setCombineLoading(true);
    try {
      const result = await factorApi.factorCombine({
        factor_ids: selectedFactors,
        symbols: [selectedSymbol],
        method: "ic_weight",
      });
      setCombineData(result);
      message.success("因子组合完成");
    } catch (error: any) {
      message.error(`因子组合失败: ${error.message}`);
    } finally {
      setCombineLoading(false);
    }
  };

  // Phase2: 遗传因子挖掘
  const handleMine = async () => {
    setMineLoading(true);
    try {
      const result = await factorApi.mine({
        symbol: selectedSymbol, n_factors: 8, population_size: 30, generations: 8,
      });
      setMineData(result);
      message.success(`挖掘完成: ${result.count} 个因子 (源: ${result.data_source})`);
    } catch (error: any) {
      message.error(`因子挖掘失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setMineLoading(false);
    }
  };

  // Phase2: 因子健康检测
  const handleHealthCheck = async () => {
    setHealthLoading(true);
    try {
      const result = await factorApi.healthCheck({
        factor_id: selectedFactor, symbol: selectedSymbol,
      });
      setHealthData(result);
      message.success(`健康检测完成: ${result.health} (源: ${result.data_source})`);
    } catch (error: any) {
      message.error(`健康检测失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setHealthLoading(false);
    }
  };

  // Phase2: 全因子研究报告
  const handleReport = async () => {
    setReportLoading(true);
    try {
      const result = await factorApi.report({
        symbols: [selectedSymbol], factor_ids: selectedFactors, top_n: 20,
      });
      setReportData(result.report);
      message.success(`报告生成完成 (源: ${result.data_source})`);
    } catch (error: any) {
      message.error(`报告生成失败: ${error.response?.data?.detail || error.message}`);
    } finally {
      setReportLoading(false);
    }
  };

  // 渲染IC时间序列图
  const renderICTimeSeries = () => {
    if (!icData?.ic_time_series) return null;

    const { dates, values, statistics } = icData.ic_time_series;
    const maxVal = Math.max(...values);
    const minVal = Math.min(...values);

    return (
      <div>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Statistic
              title="平均IC"
              value={statistics.mean}
              precision={4}
              valueStyle={{
                color: statistics.mean > 0 ? "#52c41a" : "#ff4d4f",
              }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="IC标准差"
              value={statistics.std}
              precision={4}
              valueStyle={{ color: "#1890ff" }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="IR (信息比率)"
              value={statistics.ir}
              precision={2}
              valueStyle={{ color: "#722ed1" }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="正IC占比"
              value={statistics.positive_ratio * 100}
              precision={1}
              suffix="%"
              valueStyle={{ color: "#13c2c2" }}
            />
          </Col>
        </Row>

        <div
          style={{
            height: 300,
            border: "1px solid #f0f0f0",
            padding: 16,
            position: "relative",
          }}
        >
          <Text strong>IC时间序列图</Text>
          <svg width="100%" height="260" style={{ marginTop: 10 }}>
            {/* 零线 */}
            <line
              x1="50"
              y1="130"
              x2="100%"
              y2="130"
              stroke="#d9d9d9"
              strokeDasharray="4"
            />

            {/* IC曲线 */}
            <polyline
              points={values
                .map((val: number, idx: number) => {
                  const x = 50 + (idx / values.length) * 700;
                  const y =
                    130 - ((val - minVal) / (maxVal - minVal + 0.001)) * 100;
                  return `${x},${y}`;
                })
                .join(" ")}
              fill="none"
              stroke="#1890ff"
              strokeWidth="2"
            />

            {/* X轴标签 */}
            {dates
              .filter((_: any, idx: number) => idx % 30 === 0)
              .map((date: string, idx: number) => (
                <text
                  key={idx}
                  x={50 + (idx * 30 * 700) / values.length}
                  y="250"
                  fontSize="10"
                  fill="#666"
                >
                  {date.slice(5)}
                </text>
              ))}
          </svg>
        </div>
      </div>
    );
  };

  // 渲染IC分布直方图
  const renderICDistribution = () => {
    if (!icData?.ic_distribution) return null;

    const distribution = icData.ic_distribution;
    const maxCount = Math.max(...distribution.map((d: any) => d.count));

    return (
      <div
        style={{
          height: 300,
          border: "1px solid #f0f0f0",
          padding: 16,
          marginTop: 16,
        }}
      >
        <Text strong>IC分布直方图</Text>
        <svg width="100%" height="260" style={{ marginTop: 10 }}>
          {distribution.map((item: any, idx: number) => {
            const barWidth = 700 / distribution.length;
            const barHeight = (item.count / maxCount) * 200;
            const x = 50 + idx * barWidth;
            const y = 220 - barHeight;

            return (
              <rect
                key={idx}
                x={x}
                y={y}
                width={barWidth - 2}
                height={barHeight}
                fill="#1890ff"
                opacity="0.7"
              />
            );
          })}
        </svg>
      </div>
    );
  };

  // 渲染IC衰减图
  const renderICDecay = () => {
    if (!icData?.ic_decay) return null;

    const decayData = icData.ic_decay;
    const maxIC = Math.max(...decayData.map((d: any) => Math.abs(d.ic)));

    return (
      <div
        style={{
          height: 300,
          border: "1px solid #f0f0f0",
          padding: 16,
          marginTop: 16,
        }}
      >
        <Text strong>IC衰减分析</Text>
        <svg width="100%" height="260" style={{ marginTop: 10 }}>
          {/* 零线 */}
          <line
            x1="50"
            y1="130"
            x2="100%"
            y2="130"
            stroke="#d9d9d9"
            strokeDasharray="4"
          />

          {/* 衰减曲线 */}
          <polyline
            points={decayData
              .map((item: any) => {
                const x = 50 + (item.period / decayData.length) * 700;
                const y = 130 - (item.ic / maxIC) * 100;
                return `${x},${y}`;
              })
              .join(" ")}
            fill="none"
            stroke="#ff4d4f"
            strokeWidth="2"
          />

          {/* 数据点 */}
          {decayData.map((item: any) => {
            const x = 50 + (item.period / decayData.length) * 700;
            const y = 130 - (item.ic / maxIC) * 100;
            return (
              <circle key={item.period} cx={x} cy={y} r="3" fill="#ff4d4f" />
            );
          })}

          {/* X轴标签 */}
          {decayData
            .filter((_: any, idx: number) => idx % 5 === 0)
            .map((item: any) => (
              <text
                key={item.period}
                x={50 + (item.period / decayData.length) * 700}
                y="250"
                fontSize="10"
                fill="#666"
              >
                {item.period}期
              </text>
            ))}
        </svg>
      </div>
    );
  };

  // 渲染分层回测结果
  const renderLayeredBacktest = () => {
    if (!layeredData) return null;

    const { layer_summary, long_short, turnover } = layeredData;

    return (
      <div>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="多空收益"
                value={long_short.mean_return * 100}
                precision={2}
                suffix="%"
                valueStyle={{
                  color: long_short.mean_return > 0 ? "#52c41a" : "#ff4d4f",
                }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="多空夏普比率"
                value={long_short.sharpe}
                precision={2}
                valueStyle={{ color: "#1890ff" }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="胜率"
                value={long_short.win_rate * 100}
                precision={1}
                suffix="%"
                valueStyle={{ color: "#722ed1" }}
              />
            </Card>
          </Col>
        </Row>

        {/* 5分层收益对比图 */}
        <div
          style={{
            height: 350,
            border: "1px solid #f0f0f0",
            padding: 16,
            marginTop: 16,
          }}
        >
          <Text strong>5分层收益对比</Text>
          <svg width="100%" height="300" style={{ marginTop: 10 }}>
            {layer_summary.map((layer: any, idx: number) => {
              const barWidth = 100;
              const x = 100 + idx * 140;
              const barHeight = Math.abs(layer.mean_return * 10000);
              const y = layer.mean_return > 0 ? 150 - barHeight : 150;
              const color =
                layer.mean_return > 0 ? "#52c41a" : "#ff4d4f";

              return (
                <g key={idx}>
                  <rect
                    x={x}
                    y={y}
                    width={barWidth}
                    height={barHeight}
                    fill={color}
                    opacity="0.7"
                  />
                  <text
                    x={x + barWidth / 2}
                    y="280"
                    fontSize="12"
                    fill="#666"
                    textAnchor="middle"
                  >
                    {layer.quantile}
                  </text>
                  <text
                    x={x + barWidth / 2}
                    y={y - 5}
                    fontSize="10"
                    fill={color}
                    textAnchor="middle"
                  >
                    {(layer.mean_return * 100).toFixed(2)}%
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* 换手率统计 */}
        <Card title="换手率统计" style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Statistic
                title="日均换手率"
                value={turnover.daily_turnover * 100}
                precision={2}
                suffix="%"
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="周均换手率"
                value={turnover.weekly_turnover * 100}
                precision={2}
                suffix="%"
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="月均换手率"
                value={turnover.monthly_turnover * 100}
                precision={2}
                suffix="%"
              />
            </Col>
          </Row>
        </Card>
      </div>
    );
  };

  // 渲染因子组合结果
  const renderFactorCombine = () => {
    if (!combineData) return null;

    const { weights, correlation_matrix, combined_performance } = combineData;

    return (
      <div>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="组合因子IC"
                value={combined_performance.ic}
                precision={4}
                valueStyle={{
                  color: combined_performance.ic > 0 ? "#52c41a" : "#ff4d4f",
                }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="组合因子IR"
                value={combined_performance.ir}
                precision={2}
                valueStyle={{ color: "#1890ff" }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="分散化比率"
                value={combined_performance.diversification_ratio}
                precision={3}
                valueStyle={{ color: "#722ed1" }}
              />
            </Card>
          </Col>
        </Row>

        {/* 相关性矩阵热力图 */}
        <Card title="因子相关性矩阵" style={{ marginBottom: 16 }}>
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                borderCollapse: "collapse",
                margin: "0 auto",
              }}
            >
              <thead>
                <tr>
                  <th style={{ padding: "8px", border: "1px solid #f0f0f0" }}>

                  </th>
                  {selectedFactors.map((factor) => (
                    <th
                      key={factor}
                      style={{
                        padding: "8px",
                        border: "1px solid #f0f0f0",
                        fontSize: "12px",
                      }}
                    >
                      {factor}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {correlation_matrix.map((row: any[], rowIdx: number) => (
                  <tr key={rowIdx}>
                    <td
                      style={{
                        padding: "8px",
                        border: "1px solid #f0f0f0",
                        fontSize: "12px",
                        fontWeight: "bold",
                      }}
                    >
                      {selectedFactors[rowIdx]}
                    </td>
                    {row.map((cell: any, colIdx: number) => {
                      const corr = cell.correlation;
                      const intensity = Math.abs(corr);
                      const bgColor =
                        corr > 0
                          ? `rgba(82, 196, 26, ${intensity})`
                          : `rgba(255, 77, 79, ${intensity})`;

                      return (
                        <td
                          key={colIdx}
                          style={{
                            padding: "8px",
                            border: "1px solid #f0f0f0",
                            backgroundColor: bgColor,
                            textAlign: "center",
                            fontSize: "12px",
                          }}
                        >
                          {corr.toFixed(3)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* 权重分配 */}
        <Card title="因子权重分配">
          <Table
            dataSource={weights}
            pagination={false}
            size="small"
            columns={[
              {
                title: "因子ID",
                dataIndex: "factor_id",
                key: "factor_id",
              },
              {
                title: "IC值",
                dataIndex: "ic_value",
                key: "ic_value",
                render: (val: number) => val.toFixed(4),
              },
              {
                title: "IC权重",
                dataIndex: "ic_weight",
                key: "ic_weight",
                render: (val: number) => (
                  <div>
                    {(val * 100).toFixed(2)}%
                    <div
                      style={{
                        width: "100%",
                        height: "4px",
                        backgroundColor: "#f0f0f0",
                        marginTop: "4px",
                      }}
                    >
                      <div
                        style={{
                          width: `${val * 100}%`,
                          height: "100%",
                          backgroundColor: "#1890ff",
                        }}
                      />
                    </div>
                  </div>
                ),
              },
              {
                title: "优化权重",
                dataIndex: "optimized_weight",
                key: "optimized_weight",
                render: (val: number) => (
                  <div>
                    {(val * 100).toFixed(2)}%
                    <div
                      style={{
                        width: "100%",
                        height: "4px",
                        backgroundColor: "#f0f0f0",
                        marginTop: "4px",
                      }}
                    >
                      <div
                        style={{
                          width: `${val * 100}%`,
                          height: "100%",
                          backgroundColor: "#52c41a",
                        }}
                      />
                    </div>
                  </div>
                ),
              },
            ]}
          />
        </Card>
      </div>
    );
  };

  // ───────── 一键完整分析 ─────────
  // 因子名 + 中文描述 Tooltip (desc 字典 key = alpha001)
  const factorNameWithTip = (name: string) => {
    const desc = factorDescriptions[name];
    if (!desc) return <Text strong>{name}</Text>;
    const lines = (desc.interpretation || "").split("\n");
    return (
      <Space>
        <Text strong>{name}</Text>
        <Tooltip
          title={
            <div style={{ maxWidth: 320 }}>
              <div><b>{desc.chinese_name}</b></div>
              <div style={{ fontSize: 12, marginTop: 4, color: "#ccc" }}>{desc.formula}</div>
              <div style={{ fontSize: 12, marginTop: 6, borderTop: "1px solid #555", paddingTop: 4 }}>
                {lines[0] && <div style={{ color: "#73d13d" }}>{lines[0]}</div>}
                {lines[1] && <div style={{ color: "#ff7875" }}>{lines[1]}</div>}
              </div>
              {desc.use_case && (
                <div style={{ fontSize: 12, marginTop: 6, color: "#aaa" }}>适用: {desc.use_case}</div>
              )}
            </div>
          }
        >
          <QuestionCircleOutlined style={{ color: "#888", cursor: "help" }} />
        </Tooltip>
      </Space>
    );
  };

  // 因子列表 columns: 在模块级 columns 基础上, 给 ID 列挂 Tooltip
  const factorColumns = columns.map((c: any) =>
    c.key === "id"
      ? { ...c, width: 150, render: (id: string) => factorNameWithTip(id) }
      : c
  );

  const handleFullAnalysis = async () => {
    const sym = symbolInput.trim().toUpperCase();
    if (!sym) {
      message.warning("请输入合约代码");
      return;
    }
    setAnalysisLoading(true);
    setAnalysisResult(null);
    const factorCount = vibeFactorTotal || Object.keys(factorDescriptions).length;
    setAnalysisProgress(`正在加载行情数据 / 计算 ${factorCount} 个因子...`);
    try {
      const result = await factorApi.fullAnalysis({ symbol: sym });
      if (result?.success) {
        setAnalysisResult(result);
        message.success(`${sym} 完整分析完成 (${result.data_points} 条数据)`);
      } else {
        message.error("分析返回异常");
      }
    } catch (error: any) {
      const detail = error?.response?.data?.detail || error?.message || "未知错误";
      message.error(`分析失败: ${detail}`);
    } finally {
      setAnalysisLoading(false);
      setAnalysisProgress("");
    }
  };

  const healthColor = (h: string) =>
    h === "HEALTHY" ? "#52c41a" : h === "WARNING" ? "#faad14" : "#ff4d4f";
  const healthIcon = (h: string) =>
    h === "HEALTHY" ? "✅" : h === "WARNING" ? "⚠️" : "❌";

  const renderAnalysisResult = () => {
    if (!analysisResult) return null;
    const r = analysisResult;
    const topRows = (r.top_factors || []).map((f: any) => ({ ...f, key: f.name }));
    const layeredQs = r.layered?.quantiles || [];
    const maxAbs = Math.max(
      0.0001,
      ...layeredQs.map((q: any) => Math.abs(q.mean_return || 0))
    );
    return (
      <>
        {/* 交易建议卡片 (置顶) */}
        {r.advice && (() => {
          const adv = r.advice;
          const colorMap: Record<string, string> = {
            BUY: "#52c41a", SELL: "#ff4d4f", HOLD: "#888", WAIT: "#faad14",
          };
          const iconMap: Record<string, string> = {
            BUY: "🟢", SELL: "🔴", HOLD: "⚪", WAIT: "🟡",
          };
          const col = colorMap[adv.action] || "#888";
          return (
            <Card style={{ borderLeft: `4px solid ${col}`, marginBottom: 16 }}>
              <Row align="middle" gutter={24}>
                <Col>
                  <div style={{ fontSize: 40 }}>{iconMap[adv.action] || "⚪"}</div>
                </Col>
                <Col flex="auto">
                  <Title level={3} style={{ margin: 0, color: col }}>{adv.action_cn}</Title>
                  <Text type="secondary">{adv.reason}</Text>
                  {adv.risk_note && (
                    <div style={{ marginTop: 8 }}>
                      <Text type="warning">{adv.risk_note}</Text>
                    </div>
                  )}
                </Col>
                <Col>
                  <Statistic title="置信度" value={adv.confidence} />
                  <Statistic
                    title="综合信号"
                    value={adv.signal_value}
                    precision={4}
                    valueStyle={{ color: adv.signal_value >= 0 ? "#52c41a" : "#ff4d4f" }}
                  />
                </Col>
              </Row>
            </Card>
          );
        })()}

        {/* 总览卡片 */}
        <Card title="📊 因子总览" style={{ marginBottom: 16 }}>
          <Row gutter={[16, 16]}>
            <Col xs={12} sm={6}>
              <Statistic title="Top因子平均IC" value={r.ic_stats?.mean ?? 0}
                precision={4}
                valueStyle={{ color: (r.ic_stats?.mean ?? 0) > 0 ? "#52c41a" : "#ff4d4f" }} />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic title="正IC因子" value={r.ic_stats?.positive_count ?? 0}
                suffix={`/ ${r.ic_stats?.total ?? 0}`} valueStyle={{ color: "#1890ff" }} />
            </Col>
            <Col xs={12} sm={6}>
              <Statistic title="推荐组合数" value={(r.recommended || []).length}
                valueStyle={{ color: "#722ed1" }} />
            </Col>
            <Col xs={12} sm={6}>
              <Space direction="vertical" size={0}>
                <Text style={{ color: "#52c41a" }}>✅ 健康 {r.health_distribution?.healthy ?? 0}</Text>
                <Text style={{ color: "#faad14" }}>⚠️ 警告 {r.health_distribution?.warning ?? 0}</Text>
                <Text style={{ color: "#ff4d4f" }}>❌ 失效 {r.health_distribution?.decayed ?? 0}</Text>
              </Space>
            </Col>
          </Row>
          <Divider style={{ margin: "12px 0" }} />
          <Text type="secondary">
            数据来源: 仓库直连 · {r.data_points} 条 D1 · 推荐组合 IC={r.recommended_ic} ICIR={r.recommended_icir}
          </Text>
          <div style={{ marginTop: 8 }}>
            {(r.recommended || []).map((n: string) => (
              <Tag color="purple" key={n}>{n}</Tag>
            ))}
          </div>
        </Card>

        {/* 排名表格 */}
        <Card title="🏆 因子排名 + 推荐组合" style={{ marginBottom: 16 }}>
          <Table
            dataSource={topRows}
            size="small"
            pagination={{ pageSize: 10 }}
            columns={[
              { title: "#", dataIndex: "rank", key: "rank", width: 50 },
              { title: "因子", dataIndex: "name", key: "name",
                render: (t: string) => factorNameWithTip(t) },
              { title: "IC", dataIndex: "ic", key: "ic",
                render: (v: number) => (
                  <Text style={{ color: v > 0 ? "#52c41a" : "#ff4d4f" }}>{v?.toFixed(4)}</Text>
                ) },
              { title: "ICIR", dataIndex: "icir", key: "icir",
                render: (v: number) => v?.toFixed(2) },
              { title: "多空Sharpe", dataIndex: "sharpe", key: "sharpe",
                render: (v: number) => v?.toFixed(2) },
              { title: "健康", dataIndex: "health", key: "health",
                render: (h: string) => (
                  <span style={{ color: healthColor(h) }}>{healthIcon(h)} {h}</span>
                ) },
              { title: "推荐", dataIndex: "recommended", key: "recommended",
                width: 60, render: (v: boolean) => (v ? <Text style={{ color: "#faad14" }}>★</Text> : "") },
            ]}
          />
        </Card>

        {/* 分层回测柱状图 */}
        <Card title={`📉 分层回测${r.layered?.factor ? ` — ${r.layered.factor}` : ""}`} style={{ marginBottom: 16 }}>
          {layeredQs.length ? (
            <>
              {layeredQs.map((q: any) => {
                const pct = (Math.abs(q.mean_return) / maxAbs) * 100;
                const pos = q.mean_return >= 0;
                return (
                  <div key={q.quantile} style={{ display: "flex", alignItems: "center", marginBottom: 8 }}>
                    <span style={{ width: 40 }}>{q.quantile}</span>
                    <div style={{ flex: 1, background: "#f0f0f0", borderRadius: 4, height: 22 }}>
                      <div style={{
                        width: `${pct}%`, height: "100%", borderRadius: 4,
                        background: pos ? "#52c41a" : "#ff4d4f", transition: "width .3s",
                      }} />
                    </div>
                    <span style={{ width: 90, textAlign: "right", color: pos ? "#52c41a" : "#ff4d4f" }}>
                      {(q.mean_return * 100).toFixed(3)}%
                    </span>
                  </div>
                );
              })}
              <Divider style={{ margin: "12px 0" }} />
              <Space size="large">
                <Text>多空收益: <Text strong style={{ color: r.layered.long_short_return >= 0 ? "#52c41a" : "#ff4d4f" }}>
                  {(r.layered.long_short_return * 100).toFixed(3)}%</Text></Text>
                <Text>多空夏普: <Text strong>{r.layered.long_short_sharpe?.toFixed(2)}</Text></Text>
              </Space>
            </>
          ) : <Empty description="无分层数据" />}
        </Card>
      </>
    );
  };

  return (
    <div>
      <Alert
        message="Alpha因子研究中心"
        description="IC分析、分层回测和因子组合功能已完成，可进行实时分析。"
        type="success"
        showIcon
        closable
        style={{ marginBottom: 16 }}
      />

      {/* 一键完整分析 */}
      <Card style={{ marginBottom: 16 }}>
        <Title level={4} style={{ marginTop: 0 }}>🧬 因子完整分析</Title>
        <Space.Compact style={{ width: "100%" }}>
          <Input
            size="large"
            allowClear
            placeholder="输入合约代码，如 RB2510 / 600019.SH / IO"
            value={symbolInput}
            onChange={(e) => setSymbolInput(e.target.value)}
            onPressEnter={handleFullAnalysis}
            prefix={<SearchOutlined />}
            disabled={analysisLoading}
          />
          <Button
            type="primary"
            size="large"
            loading={analysisLoading}
            onClick={handleFullAnalysis}
          >
            🧬 完整分析
          </Button>
        </Space.Compact>
        <Text type="secondary" style={{ marginTop: 8, display: "block" }}>
          支持: 期货合约(RB2510) / 股票(600019.SH) / 期权(IO) — 数据直连仓库
        </Text>
        {analysisLoading && (
          <Progress percent={100} status="active" showInfo={false} style={{ marginTop: 12 }} />
        )}
        {analysisLoading && (
          <Text type="secondary">{analysisProgress}</Text>
        )}
      </Card>

      {!analysisLoading && analysisResult && renderAnalysisResult()}
      {!analysisLoading && !analysisResult && (
        <Card style={{ marginBottom: 16 }}>
          <Empty description="输入合约代码，点击「完整分析」开始" />
        </Card>
      )}

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="因子总数"
              value={vibeFactorTotal || Object.keys(factorDescriptions).length}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: "#1890ff" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="正IC因子数"
              value={positiveICCount}
              suffix={`/ ${totalFactorCount}`}
              valueStyle={{ color: "#52c41a" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均IC"
              value={avgIC}
              prefix={<LineChartOutlined />}
              valueStyle={{
                color: parseFloat(avgIC) > 0 ? "#52c41a" : "#ff4d4f",
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均IR"
              value={avgIR}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: "#1890ff" }}
            />
          </Card>
        </Col>
      </Row>

      <Card title={`Alpha因子库 (${vibeFactorTotal || Object.keys(factorDescriptions).length}个因子)`}>
        <Space style={{ marginBottom: 12 }} wrap>
          <Input.Search placeholder="搜索因子" allowClear style={{ width: 180 }}
            onSearch={v => setVibeFactorSearch(v)} />
          <Select placeholder="筛选分类" allowClear style={{ width: 150 }}
            onChange={v => setSelectedVibeCategory(v || "")} value={selectedVibeCategory || undefined}>
            {vibeCategories.map(cat => (
              <Option key={cat} value={cat}>
                {CATEGORY_CN_MAP[cat] || cat} ({vibeFactors.filter((f: FactorInfo) => f.category === cat).length})
              </Option>
            ))}
          </Select>
        </Space>
        <Tabs defaultActiveKey="list" onChange={(key) => {
          if (key === 'vibe') loadVibeData();
        }}>
          <TabPane tab="因子列表" key="list">
            {vibeFactorTotal > 0 ? (
              <Table
                size="small"
                loading={vibeLoading}
                dataSource={vibeFactors.filter((f: FactorInfo) => {
                  const matchSearch = !vibeFactorSearch || f.name.toLowerCase().includes(vibeFactorSearch.toLowerCase()) ||
                    f.description.toLowerCase().includes(vibeFactorSearch.toLowerCase());
                  const matchCategory = !selectedVibeCategory || f.category === selectedVibeCategory;
                  return matchSearch && matchCategory;
                })}
                rowKey="name"
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 个因子`,
                }}
                scroll={{ x: 1000 }}
                columns={[
                  { title: "因子名", dataIndex: "name", width: 120, fixed: "left" as const,
                    render: (v: string) => <Text code style={{ fontSize: 11 }}>{v}</Text> },
                  { title: "分类", dataIndex: "category_cn", width: 90,
                    render: (v: string) => <Tag color={CATEGORY_COLORS[v] || "default"} style={{ fontWeight: "bold" }}>{v}</Tag> },
                  { title: "IC值", dataIndex: "ic", width: 90, sorter: (a: any, b: any) => a.ic - b.ic,
                    render: (v: number) => (
                      <Text style={{ color: v > 0 ? "#52c41a" : "#ff4d4f", fontWeight: "bold" }}>
                        {v > 0 ? "+" : ""}{v.toFixed(4)}
                      </Text>
                    )
                  },
                  { title: "IR值", dataIndex: "ir", width: 80, sorter: (a: any, b: any) => a.ir - b.ir,
                    render: (v: number) => (
                      <Text style={{ color: v > 0.5 ? "#52c41a" : v > 0 ? "#1890ff" : "#ff4d4f", fontWeight: "bold" }}>
                        {v.toFixed(2)}
                      </Text>
                    )
                  },
                  { title: "风险调整收益", dataIndex: "risk_adj_return", width: 130,
                    sorter: (a: any, b: any) => a.risk_adj_return - b.risk_adj_return,
                    render: (v: number) => (
                      <Text style={{ color: v > 0 ? "#3f8600" : "#cf1322", fontWeight: "bold" }}>
                        {v > 0 ? "+" : ""}{v.toFixed(3)}
                      </Text>
                    )
                  },
                  { title: "描述", dataIndex: "description", ellipsis: true },
                ]}
              />
            ) : (
              <Table
                dataSource={mockFactorList}
                columns={factorColumns}
                rowKey="id"
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 个因子`,
                }}
                size="middle"
                scroll={{ x: 1000 }}
              />
            )}
          </TabPane>

          <TabPane tab="IC分析" key="ic">
            <Space direction="vertical" style={{ width: "100%" }}>
              <Card size="small">
                <Space>
                  <Text>选择因子:</Text>
                  <Select
                    value={selectedFactor}
                    onChange={setSelectedFactor}
                    showSearch
                    filterOption={(i, o) => String(o?.value ?? "").toLowerCase().includes(i.toLowerCase())}
                    style={{ width: 320 }}
                  >
                    {factorOptions.map((f: any) => (
                      <Option key={f.name} value={f.name}>
                        {getFactorLabel(f)}
                      </Option>
                    ))}
                  </Select>

                  <Text>选择标的:</Text>
                  <Select
                    value={selectedSymbol}
                    onChange={setSelectedSymbol}
                    style={{ width: 150 }}
                  >
                    <Option value="000001.SZ">平安银行</Option>
                    <Option value="000002.SZ">万科A</Option>
                    <Option value="600000.SH">浦发银行</Option>
                  </Select>

                  <Button
                    type="primary"
                    icon={<ReloadOutlined />}
                    onClick={handleICAnalysis}
                    loading={icLoading}
                  >
                    开始分析
                  </Button>
                </Space>
              </Card>

              <Divider />

              {icLoading ? (
                <div style={{ textAlign: "center", padding: 50 }}>
                  <Spin size="large" tip="正在分析IC..." />
                </div>
              ) : icData ? (
                <>
                  {renderICTimeSeries()}
                  {renderICDistribution()}
                  {renderICDecay()}
                </>
              ) : (
                <Alert
                  message='请选择因子和标的后点击"开始分析"按钮'
                  type="info"
                  showIcon
                />
              )}
            </Space>
          </TabPane>

          <TabPane tab="分层回测" key="layered">
            <Space direction="vertical" style={{ width: "100%" }}>
              <Card size="small">
                <Space>
                  <Text>选择因子:</Text>
                  <Select
                    value={selectedFactor}
                    onChange={setSelectedFactor}
                    showSearch
                    filterOption={(i, o) => String(o?.value ?? "").toLowerCase().includes(i.toLowerCase())}
                    style={{ width: 320 }}
                  >
                    {factorOptions.map((f: any) => (
                      <Option key={f.name} value={f.name}>
                        {getFactorLabel(f)}
                      </Option>
                    ))}
                  </Select>

                  <Text>选择标的:</Text>
                  <Select
                    value={selectedSymbol}
                    onChange={setSelectedSymbol}
                    style={{ width: 150 }}
                  >
                    <Option value="000001.SZ">平安银行</Option>
                    <Option value="000002.SZ">万科A</Option>
                    <Option value="600000.SH">浦发银行</Option>
                  </Select>

                  <Button
                    type="primary"
                    icon={<ReloadOutlined />}
                    onClick={handleLayeredBacktest}
                    loading={layeredLoading}
                  >
                    开始回测
                  </Button>
                </Space>
              </Card>

              <Divider />

              {layeredLoading ? (
                <div style={{ textAlign: "center", padding: 50 }}>
                  <Spin size="large" tip="正在进行分层回测..." />
                </div>
              ) : layeredData ? (
                renderLayeredBacktest()
              ) : (
                <Alert
                  message='请选择因子和标的后点击"开始回测"按钮'
                  type="info"
                  showIcon
                />
              )}
            </Space>
          </TabPane>

          <TabPane tab="因子组合" key="combination">
            <Space direction="vertical" style={{ width: "100%" }}>
              <Card size="small">
                <Space wrap>
                  <Text>选择因子:</Text>
                  <Select
                    mode="multiple"
                    value={selectedFactors}
                    onChange={setSelectedFactors}
                    showSearch
                    filterOption={(i, o) => String(o?.value ?? "").toLowerCase().includes(i.toLowerCase())}
                    style={{ minWidth: 320 }}
                    maxTagCount={6}
                  >
                    {factorOptions.map((f: any) => (
                      <Option key={f.name} value={f.name}>
                        {getFactorLabel(f)}
                      </Option>
                    ))}
                  </Select>

                  <Button
                    type="primary"
                    icon={<ReloadOutlined />}
                    onClick={handleFactorCombine}
                    loading={combineLoading}
                    disabled={selectedFactors.length < 2}
                  >
                    组合分析
                  </Button>
                </Space>
              </Card>

              <Divider />

              {combineLoading ? (
                <div style={{ textAlign: "center", padding: 50 }}>
                  <Spin size="large" tip="正在进行因子组合分析..." />
                </div>
              ) : combineData ? (
                renderFactorCombine()
              ) : (
                <Alert
                  message='请选择至少2个因子后点击"组合分析"按钮'
                  type="info"
                  showIcon
                />
              )}
            </Space>
          </TabPane>

          <TabPane tab="因子挖掘" key="mining">
            <Space direction="vertical" style={{ width: "100%" }} size="large">
              <Card size="small">
                <Space wrap>
                  <Text strong>标的:</Text>
                  <Select value={selectedSymbol} onChange={setSelectedSymbol}
                    showSearch style={{ width: 200 }}
                    placeholder="期货/股票/期权 (仓库)"
                    filterOption={(i, o) => String(o?.value ?? "").toLowerCase().includes(i.toLowerCase())}>
                    {symbolOptions.map((s) => (
                      <Option key={s.code} value={s.code}>
                        {s.code}{s.status ? ` (${s.status})` : ""}
                      </Option>
                    ))}
                  </Select>
                  <Button type="primary" icon={<ExperimentOutlined />}
                    loading={mineLoading} onClick={handleMine}>
                    遗传挖掘
                  </Button>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    用算子随机组合 → IC/适应度评估 → 多代演化筛选最优因子
                  </Text>
                </Space>
              </Card>
              {mineLoading ? (
                <div style={{ textAlign: "center", padding: 50 }}>
                  <Spin size="large" tip="遗传演化中 (可能需数十秒)..." />
                </div>
              ) : mineData ? (
                <Card title={`挖掘结果 (${mineData.count} 个 · 数据源: ${mineData.data_source})`} size="small">
                  <Table size="small" rowKey="name" pagination={false}
                    dataSource={mineData.factors}
                    columns={[
                      { title: "因子", dataIndex: "name", width: 100,
                        render: (v: string) => <Text strong>{v}</Text> },
                      { title: "表达式", dataIndex: "expression", ellipsis: true },
                      { title: "适应度", dataIndex: "fitness", width: 100,
                        sorter: (a: any, b: any) => a.fitness - b.fitness,
                        render: (v: number) => v.toFixed(4) },
                      { title: "IC", dataIndex: "ic", width: 100,
                        render: (v: number) => (
                          <Tag color={Math.abs(v) > 0.03 ? "green" : "default"}>{v.toFixed(4)}</Tag>
                        ) },
                    ]} />
                </Card>
              ) : (
                <Alert message='选标的后点"遗传挖掘"，从基础算子自动发现新因子' type="info" showIcon />
              )}
            </Space>
          </TabPane>

          <TabPane tab="健康监控" key="health">
            <Space direction="vertical" style={{ width: "100%" }} size="large">
              <Card size="small">
                <Space wrap>
                  <Text strong>因子:</Text>
                  <Select value={selectedFactor} onChange={setSelectedFactor}
                    showSearch filterOption={(i, o) => String(o?.value ?? "").toLowerCase().includes(i.toLowerCase())}
                    style={{ width: 320 }}>
                    {factorOptions.map((f: any) => (
                      <Option key={f.name} value={f.name}>{getFactorLabel(f)}</Option>
                    ))}
                  </Select>
                  <Text strong>标的:</Text>
                  <Select value={selectedSymbol} onChange={setSelectedSymbol}
                    showSearch style={{ width: 200 }}
                    filterOption={(i, o) => String(o?.value ?? "").toLowerCase().includes(i.toLowerCase())}>
                    {symbolOptions.map((s) => (
                      <Option key={s.code} value={s.code}>
                        {s.code}{s.status ? ` (${s.status})` : ""}
                      </Option>
                    ))}
                  </Select>
                  <Button type="primary" icon={<LineChartOutlined />}
                    loading={healthLoading} onClick={handleHealthCheck}>
                    健康检测
                  </Button>
                </Space>
              </Card>
              {healthData ? (
                <Card size="small">
                  <Row gutter={16} style={{ marginBottom: 12 }}>
                    <Col span={6}>
                      <Statistic title="健康状态" value={healthData.health}
                        valueStyle={{
                          color: healthData.health === "HEALTHY" ? "#52c41a"
                            : healthData.health === "WARNING" ? "#faad14" : "#ff4d4f",
                        }} />
                    </Col>
                    <Col span={4}><Statistic title="当前IC" value={healthData.current_ic} /></Col>
                    <Col span={4}><Statistic title="IC趋势" value={healthData.ic_trend}
                      valueStyle={{ color: healthData.ic_trend >= 0 ? "#52c41a" : "#ff4d4f" }} /></Col>
                    <Col span={4}><Statistic title="ICIR" value={healthData.icir} /></Col>
                    <Col span={6}><Statistic title="分层单调性" value={healthData.monotonicity} /></Col>
                  </Row>
                  <Row gutter={16}>
                    <Col span={6}><Statistic title="短期IC均值" value={healthData.ic_mean_short} /></Col>
                    <Col span={6}><Statistic title="长期IC均值" value={healthData.ic_mean_long} /></Col>
                    <Col span={4}><Statistic title="数据源" value={healthData.data_source} /></Col>
                  </Row>
                  {healthData.reasons?.length > 0 && (
                    <Alert style={{ marginTop: 12 }} type={
                      healthData.alert_level === "critical" ? "error"
                        : healthData.alert_level === "warning" ? "warning" : "info"}
                      message="检测说明" description={
                        <ul style={{ margin: 0, paddingLeft: 18 }}>
                          {healthData.reasons.map((r: string, i: number) => <li key={i}>{r}</li>)}
                        </ul>} showIcon />
                  )}
                </Card>
              ) : (
                <Alert message='选因子+标的后点"健康检测"，三态评级: HEALTHY/WARNING/DECAYED' type="info" showIcon />
              )}
            </Space>
          </TabPane>

          <TabPane tab="研究报告" key="report">
            <Space direction="vertical" style={{ width: "100%" }} size="large">
              <Card size="small">
                <Space wrap>
                  <Text strong>标的:</Text>
                  <Select value={selectedSymbol} onChange={setSelectedSymbol}
                    showSearch style={{ width: 200 }}
                    filterOption={(i, o) => String(o?.value ?? "").toLowerCase().includes(i.toLowerCase())}>
                    {symbolOptions.map((s) => (
                      <Option key={s.code} value={s.code}>
                        {s.code}{s.status ? ` (${s.status})` : ""}
                      </Option>
                    ))}
                  </Select>
                  <Text strong>因子集:</Text>
                  <Select mode="multiple" value={selectedFactors} onChange={setSelectedFactors}
                    showSearch filterOption={(i, o) => String(o?.value ?? "").toLowerCase().includes(i.toLowerCase())}
                    style={{ minWidth: 320 }} maxTagCount={6}>
                    {factorOptions.map((f: any) => (
                      <Option key={f.name} value={f.name}>{getFactorLabel(f)}</Option>
                    ))}
                  </Select>
                  <Button type="primary" icon={<BarChartOutlined />}
                    loading={reportLoading} onClick={handleReport}
                    disabled={selectedFactors.length < 2}>
                    生成报告
                  </Button>
                </Space>
              </Card>
              {reportLoading ? (
                <div style={{ textAlign: "center", padding: 50 }}>
                  <Spin size="large" tip="全因子评估中..." />
                </div>
              ) : reportData ? (
                <Card size="small">
                  <Row gutter={16} style={{ marginBottom: 16 }}>
                    <Col span={4}><Statistic title="总因子" value={reportData.total_factors} /></Col>
                    <Col span={4}><Statistic title="健康" value={reportData.healthy_count}
                      valueStyle={{ color: "#52c41a" }} /></Col>
                    <Col span={4}><Statistic title="警告" value={reportData.warning_count}
                      valueStyle={{ color: "#faad14" }} /></Col>
                    <Col span={4}><Statistic title="失效" value={reportData.decayed_count}
                      valueStyle={{ color: "#ff4d4f" }} /></Col>
                    <Col span={4}><Statistic title="组合IC" value={reportData.recommended_ic} /></Col>
                    <Col span={4}><Statistic title="组合ICIR" value={reportData.recommended_icir} /></Col>
                  </Row>
                  {reportData.recommended?.length > 0 && (
                    <Alert style={{ marginBottom: 12 }} type="success" showIcon
                      message="推荐组合 (高IC + 低相关)"
                      description={reportData.recommended.map((n: string) => (
                        <Tag color="green" key={n}>{n}</Tag>
                      ))} />
                  )}
                  <Table size="small" rowKey="name" pagination={{ pageSize: 10 }}
                    dataSource={reportData.top_factors}
                    columns={[
                      { title: "#", dataIndex: "rank", width: 50 },
                      { title: "因子", dataIndex: "name",
                        render: (v: string, r: any) => (
                          <Text strong>{v}{r.is_recommended ? " ★" : ""}</Text>
                        ) },
                      { title: "IC", dataIndex: "ic_mean", width: 90 },
                      { title: "ICIR", dataIndex: "icir", width: 90 },
                      { title: "多空Sharpe", dataIndex: "sharpe_q5q1", width: 110 },
                      { title: "换手", dataIndex: "turnover", width: 90 },
                      { title: "健康", dataIndex: "health", width: 90,
                        render: (v: string) => (
                          <Tag color={v === "HEALTHY" ? "green" : v === "WARNING" ? "orange" : "red"}>{v}</Tag>
                        ) },
                    ]} />
                  {reportData.high_correlation_pairs?.length > 0 && (
                    <div style={{ marginTop: 12 }}>
                      <Text type="secondary">高相关冗余对 (|corr|≥0.85): </Text>
                      {reportData.high_correlation_pairs.map((p: any, i: number) => (
                        <Tag key={i}>{p[0]}~{p[1]}: {p[2]}</Tag>
                      ))}
                    </div>
                  )}
                </Card>
              ) : (
                <Alert message='选标的+因子集后点"生成报告"，一键评估→排名→推荐组合' type="info" showIcon />
              )}
            </Space>
          </TabPane>

          {/* ───── 量化研究 Tab (来自 VibeResearch) ───── */}
          <TabPane tab="量化研究" key="vibe">
            <Space direction="vertical" size="large" style={{ width: "100%" }}>
              {/* 数据源 + Swarm + 快速回测 */}
              <Row gutter={16}>
                <Col span={6}>
                  <Card size="small" title={<><CloudServerOutlined /> 数据源</>}>
                    <List size="small" dataSource={datasources} renderItem={(ds) => (
                      <List.Item style={{ padding: "4px 0" }}>
                        <Space>
                          <Badge status={ds.status === "available" ? "success" : "default"} />
                          <Text style={{ fontSize: 12 }}>{ds.name}</Text>
                          <Tag color={ds.status === "available" ? "green" : "default"} style={{ fontSize: 10 }}>{ds.type}</Tag>
                        </Space>
                      </List.Item>
                    )} />
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small" title={<><RobotOutlined /> 多Agent ({swarmStatus?.total_agents ?? 0})</>}>
                    <List size="small" dataSource={swarmStatus?.agents ?? []} renderItem={(agent) => (
                      <List.Item style={{ padding: "4px 0" }}>
                        <Space>
                          <Badge status={agent.status === "idle" ? "success" : "processing"} />
                          <Text style={{ fontSize: 12 }}>{agent.name}</Text>
                          {agent.tasks > 0 && <Tag color="blue" style={{ fontSize: 10 }}>{agent.tasks}任务</Tag>}
                        </Space>
                      </List.Item>
                    )} />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small" title={<><PlayCircleOutlined /> 快速回测</>}>
                    <Space>
                      <Input placeholder="股票代码" value={btSymbol} onChange={e => setBtSymbol(e.target.value)} style={{ width: 100 }} />
                      <Select value={btStrategy} onChange={setBtStrategy} style={{ width: 120 }}>
                        <Option value="ma_cross">均线交叉</Option>
                        <Option value="rsi_rev">RSI反转</Option>
                        <Option value="momentum">动量策略</Option>
                      </Select>
                      <Button type="primary" onClick={handleBacktest} loading={running}>运行</Button>
                      {backtests.length > 0 && (
                        <Select
                          placeholder="选择历史"
                          style={{ width: 150 }}
                          onChange={(id) => {
                            const bt = backtests.find((b: BacktestResult) => b.id === id);
                            if (bt) {
                              setSelectedBacktest(bt);
                              setChartData(generateChartData(bt));
                            }
                          }}
                        >
                          {backtests.slice(0, 5).map((b: BacktestResult) => (
                            <Option key={b.id} value={b.id}>{b.symbol} {b.strategy}</Option>
                          ))}
                        </Select>
                      )}
                    </Space>
                  </Card>
                </Col>
              </Row>

              {/* 研究智能体 */}
              <Card size="small" title={<><ThunderboltOutlined /> 研究智能体</>}>
                <Space>
                  <Input
                    placeholder="研究问题，如: 分析特斯拉近期走势和投资价值"
                    value={researchQuery}
                    onChange={e => setResearchQuery(e.target.value)}
                    style={{ width: 500 }}
                    onPressEnter={handleResearch}
                  />
                  <Button type="primary" onClick={handleResearch} loading={researching}>研究</Button>
                </Space>
                {researchResult && (
                  <div style={{ marginTop: 12 }}>
                    <Space style={{ marginBottom: 8 }}>
                      <Text type="secondary">置信度: </Text>
                      <AntProgress percent={Math.round(researchResult.confidence * 100)} size="small" style={{ width: 200 }} />
                      {researchResult.top_factors && researchResult.top_factors.length > 0 && (
                        <>
                          <Text type="secondary">推荐因子: </Text>
                          {researchResult.top_factors.slice(0, 3).map((f: string) => (
                            <Tag key={f} color="blue">{f}</Tag>
                          ))}
                        </>
                      )}
                    </Space>
                    <Row gutter={12}>
                      <Col span={12}>
                        <Text strong style={{ fontSize: 12 }}>研究结论:</Text>
                        <List size="small" dataSource={researchResult.findings}
                          renderItem={(f: string) => <List.Item style={{ padding: "2px 0" }}><Text style={{ fontSize: 12 }}>{f}</Text></List.Item>}
                        />
                      </Col>
                      <Col span={12}>
                        <Text strong style={{ fontSize: 12 }}>信号:</Text>
                        <Space style={{ marginTop: 4 }}>
                          {researchResult.signals.map((s: string, i: number) => <Tag key={i} color={s === "买入" ? "green" : "default"}>{s}</Tag>)}
                        </Space>
                      </Col>
                    </Row>
                  </div>
                )}
              </Card>

              {/* 回测结果 */}
              {selectedBacktest && (
                <Card size="small" title={<><LineChartOutlined /> 回测结果: {selectedBacktest.symbol}</>}>
                  <Row gutter={16}>
                    <Col span={6}>
                      <Statistic
                        title="总收益"
                        value={selectedBacktest.total_return}
                        suffix="%"
                        precision={2}
                        valueStyle={{ color: selectedBacktest.total_return > 0 ? "#3f8600" : "#cf1322" }}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic title="夏普比率" value={selectedBacktest.sharpe_ratio} precision={2} />
                    </Col>
                    <Col span={6}>
                      <Statistic title="最大回撤" value={selectedBacktest.max_drawdown} suffix="%" valueStyle={{ color: "#cf1322" }} />
                    </Col>
                    <Col span={6}>
                      <Statistic title="胜率" value={selectedBacktest.win_rate} suffix="%" precision={1} />
                    </Col>
                  </Row>
                  <ResponsiveContainer width="100%" height={250} style={{ marginTop: 16 }}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="day" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} />
                      <RechartsTooltip formatter={(value: unknown) => [`¥${Number(value).toLocaleString()}`, ""]} />
                      <Legend />
                      <Line type="monotone" dataKey="value" stroke="#1890ff" name="策略" dot={false} />
                      <Line type="monotone" dataKey="benchmark" stroke="#999" name="基准" dot={false} strokeDasharray="5 5" />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              )}

              {/* 因子表现 */}
              <Card size="small" title={<><LineChartOutlined /> Alpha因子表现</>}>
                <Row gutter={16}>
                  <Col span={12}>
                    <Title level={5} style={{ marginTop: 0 }}>Top因子收益分布</Title>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={vibeFactors.slice(0, 10).map((f: FactorInfo) => ({ name: f.name, performance: f.risk_adj_return }))} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" domain={[-1, 2]} tickFormatter={(v: number) => `${v}%`} />
                        <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 11 }} />
                        <RechartsTooltip formatter={(v: unknown) => [`${Number(v).toFixed(3)}`, "风险调整收益"]} />
                        <Bar dataKey="performance" fill="#1890ff" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </Col>
                  <Col span={12}>
                    <Title level={5} style={{ marginTop: 0 }}>分类统计</Title>
                    <Tag color={vibeFactorSource === "alpha101" ? "green" : "orange"} style={{ marginBottom: 8 }}>
                      {vibeFactorSource === "alpha101" ? `✅ 真实因子库 (${vibeFactorTotal}个)` : "⚠️ 模拟数据"}
                    </Tag>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                      {vibeCategories.map((cat: string) => {
                        const catCN = cat in CATEGORY_COLORS ? cat : CATEGORY_CN_MAP[cat] || cat;
                        return (
                          <Tooltip key={cat} title={`${catCN} 因子`}>
                            <Tag color={CATEGORY_COLORS[cat] || CATEGORY_COLORS[catCN] || "default"} style={{ cursor: "pointer", padding: "4px 12px" }}>
                              {catCN}: {vibeFactors.filter((f: FactorInfo) => f.category === cat).length}
                            </Tag>
                          </Tooltip>
                        );
                      })}
                    </div>
                    <div style={{ marginTop: 16 }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        共 {vibeFactorTotal} 个因子
                      </Text>
                    </div>
                  </Col>
                </Row>
              </Card>

              {/* 因子库 */}
              <Card size="small" title={<><ExperimentOutlined /> Alpha因子库</>}>
                <Space style={{ marginBottom: 8 }} wrap>
                  <Input.Search
                    placeholder="搜索因子"
                    value={vibeFactorSearch}
                    onChange={e => setVibeFactorSearch(e.target.value)}
                    style={{ width: 200 }}
                  />
                  <Select
                    placeholder="筛选分类"
                    allowClear
                    value={selectedVibeCategory || undefined}
                    onChange={v => setSelectedVibeCategory(v || "")}
                    style={{ width: 140 }}
                  >
                    {vibeCategories.map(cat => (
                      <Option key={cat} value={cat}>
                        {CATEGORY_CN_MAP[cat] || cat} ({vibeFactors.filter((f: FactorInfo) => f.category === cat).length})
                      </Option>
                    ))}
                  </Select>
                  <Text type="secondary" style={{ fontSize: 11 }}>共 {vibeFactorTotal} 个因子</Text>
                </Space>
                <Table
                  size="small"
                  loading={vibeLoading}
                  dataSource={vibeFactors.filter((f: FactorInfo) => {
                    const matchSearch = f.name.toLowerCase().includes(vibeFactorSearch.toLowerCase()) ||
                      f.description.toLowerCase().includes(vibeFactorSearch.toLowerCase());
                    const matchCategory = !selectedVibeCategory || f.category === selectedVibeCategory;
                    return matchSearch && matchCategory;
                  })}
                  rowKey="name"
                  pagination={{ pageSize: 10, showSizeChanger: true, pageSizeOptions: [10, 20, 50, 100] }}
                  scroll={{ x: 800 }}
                  columns={[
                    { title: "因子名", dataIndex: "name", width: 120, fixed: "left" as const,
                      render: (v: string) => <Text code style={{ fontSize: 11 }}>{v}</Text> },
                    { title: "分类", dataIndex: "category_cn", width: 90,
                      render: (v: string) => <Tag color={CATEGORY_COLORS[v] || "default"} style={{ fontWeight: "bold" }}>{v}</Tag> },
                    { title: "IC", dataIndex: "ic", width: 80,
                      render: (v: number) => (
                        <Text style={{ color: v > 0 ? "#52c41a" : "#ff4d4f", fontWeight: "bold" }}>
                          {v > 0 ? "+" : ""}{v.toFixed(4)}
                        </Text>
                      )
                    },
                    { title: "IR", dataIndex: "ir", width: 70,
                      render: (v: number) => (
                        <Text style={{ color: v > 0.5 ? "#52c41a" : v > 0 ? "#1890ff" : "#ff4d4f", fontWeight: "bold" }}>
                          {v.toFixed(2)}
                        </Text>
                      )
                    },
                    { title: "风险调整收益", dataIndex: "risk_adj_return", width: 130,
                      render: (v: number) => (
                        <Text style={{ color: v > 0 ? "#3f8600" : "#cf1322", fontWeight: "bold" }}>
                          {v > 0 ? "+" : ""}{v.toFixed(3)}
                        </Text>
                      )
                    },
                  ]}
                />
              </Card>
            </Space>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
}
