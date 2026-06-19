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
} from "antd";
import {
  ExperimentOutlined,
  LineChartOutlined,
  BarChartOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { factorApi } from "../services/factorApi";

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

// 101个Alpha因子Mock数据
const mockFactors = Array.from({ length: 101 }, (_, i) => ({
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

  const avgIC = (
    mockFactors.reduce((sum, f) => sum + f.ic, 0) / mockFactors.length
  ).toFixed(4);
  const avgIR = (
    mockFactors.reduce((sum, f) => sum + f.ir, 0) / mockFactors.length
  ).toFixed(2);
  const positiveICCount = mockFactors.filter((f) => f.ic > 0).length;

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

  return (
    <div>
      <Alert
        message="Alpha因子研究中心"
        description="本页面展示101个WorldQuant Alpha因子。IC分析、分层回测和因子组合功能已完成，可进行实时分析。"
        type="success"
        showIcon
        closable
        style={{ marginBottom: 16 }}
      />

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="因子总数"
              value={101}
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
              suffix={`/ ${mockFactors.length}`}
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

      <Card title="Alpha因子库 (101个因子)">
        <Tabs defaultActiveKey="list">
          <TabPane tab="因子列表" key="list">
            <Table
              dataSource={mockFactors}
              columns={columns}
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
          </TabPane>

          <TabPane tab="IC分析" key="ic">
            <Space direction="vertical" style={{ width: "100%" }}>
              <Card size="small">
                <Space>
                  <Text>选择因子:</Text>
                  <Select
                    value={selectedFactor}
                    onChange={setSelectedFactor}
                    style={{ width: 150 }}
                  >
                    {mockFactors.slice(0, 20).map((f) => (
                      <Option key={f.id} value={f.id}>
                        {f.name}
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
                    style={{ width: 150 }}
                  >
                    {mockFactors.slice(0, 20).map((f) => (
                      <Option key={f.id} value={f.id}>
                        {f.name}
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
                <Space>
                  <Text>选择因子:</Text>
                  <Select
                    mode="multiple"
                    value={selectedFactors}
                    onChange={setSelectedFactors}
                    style={{ width: 300 }}
                    maxTagCount={3}
                  >
                    {mockFactors.slice(0, 20).map((f) => (
                      <Option key={f.id} value={f.id}>
                        {f.name}
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
                  <Select value={selectedSymbol} onChange={setSelectedSymbol} style={{ width: 160 }}>
                    <Option value="600019.SH">600019.SH 宝钢</Option>
                    <Option value="601899.SH">601899.SH 紫金</Option>
                    <Option value="600585.SH">600585.SH 海螺</Option>
                    <Option value="000001.SZ">000001.SZ 平安</Option>
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
                    showSearch style={{ width: 150 }}>
                    {mockFactors.slice(0, 30).map((f) => (
                      <Option key={f.id} value={f.id}>{f.name}</Option>
                    ))}
                  </Select>
                  <Text strong>标的:</Text>
                  <Select value={selectedSymbol} onChange={setSelectedSymbol} style={{ width: 160 }}>
                    <Option value="600019.SH">600019.SH</Option>
                    <Option value="601899.SH">601899.SH</Option>
                    <Option value="000001.SZ">000001.SZ</Option>
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
                  <Select value={selectedSymbol} onChange={setSelectedSymbol} style={{ width: 160 }}>
                    <Option value="600019.SH">600019.SH</Option>
                    <Option value="601899.SH">601899.SH</Option>
                    <Option value="000001.SZ">000001.SZ</Option>
                  </Select>
                  <Text strong>因子集:</Text>
                  <Select mode="multiple" value={selectedFactors} onChange={setSelectedFactors}
                    style={{ minWidth: 280 }} maxTagCount={6}>
                    {mockFactors.slice(0, 30).map((f) => (
                      <Option key={f.id} value={f.id}>{f.name}</Option>
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
        </Tabs>
      </Card>
    </div>
  );
}
