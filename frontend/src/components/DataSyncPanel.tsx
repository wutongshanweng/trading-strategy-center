import { useState, useEffect } from "react";
import {
  Card,
  Switch,
  Select,
  Button,
  Space,
  Tag,
  Alert,
  Table,
  Row,
  Col,
  Statistic,
  message,
  Divider,
  Progress,
} from "antd";
import {
  SyncOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import axios from "axios";

const { Option } = Select;

interface SyncStatus {
  status: "idle" | "syncing" | "paused" | "error";
  config: {
    enabled: boolean;
    interval: string;
    auto_fill: boolean;
    symbols: string[];
  };
  stats: Record<string, {
    last_sync: string | null;
    success_count: number;
    error_count: number;
    missing_filled: number;
  }>;
  active_tasks: number;
}

export default function DataSyncPanel() {
  const [syncEnabled, setSyncEnabled] = useState(false);
  const [syncInterval, setSyncInterval] = useState("1m");
  const [autoFill, setAutoFill] = useState(true);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(["RB", "CU", "AU"]);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(false);

  // 可用品种列表
  const availableSymbols = [
    "RB", "CU", "AU", "AG", "IF", "IC", "IH",
    "MA", "TA", "CF", "SR", "OI", "RM", "FG"
  ];

  // 获取同步状态
  const fetchSyncStatus = async () => {
    try {
      const response = await axios.get("http://localhost:8000/api/v1/data-sync/status");
      setSyncStatus(response.data);
      setSyncEnabled(response.data.config.enabled);
      setSyncInterval(response.data.config.interval);
      setAutoFill(response.data.config.auto_fill);
      if (response.data.config.symbols.length > 0) {
        setSelectedSymbols(response.data.config.symbols);
      }
    } catch (error) {
      console.error("获取同步状态失败:", error);
    }
  };

  useEffect(() => {
    fetchSyncStatus();
    // 每5秒刷新状态
    const interval = setInterval(fetchSyncStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // 启动同步
  const handleStartSync = async () => {
    if (selectedSymbols.length === 0) {
      message.warning("请至少选择一个品种");
      return;
    }

    setLoading(true);
    try {
      await axios.post("http://localhost:8000/api/v1/data-sync/start", {
        symbols: selectedSymbols,
        interval: syncInterval,
        auto_fill: autoFill,
      });
      message.success("实时同步已启动");
      setSyncEnabled(true);
      fetchSyncStatus();
    } catch (error) {
      message.error("启动同步失败");
    } finally {
      setLoading(false);
    }
  };

  // 停止同步
  const handleStopSync = async () => {
    setLoading(true);
    try {
      await axios.post("http://localhost:8000/api/v1/data-sync/stop");
      message.success("实时同步已停止");
      setSyncEnabled(false);
      fetchSyncStatus();
    } catch (error) {
      message.error("停止同步失败");
    } finally {
      setLoading(false);
    }
  };

  // 暂停/恢复同步
  const handleTogglePause = async () => {
    setLoading(true);
    try {
      const endpoint = syncStatus?.status === "syncing" ? "pause" : "resume";
      await axios.post(`http://localhost:8000/api/v1/data-sync/${endpoint}`);
      message.success(syncStatus?.status === "syncing" ? "同步已暂停" : "同步已恢复");
      fetchSyncStatus();
    } catch (error) {
      message.error("操作失败");
    } finally {
      setLoading(false);
    }
  };

  // 状态颜色
  const getStatusColor = (status?: string) => {
    switch (status) {
      case "syncing":
        return "success";
      case "paused":
        return "warning";
      case "error":
        return "error";
      default:
        return "default";
    }
  };

  // 状态文本
  const getStatusText = (status?: string) => {
    switch (status) {
      case "syncing":
        return "运行中";
      case "paused":
        return "已暂停";
      case "error":
        return "错误";
      default:
        return "未启动";
    }
  };

  // 统计数据
  const totalSuccess = syncStatus
    ? Object.values(syncStatus.stats).reduce((sum, s) => sum + s.success_count, 0)
    : 0;
  const totalErrors = syncStatus
    ? Object.values(syncStatus.stats).reduce((sum, s) => sum + s.error_count, 0)
    : 0;
  const totalFilled = syncStatus
    ? Object.values(syncStatus.stats).reduce((sum, s) => sum + s.missing_filled, 0)
    : 0;

  // 表格列
  const columns = [
    {
      title: "品种",
      dataIndex: "symbol",
      key: "symbol",
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: "最后同步",
      dataIndex: "last_sync",
      key: "last_sync",
      render: (time: string | null) =>
        time ? new Date(time).toLocaleTimeString("zh-CN") : "-",
    },
    {
      title: "成功次数",
      dataIndex: "success_count",
      key: "success_count",
      render: (count: number) => <Tag color="success">{count}</Tag>,
    },
    {
      title: "失败次数",
      dataIndex: "error_count",
      key: "error_count",
      render: (count: number) =>
        count > 0 ? <Tag color="error">{count}</Tag> : <Tag>0</Tag>,
    },
    {
      title: "已填充",
      dataIndex: "missing_filled",
      key: "missing_filled",
      render: (count: number) => count,
    },
    {
      title: "状态",
      key: "status",
      render: () => (
        <Tag color={getStatusColor(syncStatus?.status)}>
          {getStatusText(syncStatus?.status)}
        </Tag>
      ),
    },
  ];

  // 表格数据
  const tableData = syncStatus
    ? Object.entries(syncStatus.stats).map(([symbol, stats]) => ({
        symbol,
        ...stats,
      }))
    : [];

  return (
    <Card
      title={
        <Space>
          <SyncOutlined spin={syncStatus?.status === "syncing"} />
          数据实时同步
        </Space>
      }
      extra={
        <Tag color={getStatusColor(syncStatus?.status)} icon={<CheckCircleOutlined />}>
          {getStatusText(syncStatus?.status)}
        </Tag>
      }
    >
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃任务"
              value={syncStatus?.active_tasks || 0}
              prefix={<SyncOutlined />}
              valueStyle={{ color: "#1890ff" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功次数"
              value={totalSuccess}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: "#52c41a" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败次数"
              value={totalErrors}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: totalErrors > 0 ? "#ff4d4f" : "#d9d9d9" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已填充数据"
              value={totalFilled}
              prefix={<ReloadOutlined />}
              valueStyle={{ color: "#722ed1" }}
            />
          </Card>
        </Col>
      </Row>

      <Alert
        message="实时数据同步"
        description="启用后，系统将按设定频率自动获取最新数据。自动填充功能会检测并补全缺失的历史数据。"
        type="info"
        showIcon
        closable
        style={{ marginBottom: 16 }}
      />

      {/* 配置区域 */}
      <Card size="small" title="同步配置" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <Row gutter={16} align="middle">
            <Col span={4}>
              <strong>启用同步:</strong>
            </Col>
            <Col span={20}>
              <Switch
                checked={syncEnabled}
                onChange={(checked) => {
                  if (checked) {
                    handleStartSync();
                  } else {
                    handleStopSync();
                  }
                }}
                checkedChildren="已启用"
                unCheckedChildren="已禁用"
                loading={loading}
              />
            </Col>
          </Row>

          <Row gutter={16} align="middle">
            <Col span={4}>
              <strong>同步频率:</strong>
            </Col>
            <Col span={20}>
              <Select
                value={syncInterval}
                onChange={setSyncInterval}
                style={{ width: 200 }}
                disabled={syncEnabled}
              >
                <Option value="1m">每1分钟</Option>
                <Option value="5m">每5分钟</Option>
                <Option value="15m">每15分钟</Option>
                <Option value="1h">每1小时</Option>
              </Select>
              <span style={{ marginLeft: 16, color: "#999" }}>
                {syncEnabled && "（运行中无法修改）"}
              </span>
            </Col>
          </Row>

          <Row gutter={16} align="middle">
            <Col span={4}>
              <strong>自动填充:</strong>
            </Col>
            <Col span={20}>
              <Switch
                checked={autoFill}
                onChange={setAutoFill}
                checkedChildren="开启"
                unCheckedChildren="关闭"
                disabled={syncEnabled}
              />
              <span style={{ marginLeft: 16, color: "#999" }}>
                自动检测并填充缺失数据
              </span>
            </Col>
          </Row>

          <Row gutter={16} align="middle">
            <Col span={4}>
              <strong>监控品种:</strong>
            </Col>
            <Col span={20}>
              <Select
                mode="multiple"
                value={selectedSymbols}
                onChange={setSelectedSymbols}
                style={{ width: "100%" }}
                placeholder="选择需要同步的品种"
                disabled={syncEnabled}
              >
                {availableSymbols.map((symbol) => (
                  <Option key={symbol} value={symbol}>
                    {symbol}
                  </Option>
                ))}
              </Select>
            </Col>
          </Row>
        </Space>
      </Card>

      {/* 操作按钮 */}
      <Space style={{ marginBottom: 16 }}>
        {!syncEnabled ? (
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleStartSync}
            loading={loading}
          >
            启动同步
          </Button>
        ) : (
          <>
            <Button
              danger
              icon={<CloseCircleOutlined />}
              onClick={handleStopSync}
              loading={loading}
            >
              停止同步
            </Button>
            <Button
              icon={<PauseCircleOutlined />}
              onClick={handleTogglePause}
              loading={loading}
            >
              {syncStatus?.status === "syncing" ? "暂停" : "恢复"}
            </Button>
          </>
        )}
        <Button icon={<ReloadOutlined />} onClick={fetchSyncStatus}>
          刷新状态
        </Button>
      </Space>

      <Divider />

      {/* 同步详情表格 */}
      <Table
        columns={columns}
        dataSource={tableData}
        rowKey="symbol"
        pagination={false}
        size="small"
      />
    </Card>
  );
}
