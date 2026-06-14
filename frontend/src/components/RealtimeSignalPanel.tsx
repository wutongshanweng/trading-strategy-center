import { useState, useEffect } from "react";
import {
  Card,
  Badge,
  Tag,
  Space,
  Button,
  Switch,
  Tooltip,
  Alert,
  Typography,
  Divider,
  Row,
  Col,
  Statistic,
} from "antd";
import {
  BellOutlined,
  SoundOutlined,
  FilterOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from "@ant-design/icons";

const { Text, Title } = Typography;

interface RealtimeSignal {
  id: string;
  timestamp: string;
  symbol: string;
  contract: string;
  price: number;
  direction: "BUY" | "SELL" | "HOLD";
  strategy: string;
  reason: string;
  confidence: number;
  priority: "high" | "medium" | "low";
}

// Mock实时信号数据
const generateMockSignal = (): RealtimeSignal => {
  const symbols = ["RB", "CU", "AU", "AG", "IF"];
  const contracts = ["2501", "2502", "2503"];
  const strategies = ["双均线趋势", "RSI超买超卖", "MACD动量", "布林带突破", "一目均衡"];
  const reasons = [
    "5日线上穿20日线，MACD金叉",
    "RSI(14)=78，进入超买区域",
    "价格突破布林带上轨",
    "MACD柱状图由负转正",
    "转换线上穿基准线",
  ];

  const symbol = symbols[Math.floor(Math.random() * symbols.length)];
  const direction = Math.random() > 0.5 ? "BUY" : "SELL";
  const confidence = 0.6 + Math.random() * 0.35;
  const priority = confidence > 0.85 ? "high" : confidence > 0.7 ? "medium" : "low";

  return {
    id: `signal_${Date.now()}_${Math.random()}`,
    timestamp: new Date().toLocaleTimeString("zh-CN"),
    symbol,
    contract: `${symbol}${contracts[Math.floor(Math.random() * contracts.length)]}`,
    price: 3000 + Math.random() * 2000,
    direction,
    strategy: strategies[Math.floor(Math.random() * strategies.length)],
    reason: reasons[Math.floor(Math.random() * reasons.length)],
    confidence,
    priority,
  };
};

export default function RealtimeSignalPanel() {
  const [signals, setSignals] = useState<RealtimeSignal[]>([]);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [pushEnabled, setPushEnabled] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 模拟实时信号接收
  useEffect(() => {
    if (!autoRefresh) return;

    // 初始化一些信号
    const initialSignals = Array.from({ length: 3 }, generateMockSignal);
    setSignals(initialSignals);

    // 每10秒添加新信号
    const interval = setInterval(() => {
      const newSignal = generateMockSignal();
      setSignals((prev) => [newSignal, ...prev].slice(0, 20)); // 保留最近20个

      // 播放提示音
      if (soundEnabled && newSignal.priority === "high") {
        playNotificationSound();
      }

      // 推送通知
      if (pushEnabled && newSignal.priority === "high") {
        showBrowserNotification(newSignal);
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [autoRefresh, soundEnabled, pushEnabled]);

  const playNotificationSound = () => {
    const audio = new Audio("data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSyAzPDZizMHFmW57OihUBELTKXh8LJnHAU2jdXwzn0vBSh+zO/blEILElyx6OyrWBUIQ5zd8sFuJAUrhM/w3I4+CRZiuOznpVITC0mi4O+1aR0FM4vU8c1+MAYnfczvnV0RDUmk4e+zaR4EL4fP8N6SPwsVXLXp7K1aFgZAl93xwW8lBSiBzvDajToIFGO66+mjTxEMTKPg8LJoHgU1i9Xxz4IxBSh9yu+hWhMMR6Hd8LZuIQUpgs/w24k5CBRjtOnnm0wRDUal4PG2aSAFM4vV8c6AMgUofszvrFsUC0Wf3fG8cSYGKYHP8NuLOwgUYrPp56hVEwtGpN7xt2sgBjCJ1fHOfzEFKH3M76tbFAw=");
    audio.play().catch(() => {}); // 忽略播放失败
  };

  const showBrowserNotification = (signal: RealtimeSignal) => {
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification("🔔 交易信号告警", {
        body: `${signal.contract} ${signal.direction} ${signal.price.toFixed(0)} (${(signal.confidence * 100).toFixed(0)}%)`,
        icon: "/favicon.ico",
      });
    }
  };

  const requestNotificationPermission = async () => {
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission();
    }
  };

  useEffect(() => {
    requestNotificationPermission();
  }, []);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return { bg: "#fff1f0", border: "#ff4d4f", dot: "error" };
      case "medium":
        return { bg: "#fffbe6", border: "#faad14", dot: "warning" };
      default:
        return { bg: "#f6ffed", border: "#52c41a", dot: "success" };
    }
  };

  const getDirectionColor = (direction: string) => {
    return direction === "BUY" ? "success" : "error";
  };

  const highPrioritySignals = signals.filter((s) => s.priority === "high");
  const mediumPrioritySignals = signals.filter((s) => s.priority === "medium");
  const lowPrioritySignals = signals.filter((s) => s.priority === "low");

  return (
    <Card
      title={
        <Space>
          <BellOutlined style={{ fontSize: 18, color: "#1890ff" }} />
          <span>实盘信号告警</span>
          <Badge count={highPrioritySignals.length} style={{ backgroundColor: "#ff4d4f" }} />
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="声音提醒">
            <Switch
              checked={soundEnabled}
              onChange={setSoundEnabled}
              checkedChildren={<SoundOutlined />}
              unCheckedChildren={<SoundOutlined />}
              size="small"
            />
          </Tooltip>
          <Tooltip title="推送通知">
            <Switch
              checked={pushEnabled}
              onChange={setPushEnabled}
              checkedChildren={<BellOutlined />}
              unCheckedChildren={<BellOutlined />}
              size="small"
            />
          </Tooltip>
          <Tooltip title="自动刷新">
            <Switch
              checked={autoRefresh}
              onChange={setAutoRefresh}
              checkedChildren={<ReloadOutlined />}
              unCheckedChildren={<ReloadOutlined />}
              size="small"
            />
          </Tooltip>
          <Button size="small" icon={<FilterOutlined />}>
            过滤
          </Button>
        </Space>
      }
      style={{ marginBottom: 24 }}
    >
      {/* 统计信息 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Statistic
            title="高优先级"
            value={highPrioritySignals.length}
            valueStyle={{ color: "#ff4d4f" }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="中优先级"
            value={mediumPrioritySignals.length}
            valueStyle={{ color: "#faad14" }}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="低优先级"
            value={lowPrioritySignals.length}
            valueStyle={{ color: "#52c41a" }}
          />
        </Col>
      </Row>

      <Alert
        message="实时信号监控中"
        description="信号每10秒更新一次。高优先级信号会触发声音和推送通知。"
        type="info"
        showIcon
        closable
        style={{ marginBottom: 16 }}
      />

      {/* 高优先级信号 */}
      {highPrioritySignals.length > 0 && (
        <>
          <Title level={5} style={{ color: "#ff4d4f" }}>
            🔴 高优先级信号 ({highPrioritySignals.length})
          </Title>
          <Space direction="vertical" style={{ width: "100%", marginBottom: 16 }} size="small">
            {highPrioritySignals.map((signal) => {
              const colors = getPriorityColor(signal.priority);
              return (
                <Card
                  key={signal.id}
                  size="small"
                  style={{
                    backgroundColor: colors.bg,
                    borderColor: colors.border,
                    borderWidth: 2,
                  }}
                >
                  <Row gutter={16} align="middle">
                    <Col span={12}>
                      <Space direction="vertical" size={0}>
                        <Space>
                          <Text strong style={{ fontSize: 16 }}>
                            {signal.contract}
                          </Text>
                          <Tag color={getDirectionColor(signal.direction)}>
                            {signal.direction === "BUY" ? "买入" : "卖出"}
                          </Tag>
                          <Text strong>{signal.price.toFixed(0)}</Text>
                        </Space>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          策略: {signal.strategy}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {signal.reason}
                        </Text>
                      </Space>
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="置信度"
                        value={signal.confidence * 100}
                        precision={0}
                        suffix="%"
                        valueStyle={{
                          color: signal.confidence > 0.8 ? "#52c41a" : "#faad14",
                          fontSize: 20,
                        }}
                      />
                    </Col>
                    <Col span={6}>
                      <Space>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {signal.timestamp}
                        </Text>
                        <Button size="small" type="primary">
                          查看详情
                        </Button>
                        <Button size="small" icon={<CloseCircleOutlined />}>
                          忽略
                        </Button>
                      </Space>
                    </Col>
                  </Row>
                </Card>
              );
            })}
          </Space>
        </>
      )}

      {/* 中优先级信号 */}
      {mediumPrioritySignals.length > 0 && (
        <>
          <Divider />
          <Title level={5} style={{ color: "#faad14" }}>
            🟡 中优先级信号 ({mediumPrioritySignals.length})
          </Title>
          <Space direction="vertical" style={{ width: "100%", marginBottom: 16 }} size="small">
            {mediumPrioritySignals.slice(0, 3).map((signal) => {
              const colors = getPriorityColor(signal.priority);
              return (
                <Card
                  key={signal.id}
                  size="small"
                  style={{ backgroundColor: colors.bg, borderColor: colors.border }}
                >
                  <Space>
                    <Text strong>{signal.contract}</Text>
                    <Tag color={getDirectionColor(signal.direction)}>
                      {signal.direction === "BUY" ? "买入" : "卖出"}
                    </Tag>
                    <Text>{signal.price.toFixed(0)}</Text>
                    <Text type="secondary">置信度: {(signal.confidence * 100).toFixed(0)}%</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {signal.timestamp}
                    </Text>
                  </Space>
                </Card>
              );
            })}
            {mediumPrioritySignals.length > 3 && (
              <Text type="secondary">还有 {mediumPrioritySignals.length - 3} 个信号...</Text>
            )}
          </Space>
        </>
      )}

      {/* 无信号提示 */}
      {signals.length === 0 && (
        <div style={{ textAlign: "center", padding: "40px 0", color: "#999" }}>
          <CheckCircleOutlined style={{ fontSize: 48, marginBottom: 16 }} />
          <div>暂无信号，系统监控中...</div>
        </div>
      )}
    </Card>
  );
}
