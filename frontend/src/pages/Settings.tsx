import { useState } from "react";
import {
  Card, Form, Input, InputNumber, Select, Button, Switch, Divider,
  Typography, message, Tabs, Tag, Row, Col, Space, Tooltip,
} from "antd";
import {
  SettingOutlined, KeyOutlined, BellOutlined, ApiOutlined,
  SafetyOutlined, SaveOutlined, ReloadOutlined,
} from "@ant-design/icons";

const { Text, Title } = Typography;

export default function Settings() {
  const [activeTab, setActiveTab] = useState("general");
  const [form] = Form.useForm();
  const [apiForm] = Form.useForm();
  const [alertForm] = Form.useForm();

  const handleSave = () => {
    message.success("设置已保存");
  };

  return (
    <div>
      <div className="page-header">
        <h2>
          <SettingOutlined style={{ marginRight: 8 }} />
          系统设置
        </h2>
        <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
          保存设置
        </Button>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: "general",
            label: <span><SettingOutlined /> 基本设置</span>,
            children: (
              <Card bordered={false}>
                <Form form={form} layout="vertical" style={{ maxWidth: 600 }}>
                  <Form.Item label="系统名称" name="systemName" initialValue="Trading Strategy Center">
                    <Input />
                  </Form.Item>
                  <Form.Item label="默认资金" name="defaultCapital" initialValue={1000000}>
                    <InputNumber style={{ width: "100%" }} min={100000} step={100000} prefix="¥" />
                  </Form.Item>
                  <Form.Item label="最大持仓数" name="maxPositions" initialValue={10}>
                    <InputNumber min={1} max={100} />
                  </Form.Item>
                  <Form.Item label="默认杠杆" name="defaultLeverage" initialValue={1}>
                    <InputNumber min={1} max={10} />
                  </Form.Item>
                  <Form.Item label="数据语言" name="locale" initialValue="zh-CN">
                    <Select options={[{ label: "中文", value: "zh-CN" }, { label: "English", value: "en-US" }]} />
                  </Form.Item>
                  <Divider />
                  <Form.Item label="启用自动交易" name="autoTrading" valuePropName="checked" initialValue={false}>
                    <Switch />
                  </Form.Item>
                </Form>
              </Card>
            ),
          },
          {
            key: "api",
            label: <span><KeyOutlined /> API密钥</span>,
            children: (
              <Card bordered={false}>
                <Form form={apiForm} layout="vertical" style={{ maxWidth: 600 }}>
                  <Form.Item label="DeepSeek API Key" name="deepseekKey">
                    <Input.Password placeholder="sk-..." />
                  </Form.Item>
                  <Form.Item label="OpenAI API Key" name="openaiKey">
                    <Input.Password placeholder="sk-..." />
                  </Form.Item>
                  <Form.Item label="Claude API Key" name="claudeKey">
                    <Input.Password placeholder="sk-ant-..." />
                  </Form.Item>
                  <Form.Item label="默认LLM提供商" name="llmProvider" initialValue="deepseek">
                    <Select options={[
                      { label: "DeepSeek", value: "deepseek" },
                      { label: "OpenAI", value: "openai" },
                      { label: "Claude (Anthropic)", value: "claude" },
                    ]} />
                  </Form.Item>
                  <Divider />
                  <Form.Item label="数据源 Token" name="dataSourceToken">
                    <Input.Password placeholder="Data provider token" />
                  </Form.Item>
                </Form>
              </Card>
            ),
          },
          {
            key: "risk",
            label: <span><SafetyOutlined /> 风控设置</span>,
            children: (
              <Card bordered={false}>
                <Form layout="vertical" style={{ maxWidth: 600 }}>
                  <Form.Item label="单笔最大亏损" name="maxLossPerTrade" initialValue={5000}>
                    <InputNumber style={{ width: "100%" }} min={100} step={1000} prefix="¥" />
                  </Form.Item>
                  <Form.Item label="日最大亏损" name="maxDailyLoss" initialValue={50000}>
                    <InputNumber style={{ width: "100%" }} min={1000} step={5000} prefix="¥" />
                  </Form.Item>
                  <Form.Item label="最大回撤限制" name="maxDrawdownLimit" initialValue={20}>
                    <InputNumber min={1} max={100} suffix="%" />
                  </Form.Item>
                  <Form.Item label="VaR置信水平" name="varConfidence" initialValue={0.95}>
                    <Select options={[
                      { label: "95%", value: 0.95 },
                      { label: "97.5%", value: 0.975 },
                      { label: "99%", value: 0.99 },
                    ]} />
                  </Form.Item>
                </Form>
              </Card>
            ),
          },
          {
            key: "alerts",
            label: <span><BellOutlined /> 通知告警</span>,
            children: (
              <Card bordered={false}>
                <Form form={alertForm} layout="vertical" style={{ maxWidth: 600 }}>
                  <Form.Item label="飞书 Webhook URL" name="feishuWebhook">
                    <Input placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..." />
                  </Form.Item>
                  <Form.Item label="邮箱通知" name="emailNotify">
                    <Input placeholder="admin@example.com" />
                  </Form.Item>
                  <Divider />
                  <Form.Item label="风控告警" name="alertRisk" valuePropName="checked" initialValue={true}>
                    <Switch />
                  </Form.Item>
                  <Form.Item label="成交通知" name="alertFill" valuePropName="checked" initialValue={true}>
                    <Switch />
                  </Form.Item>
                  <Form.Item label="异常检测告警" name="alertAnomaly" valuePropName="checked" initialValue={true}>
                    <Switch />
                  </Form.Item>
                </Form>
              </Card>
            ),
          },
          {
            key: "system",
            label: <span><ApiOutlined /> 系统信息</span>,
            children: (
              <Card bordered={false}>
                <Row gutter={[24, 16]}>
                  <Col span={12}>
                    <Text type="secondary">版本</Text>
                    <div><Text strong>v0.1.0</Text></div>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary">Python</Text>
                    <div><Text strong>3.11+</Text></div>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary">数据库</Text>
                    <div><Text strong>PostgreSQL 15</Text></div>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary">缓存</Text>
                    <div><Text strong>Redis 7</Text></div>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary">队列</Text>
                    <div><Text strong>Celery + RabbitMQ</Text></div>
                  </Col>
                  <Col span={12}>
                    <Text type="secondary">前端</Text>
                    <div><Text strong>React 18 + Vite 5</Text></div>
                  </Col>
                  <Col span={24}>
                    <Divider />
                    <Space>
                      <Button icon={<ReloadOutlined />}>检查更新</Button>
                      <Button>查看日志</Button>
                    </Space>
                  </Col>
                </Row>
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
}
