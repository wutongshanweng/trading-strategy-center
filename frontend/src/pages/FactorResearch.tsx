import { Card, Table, Tabs, Tag, Space, Typography, Alert, Statistic, Row, Col } from "antd";
import { ExperimentOutlined, LineChartOutlined, BarChartOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;
const { TabPane } = Tabs;

// 101个Alpha因子Mock数据
const mockFactors = Array.from({ length: 101 }, (_, i) => ({
  id: `alpha${String(i + 1).padStart(3, '0')}`,
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
  const avgIC = (mockFactors.reduce((sum, f) => sum + f.ic, 0) / mockFactors.length).toFixed(4);
  const avgIR = (mockFactors.reduce((sum, f) => sum + f.ir, 0) / mockFactors.length).toFixed(2);
  const positiveICCount = mockFactors.filter(f => f.ic > 0).length;

  return (
    <div>
      <Alert
        message="Alpha因子研究中心"
        description="本页面展示101个WorldQuant Alpha因子。点击因子ID可查看详细公式和计算逻辑。IC/IR数据为示例数据，实际使用时需连接后端API进行因子评估。"
        type="info"
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
              valueStyle={{ color: parseFloat(avgIC) > 0 ? "#52c41a" : "#ff4d4f" }}
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
            <Space direction="vertical" style={{ width: "100%", padding: 24 }}>
              <Title level={4}>信息系数（IC）分析</Title>
              <Text type="secondary">
                IC（Information Coefficient）衡量因子值与未来收益的相关性。
                <br />
                - IC &gt; 0.03: 优秀因子
                <br />
                - IC = 0.01-0.03: 良好因子
                <br />
                - IC &lt; 0.01: 弱因子
              </Text>
              <Alert
                message="功能开发中"
                description="IC时间序列图、IC分布直方图、IC衰减分析等功能正在开发中。"
                type="warning"
              />
            </Space>
          </TabPane>

          <TabPane tab="分层回测" key="layered">
            <Space direction="vertical" style={{ width: "100%", padding: 24 }}>
              <Title level={4}>因子分层回测</Title>
              <Text type="secondary">
                将股票按因子值分成5层，观察每层的平均收益，验证因子的单调性。
              </Text>
              <Alert
                message="功能开发中"
                description="5分层收益对比图、多空组合分析、换手率统计等功能正在开发中。"
                type="warning"
              />
            </Space>
          </TabPane>

          <TabPane tab="因子组合" key="combination">
            <Space direction="vertical" style={{ width: "100%", padding: 24 }}>
              <Title level={4}>因子组合优化</Title>
              <Text type="secondary">
                通过IC加权、等权或优化算法，将多个因子组合成一个复合因子。
              </Text>
              <Alert
                message="功能开发中"
                description="相关性矩阵、IC加权组合、优化权重计算等功能正在开发中。"
                type="warning"
              />
            </Space>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
}
