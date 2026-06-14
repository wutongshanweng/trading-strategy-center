import { useEffect, useState } from "react";
import {
  Row, Col, Card, Table, Tag, Button, Select, Typography, Statistic,
  Modal, Form, Input, message, Spin, Badge, Tooltip, Divider, Progress,
} from "antd";
import {
  RobotOutlined, PlayCircleOutlined, CheckCircleOutlined,
  CloseCircleOutlined, ThunderboltOutlined,
} from "@ant-design/icons";
import { listMLModels, trainModel } from "../api/client";
import type { MLModel } from "../api/client";
import { useMLStore } from "../store/useAppStore";

const { Text, Title } = Typography;

const MOCK_MODELS: MLModel[] = [
  { id: "m1", name: "LSTM 价格预测", type: "lstm", status: "ready", accuracy: 0.876, last_trained: "2024-06-10 14:30" },
  { id: "m2", name: "XGBoost 方向分类", type: "xgboost", status: "ready", accuracy: 0.812, last_trained: "2024-06-09 10:00" },
  { id: "m3", name: "Transformer 时序模型", type: "transformer", status: "training", accuracy: null, last_trained: null },
  { id: "m4", name: "HMM 市场状态", type: "hmm", status: "idle", accuracy: 0.721, last_trained: "2024-05-28 16:00" },
  { id: "m5", name: "随机森林因子选择", type: "random_forest", status: "ready", accuracy: 0.795, last_trained: "2024-06-08 09:15" },
  { id: "m6", name: "CNN 图形识别", type: "cnn", status: "failed", accuracy: null, last_trained: "2024-06-01 12:00" },
];

const statusConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  ready: { label: "就绪", color: "green", icon: <CheckCircleOutlined /> },
  training: { label: "训练中", color: "processing", icon: <ThunderboltOutlined /> },
  idle: { label: "空闲", color: "default", icon: <RobotOutlined /> },
  failed: { label: "失败", color: "error", icon: <CloseCircleOutlined /> },
};

const columns = [
  { title: "名称", dataIndex: "name", key: "name", render: (v: string) => <Text strong>{v}</Text> },
  { title: "类型", dataIndex: "type", key: "type", render: (v: string) => <Tag>{v.toUpperCase()}</Tag> },
  {
    title: "状态", dataIndex: "status", key: "status",
    render: (v: string) => {
      const c = statusConfig[v] ?? { label: v, color: "default", icon: null };
      return <Badge status={c.color as any} text={c.label} />;
    },
  },
  {
    title: "准确率", dataIndex: "accuracy", key: "accuracy",
    render: (v: number | null) =>
      v != null ? (
        <span style={{ color: v >= 0.8 ? "#00d4aa" : v >= 0.7 ? "#ffd666" : "#ff4d6a" }}>
          {(v * 100).toFixed(1)}%
        </span>
      ) : <Text type="secondary">-</Text>,
  },
  { title: "最后训练", dataIndex: "last_trained", key: "last_trained", render: (v: string | null) => v ?? "-" },
  {
    title: "操作", key: "actions",
    render: (_: any, record: MLModel) => (
      <Button
        type="link"
        icon={<PlayCircleOutlined />}
        disabled={record.status === "training"}
      >
        {record.status === "training" ? "训练中..." : "重新训练"}
      </Button>
    ),
  },
];

export default function ML() {
  const { models, setModels, status, setStatus } = useMLStore();
  const [trainOpen, setTrainOpen] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    setStatus("loading");
    listMLModels()
      .then((res) => setModels(res.data))
      .catch(() => setModels(MOCK_MODELS))
      .finally(() => setStatus("success"));
  }, []);

  const handleTrain = async () => {
    try {
      const values = await form.validateFields();
      message.success(`模型 ${values.model_type.toUpperCase()} 训练任务已提交`);
      setTrainOpen(false);
      form.resetFields();
    } catch { /* validation */ }
  };

  const readyCount = models.filter((m) => m.status === "ready").length;
  const avgAccuracy =
    models.filter((m) => m.accuracy != null).reduce((s, m) => s + (m.accuracy ?? 0), 0) /
    Math.max(1, models.filter((m) => m.accuracy != null).length);

  return (
    <Spin spinning={status === "loading"}>
      <div className="page-header">
        <h2>机器学习</h2>
        <Button type="primary" icon={<PlayCircleOutlined />} onClick={() => setTrainOpen(true)}>
          训练新模型
        </Button>
      </div>

      {/* Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <Statistic title="模型总数" value={models.length} prefix={<RobotOutlined />} valueStyle={{ color: "#4096ff" }} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <Statistic title="就绪模型" value={readyCount} prefix={<CheckCircleOutlined />} valueStyle={{ color: "#00d4aa" }} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small" bordered={false}>
            <Statistic title="平均准确率" value={avgAccuracy * 100} precision={1} suffix="%" valueStyle={{ color: avgAccuracy >= 0.8 ? "#00d4aa" : "#ffd666" }} />
          </Card>
        </Col>
      </Row>

      {/* Model cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {models.map((m) => (
          <Col xs={24} sm={12} lg={8} key={m.id}>
            <Card
              hoverable
              bordered={false}
              style={{ height: "100%" }}
              actions={[
                <Button type="link" size="small" disabled={m.status === "training"}>训练</Button>,
                <Button type="link" size="small">详情</Button>,
                <Button type="link" size="small" danger>删除</Button>,
              ]}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <Text strong>{m.name}</Text>
                <Badge status={statusConfig[m.status]?.color as any} />
              </div>
              <Tag>{m.type.toUpperCase()}</Tag>
              <div style={{ marginTop: 12 }}>
                <Text type="secondary">状态: {statusConfig[m.status]?.label ?? m.status}</Text>
              </div>
              {m.accuracy != null && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">准确率: </Text>
                  <Progress
                    percent={Math.round(m.accuracy * 100)}
                    size="small"
                    strokeColor={m.accuracy >= 0.8 ? "#00d4aa" : m.accuracy >= 0.7 ? "#ffd666" : "#ff4d6a"}
                  />
                </div>
              )}
              {m.last_trained && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>最后训练: {m.last_trained}</Text>
                </div>
              )}
            </Card>
          </Col>
        ))}
      </Row>

      {/* Model Table */}
      <Card title="全部模型" bordered={false}>
        <Table dataSource={models} columns={columns} rowKey="id" pagination={false} size="middle" />
      </Card>

      {/* Train Modal */}
      <Modal title="训练新模型" open={trainOpen} onOk={handleTrain} onCancel={() => setTrainOpen(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="model_type" label="模型类型" rules={[{ required: true }]}>
            <Select options={[
              { label: "LSTM 时序预测", value: "lstm" },
              { label: "XGBoost 分类", value: "xgboost" },
              { label: "Transformer 注意力模型", value: "transformer" },
              { label: "HMM 隐马尔可夫", value: "hmm" },
              { label: "随机森林", value: "random_forest" },
              { label: "CNN 卷积网络", value: "cnn" },
            ]} />
          </Form.Item>
          <Form.Item name="params" label="额外参数 (JSON)">
            <Input.TextArea rows={4} placeholder='{"epochs": 100, "lr": 0.001}' />
          </Form.Item>
        </Form>
      </Modal>
    </Spin>
  );
}
