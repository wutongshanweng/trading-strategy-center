import { useState } from "react";
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Space,
  Divider,
  InputNumber,
  Switch,
  message,
  Steps,
  Alert,
  Tag,
} from "antd";
import {
  PlusOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  SaveOutlined,
} from "@ant-design/icons";

const { Option } = Select;
const { TextArea } = Input;

export default function StrategyBuilder() {
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [signals, setSignals] = useState<any[]>([]);

  // 添加信号条件
  const addSignal = (type: "entry" | "exit") => {
    const newSignal = {
      id: Date.now(),
      type,
      indicator: "",
      condition: "",
      value: 0,
    };
    setSignals([...signals, newSignal]);
  };

  // 删除信号
  const removeSignal = (id: number) => {
    setSignals(signals.filter((s) => s.id !== id));
  };

  // 保存策略
  const handleSave = async (values: any) => {
    try {
      // TODO: 调用后端API保存策略
      console.log("保存策略:", { ...values, signals });
      message.success("策略已保存");
    } catch (error) {
      message.error("保存失败");
    }
  };

  // 立即回测
  const handleBacktest = async () => {
    try {
      const values = await form.validateFields();
      // TODO: 调用后端API执行回测
      message.success("回测已启动，请稍候...");
    } catch (error) {
      message.error("请完成策略配置");
    }
  };

  const steps = [
    {
      title: "基本信息",
      content: (
        <>
          <Form.Item
            label="策略名称"
            name="name"
            rules={[{ required: true, message: "请输入策略名称" }]}
          >
            <Input placeholder="我的趋势策略" />
          </Form.Item>

          <Form.Item
            label="策略类型"
            name="type"
            rules={[{ required: true }]}
          >
            <Select placeholder="选择策略类型">
              <Option value="trend">趋势跟踪</Option>
              <Option value="mean_reversion">均值回复</Option>
              <Option value="arbitrage">套利策略</Option>
              <Option value="momentum">动量策略</Option>
              <Option value="breakout">突破策略</Option>
            </Select>
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea rows={3} placeholder="简要描述策略逻辑" />
          </Form.Item>
        </>
      ),
    },
    {
      title: "信号配置",
      content: (
        <>
          <Alert
            message="配置入场和出场信号"
            description="添加技术指标条件，当所有条件满足时触发信号"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Card size="small" title="入场信号" style={{ marginBottom: 16 }}>
            {signals.filter((s) => s.type === "entry").length === 0 ? (
              <div style={{ textAlign: "center", padding: "20px 0", color: "#999" }}>
                暂无入场信号，点击下方按钮添加
              </div>
            ) : (
              <Space direction="vertical" style={{ width: "100%" }}>
                {signals
                  .filter((s) => s.type === "entry")
                  .map((signal) => (
                    <div key={signal.id}>
                      <Space>
                        <Select
                          placeholder="指标"
                          style={{ width: 150 }}
                          onChange={(value) => {
                            signal.indicator = value;
                          }}
                        >
                          <Option value="MA">移动平均线</Option>
                          <Option value="RSI">RSI</Option>
                          <Option value="MACD">MACD</Option>
                          <Option value="BOLL">布林带</Option>
                        </Select>
                        <Select
                          placeholder="条件"
                          style={{ width: 120 }}
                          onChange={(value) => {
                            signal.condition = value;
                          }}
                        >
                          <Option value=">">大于</Option>
                          <Option value="<">小于</Option>
                          <Option value="cross_above">上穿</Option>
                          <Option value="cross_below">下穿</Option>
                        </Select>
                        <InputNumber
                          placeholder="数值"
                          style={{ width: 100 }}
                          onChange={(value) => {
                            signal.value = value;
                          }}
                        />
                        <Button
                          danger
                          size="small"
                          icon={<DeleteOutlined />}
                          onClick={() => removeSignal(signal.id)}
                        />
                      </Space>
                    </div>
                  ))}
              </Space>
            )}
            <Button
              type="dashed"
              icon={<PlusOutlined />}
              onClick={() => addSignal("entry")}
              style={{ marginTop: 16, width: "100%" }}
            >
              添加入场条件
            </Button>
          </Card>

          <Card size="small" title="出场信号">
            {signals.filter((s) => s.type === "exit").length === 0 ? (
              <div style={{ textAlign: "center", padding: "20px 0", color: "#999" }}>
                暂无出场信号，点击下方按钮添加
              </div>
            ) : (
              <Space direction="vertical" style={{ width: "100%" }}>
                {signals
                  .filter((s) => s.type === "exit")
                  .map((signal) => (
                    <div key={signal.id}>
                      <Space>
                        <Select placeholder="指标" style={{ width: 150 }}>
                          <Option value="MA">移动平均线</Option>
                          <Option value="RSI">RSI</Option>
                          <Option value="MACD">MACD</Option>
                          <Option value="time">持仓时间</Option>
                        </Select>
                        <Select placeholder="条件" style={{ width: 120 }}>
                          <Option value=">">大于</Option>
                          <Option value="<">小于</Option>
                          <Option value="cross_above">上穿</Option>
                          <Option value="cross_below">下穿</Option>
                        </Select>
                        <InputNumber placeholder="数值" style={{ width: 100 }} />
                        <Button
                          danger
                          size="small"
                          icon={<DeleteOutlined />}
                          onClick={() => removeSignal(signal.id)}
                        />
                      </Space>
                    </div>
                  ))}
              </Space>
            )}
            <Button
              type="dashed"
              icon={<PlusOutlined />}
              onClick={() => addSignal("exit")}
              style={{ marginTop: 16, width: "100%" }}
            >
              添加出场条件
            </Button>
          </Card>
        </>
      ),
    },
    {
      title: "参数和风控",
      content: (
        <>
          <Divider>策略参数</Divider>
          <Form.Item label="快速周期" name="fast_period" initialValue={5}>
            <InputNumber min={1} max={50} style={{ width: "100%" }} />
          </Form.Item>

          <Form.Item label="慢速周期" name="slow_period" initialValue={20}>
            <InputNumber min={5} max={200} style={{ width: "100%" }} />
          </Form.Item>

          <Divider>风险管理</Divider>
          <Form.Item label="止损比例(%)" name="stop_loss" initialValue={2}>
            <InputNumber min={0.1} max={50} step={0.1} style={{ width: "100%" }} />
          </Form.Item>

          <Form.Item label="止盈比例(%)" name="take_profit" initialValue={10}>
            <InputNumber min={0.1} max={100} step={0.1} style={{ width: "100%" }} />
          </Form.Item>

          <Form.Item label="最大仓位(%)" name="max_position" initialValue={30}>
            <InputNumber min={1} max={100} style={{ width: "100%" }} />
          </Form.Item>

          <Form.Item label="允许做空" name="allow_short" valuePropName="checked">
            <Switch />
          </Form.Item>
        </>
      ),
    },
  ];

  return (
    <Card title="创建新策略" style={{ maxWidth: 1000, margin: "0 auto" }}>
      <Steps current={currentStep} style={{ marginBottom: 32 }}>
        {steps.map((item) => (
          <Steps.Step key={item.title} title={item.title} />
        ))}
      </Steps>

      <Form form={form} layout="vertical" onFinish={handleSave}>
        <div style={{ minHeight: 400 }}>{steps[currentStep].content}</div>

        <Divider />

        <Space>
          {currentStep > 0 && (
            <Button onClick={() => setCurrentStep(currentStep - 1)}>
              上一步
            </Button>
          )}
          {currentStep < steps.length - 1 && (
            <Button type="primary" onClick={() => setCurrentStep(currentStep + 1)}>
              下一步
            </Button>
          )}
          {currentStep === steps.length - 1 && (
            <>
              <Button type="primary" icon={<SaveOutlined />} htmlType="submit">
                保存策略
              </Button>
              <Button
                type="default"
                icon={<PlayCircleOutlined />}
                onClick={handleBacktest}
              >
                立即回测
              </Button>
            </>
          )}
        </Space>
      </Form>
    </Card>
  );
}
