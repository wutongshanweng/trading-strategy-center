import { useEffect, useState, useCallback } from "react";
import {
  Card, Row, Col, Statistic, Typography, Tag, Table, Spin, Empty, Alert, Button,
  Collapse, Space, message, Tooltip, Tabs, Switch, InputNumber, Descriptions,
} from "antd";
import {
  ThunderboltOutlined, SafetyCertificateOutlined, ReloadOutlined,
  ExperimentOutlined, HistoryOutlined, BranchesOutlined, RobotOutlined,
  PlayCircleOutlined,
} from "@ant-design/icons";
import {
  getIterationOverview, getParamVersions, getPromotionHistory, getRetrainHistory,
  runRetrainCycle, getAutomationConfig, setAutomationConfig, runAutomationNow, listRealMLModels,
} from "../api/client";

const { Title, Text } = Typography;

function degColor(v: number) {
  return v < -0.3 ? "#ff4d4f" : v < -0.1 ? "#faad14" : "#52c41a";
}

export default function IterationMonitor() {
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState<any>(null);
  const [paramVersions, setParamVersions] = useState<Record<string, any[]>>({});
  const [promoHist, setPromoHist] = useState<any[]>([]);
  const [retrainHist, setRetrainHist] = useState<any[]>([]);
  const [retraining, setRetraining] = useState(false);
  // 自动化
  const [autoCfg, setAutoCfg] = useState<any>(null);
  const [autoLog, setAutoLog] = useState<any[]>([]);
  const [autoBusy, setAutoBusy] = useState(false);
  // ML 模型
  const [mlModels, setMlModels] = useState<string[]>([]);

  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      const [ov, pv, ph, rh, ac, ml] = await Promise.allSettled([
        getIterationOverview(), getParamVersions(), getPromotionHistory(10), getRetrainHistory(10),
        getAutomationConfig(), listRealMLModels(),
      ]);
      if (ov.status === "fulfilled") setOverview(ov.value.data);
      if (pv.status === "fulfilled") setParamVersions(pv.value.data.strategies || {});
      if (ph.status === "fulfilled") setPromoHist(ph.value.data.history || []);
      if (rh.status === "fulfilled") setRetrainHist(rh.value.data.history || []);
      if (ac.status === "fulfilled") { setAutoCfg(ac.value.data.config); setAutoLog(ac.value.data.log || []); }
      if (ml.status === "fulfilled") setMlModels(ml.value.data.models || []);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const runRetrain = async () => {
    setRetraining(true);
    message.loading({ content: "触发重训周期 (参数层贝叶斯优化, 较慢)...", key: "rt", duration: 0 });
    try {
      const res = await runRetrainCycle({ param_n_iter: 8 });
      const d = res.data;
      message.success({ content: `重训完成: 参数层优化 ${d.param_optimized?.length ?? 0} 个策略`, key: "rt", duration: 5 });
      loadAll();
    } catch {
      message.error({ content: "重训失败 (需先有排行榜候选)", key: "rt" });
    } finally { setRetraining(false); }
  };

  const toggleAuto = async (enabled: boolean) => {
    try {
      const res = await setAutomationConfig({ enabled });
      setAutoCfg(res.data.config);
      message.success(enabled ? "已开启自动迭代" : "已关闭自动迭代");
    } catch { message.error("设置失败"); }
  };

  const saveInterval = async (interval_hours: number) => {
    try {
      const res = await setAutomationConfig({ interval_hours });
      setAutoCfg(res.data.config);
    } catch { message.error("设置失败"); }
  };

  const runAutoNow = async () => {
    setAutoBusy(true);
    message.loading({ content: "立即执行安全自动周期 (回测+参数重优化, 较慢)...", key: "an", duration: 0 });
    try {
      const res = await runAutomationNow();
      const d = res.data;
      message.success({ content: `周期完成: 回测冠军 ${d.tournament?.top_strategy ?? "—"}, 参数优化 ${d.retrain?.params_optimized ?? 0} 个 (${d.duration_sec}s)`, key: "an", duration: 6 });
      loadAll();
    } catch {
      message.error({ content: "执行失败", key: "an" });
    } finally { setAutoBusy(false); }
  };

  const c = overview?.counts || {};

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Title level={3} style={{ margin: 0 }}><BranchesOutlined /> 智能中心</Title>
        <Space>
          <Button icon={<ExperimentOutlined />} loading={retraining} onClick={runRetrain}>触发重训周期</Button>
          <Button icon={<ReloadOutlined />} onClick={loadAll} loading={loading}>刷新</Button>
        </Space>
      </div>
      <Text type="secondary">机器学习模型 + 自我迭代闭环 (锦标赛→反馈→重训→晋级) 统一管理</Text>

      {/* 自动化控制面板 */}
      <Card size="small" style={{ margin: "12px 0" }}
        title={<><PlayCircleOutlined /> 自动迭代控制</>}>
        {!autoCfg ? <Spin /> : (
          <Row gutter={16} align="middle">
            <Col>
              <Space direction="vertical" size={0}>
                <Text type="secondary" style={{ fontSize: 12 }}>自动迭代开关</Text>
                <Switch checked={autoCfg.enabled} onChange={toggleAuto}
                  checkedChildren="自动" unCheckedChildren="手动" />
              </Space>
            </Col>
            <Col>
              <Space direction="vertical" size={0}>
                <Text type="secondary" style={{ fontSize: 12 }}>周期 (小时)</Text>
                <InputNumber min={1} max={168} value={autoCfg.interval_hours}
                  onChange={(v) => v && saveInterval(v)} style={{ width: 90 }} />
              </Space>
            </Col>
            <Col>
              <Space direction="vertical" size={0}>
                <Text type="secondary" style={{ fontSize: 12 }}>上次运行</Text>
                <Text>{autoCfg.last_run ? new Date(autoCfg.last_run).toLocaleString("zh-CN") : "从未"}</Text>
              </Space>
            </Col>
            <Col flex="auto" style={{ textAlign: "right" }}>
              <Button type="primary" ghost icon={<ThunderboltOutlined />} loading={autoBusy} onClick={runAutoNow}>
                立即执行一次
              </Button>
            </Col>
          </Row>
        )}
        <Alert style={{ marginTop: 12 }} type="warning" showIcon
          message="安全边界: 自动周期只做「回测刷新排名 + 参数层重优化」。晋升验证后的「毕业为冠军」和资金分配始终需要人工批准, 不会自动执行。" />
        {autoLog.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>最近自动运行:</Text>
            <Table size="small" pagination={false} style={{ marginTop: 4 }}
              dataSource={autoLog.slice(0, 5).map((l, i) => ({ ...l, key: i }))}
              columns={[
                { title: "时间", dataIndex: "finished_at", key: "t", render: (x: string) => x?.slice(5, 19).replace("T", " ") },
                { title: "触发", dataIndex: "trigger", key: "tr", render: (x: string) => <Tag>{x === "scheduled" ? "定时" : x === "manual" ? "手动" : x}</Tag> },
                { title: "回测冠军", dataIndex: "tournament", key: "top", render: (t: any) => t?.top_strategy ?? "—" },
                { title: "参数优化", dataIndex: "retrain", key: "rt", render: (r: any) => r?.params_optimized ?? 0 },
                { title: "耗时(s)", dataIndex: "duration_sec", key: "d" },
                { title: "错误", dataIndex: "error", key: "e", render: (e: string) => e ? <Text type="danger" style={{ fontSize: 11 }}>{e}</Text> : "-" },
              ]} />
          </div>
        )}
      </Card>

      <Tabs
        defaultActiveKey="iteration"
        items={[
          {
            key: "iteration", label: <span><BranchesOutlined /> 迭代监控</span>,
            children: loading && !overview ? <div style={{ textAlign: "center", padding: 60 }}><Spin size="large" /></div> : (
              <>
                <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
                  <Col xs={12} sm={6}><Card size="small"><Statistic title="排名策略" value={c.ranked_strategies ?? 0} prefix={<ThunderboltOutlined />} /></Card></Col>
                  <Col xs={12} sm={6}><Card size="small"><Statistic title="参数已调优" value={c.param_tuned_strategies ?? 0} suffix={`/ ${c.param_versions_total ?? 0}版本`} /></Card></Col>
                  <Col xs={12} sm={6}><Card size="small"><Statistic title="晋升验证次数" value={c.promotion_runs ?? 0} prefix={<SafetyCertificateOutlined />} /></Card></Col>
                  <Col xs={12} sm={6}><Card size="small"><Statistic title="重训周期" value={c.retrain_cycles ?? 0} prefix={<ExperimentOutlined />} /></Card></Col>
                  <Col xs={12} sm={6}><Card size="small"><Statistic title="反馈记录" value={c.feedback_entries ?? 0} prefix={<HistoryOutlined />} /></Card></Col>
                  <Col xs={12} sm={6}><Card size="small"><Statistic title="冠军" value={c.champions ?? 0} valueStyle={{ color: "#faad14" }} /></Card></Col>
                  <Col xs={12} sm={6}><Card size="small"><Statistic title="考察中" value={c.challengers ?? 0} valueStyle={{ color: "#4096ff" }} /></Card></Col>
                </Row>
                <MonitorBody paramVersions={paramVersions} promoHist={promoHist} retrainHist={retrainHist} />
              </>
            ),
          },
          {
            key: "ml", label: <span><RobotOutlined /> ML模型</span>,
            children: <MLPanel models={mlModels} />,
          },
        ]}
      />
    </div>
  );
}

function MLPanel({ models }: { models: string[] }) {
  const MODEL_CN: Record<string, string> = {
    linear_regression: "线性回归", arima: "ARIMA 时序", garch: "GARCH 波动率",
    hmm: "HMM 市场状态", random_forest: "随机森林",
  };
  return (
    <Card size="small" title={<><RobotOutlined /> 可用 ML 模型 (后端真实注册)</>}>
      {models.length === 0 ? <Empty description="后端未返回模型, 检查 /api/v1/models" image={Empty.PRESENTED_IMAGE_SIMPLE} /> : (
        <>
          <Alert type="info" showIcon style={{ marginBottom: 12 }}
            message="这些是后端 quant_models 真实注册的统计模型。训练/预测通过策略回测与重训周期间接驱动 (参数层); 也可经 /api/v1/models/{name}/train 单独训练。" />
          <Row gutter={[12, 12]}>
            {models.map((m) => (
              <Col xs={24} sm={12} lg={8} key={m}>
                <Card size="small" hoverable>
                  <Space direction="vertical" size={2}>
                    <Text strong>{MODEL_CN[m] || m}</Text>
                    <Tag color="blue">{m}</Tag>
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </>
      )}
    </Card>
  );
}

function MonitorBody({ paramVersions, promoHist, retrainHist }: {
  paramVersions: Record<string, any[]>; promoHist: any[]; retrainHist: any[];
}) {
  const paramStrategies = Object.keys(paramVersions).filter((s) => paramVersions[s]?.length);

  return (
    <>
      {/* 参数版本演化 */}
      <Card size="small" title={<><ExperimentOutlined /> 参数优化版本演化</>} style={{ marginBottom: 16 }}>
        {paramStrategies.length === 0 ? <Empty description="暂无参数优化记录, 去触发重训周期" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
          <Collapse items={paramStrategies.map((s) => ({
            key: s,
            label: <Space><Text strong>{s}</Text><Tag color="blue">{paramVersions[s].length} 个版本</Tag>
              <Text type="secondary">最新分 {paramVersions[s][paramVersions[s].length - 1]?.score}</Text></Space>,
            children: (
              <Table size="small" pagination={false}
                dataSource={paramVersions[s].map((v: any, i: number) => ({ ...v, key: i }))}
                columns={[
                  { title: "版本", dataIndex: "version", key: "v", width: 70 },
                  { title: "得分(夏普)", dataIndex: "score", key: "score",
                    render: (x: number) => <span style={{ color: x > 0 ? "#52c41a" : "#ff4d4f" }}>{x}</span> },
                  { title: "参数", dataIndex: "params", key: "p",
                    render: (p: any) => <Text code style={{ fontSize: 11 }}>{JSON.stringify(p)}</Text> },
                ]} />
            ),
          }))} />}
      </Card>

      {/* 晋升验证历史 + walk-forward 窗口明细 */}
      <Card size="small" title={<><SafetyCertificateOutlined /> 晋升验证历史 (walk-forward 窗口明细)</>} style={{ marginBottom: 16 }}>
        {promoHist.length === 0 ? <Empty description="暂无晋升验证记录" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
          <Collapse items={promoHist.map((run, ri) => ({
            key: String(ri),
            label: <Space>
              <Text>{run.timestamp?.slice(5, 19).replace("T", " ")}</Text>
              <Tag>评估 {run.evaluated}</Tag>
              <Tag color="green">晋级 {run.n_promoted}</Tag>
              <Text type="secondary">市态冠军: {(run.champions_by_regime || []).join("/") || "无"}</Text>
            </Space>,
            children: (
              <Table size="small" pagination={false}
                dataSource={(run.verdicts || []).map((v: any, i: number) => ({ ...v, key: i }))}
                expandable={{
                  expandedRowRender: (v: any) => (
                    <Table size="small" pagination={false}
                      dataSource={(v.windows || []).map((w: any, i: number) => ({ ...w, key: i }))}
                      columns={[
                        { title: "窗口", dataIndex: "window_id", key: "w", width: 60 },
                        { title: "样本内夏普", dataIndex: "is_sharpe", key: "is" },
                        { title: "样本外夏普", dataIndex: "oos_sharpe", key: "oos",
                          render: (x: number) => <span style={{ color: x > 0 ? "#52c41a" : "#ff4d4f" }}>{x}</span> },
                        { title: "退化", dataIndex: "degradation", key: "deg",
                          render: (x: number) => <span style={{ color: degColor(x) }}>{(x * 100).toFixed(0)}%</span> },
                        { title: "参数", dataIndex: "params", key: "p",
                          render: (p: any) => <Text code style={{ fontSize: 11 }}>{JSON.stringify(p)}</Text> },
                      ]} />
                  ),
                  rowExpandable: (v: any) => (v.windows || []).length > 0,
                }}
                columns={[
                  { title: "策略", dataIndex: "strategy_name", key: "n", render: (x: string) => <Text strong>{x}</Text> },
                  { title: "结果", dataIndex: "passed", key: "passed",
                    render: (p: boolean) => <Tag color={p ? "green" : "red"}>{p ? "晋级" : "拒绝"}</Tag> },
                  { title: "OOS夏普", dataIndex: "mean_oos_sharpe", key: "oos" },
                  { title: "退化", dataIndex: "mean_degradation", key: "deg",
                    render: (x: number) => <span style={{ color: degColor(x) }}>{(x * 100).toFixed(0)}%</span> },
                  { title: "过拟合比", dataIndex: "overfit_ratio", key: "of",
                    render: (x: number) => `${(x * 100).toFixed(0)}%` },
                  { title: "市态", dataIndex: "regime", key: "r", render: (x: string) => <Tag>{x}</Tag> },
                  { title: "理由", dataIndex: "reason", key: "reason", render: (x: string) => <Text type="secondary" style={{ fontSize: 12 }}>{x}</Text> },
                ]} />
            ),
          }))} />}
      </Card>

      {/* 重训历史 */}
      <Card size="small" title={<><ExperimentOutlined /> 重训周期历史</>}>
        {retrainHist.length === 0 ? <Empty description="暂无重训记录" image={Empty.PRESENTED_IMAGE_SIMPLE} /> :
          <Table size="small" pagination={false}
            dataSource={retrainHist.map((r, i) => ({ ...r, key: i }))}
            columns={[
              { title: "时间", dataIndex: "timestamp", key: "t", render: (x: string) => x?.slice(5, 19).replace("T", " ") },
              { title: "参数层优化", dataIndex: "n_params_optimized", key: "np",
                render: (n: number, r: any) => <Tooltip title={(r.param_optimized || []).map((p: any) => `${p.strategy}:${p.best_score}`).join(", ")}><Tag color="blue">{n} 个</Tag></Tooltip> },
              { title: "因子检测", dataIndex: "n_factors_checked", key: "nf", render: (n: number) => `${n}` },
              { title: "模型检测", dataIndex: "n_models_checked", key: "nm", render: (n: number) => `${n}` },
              { title: "已重训模型", dataIndex: "models_retrained", key: "mr", render: (m: string[]) => (m || []).length || "-" },
              { title: "说明", dataIndex: "notes", key: "notes", render: (n: string[]) => <Text type="secondary" style={{ fontSize: 11 }}>{(n || []).join("; ")}</Text> },
            ]} />}
      </Card>
    </>
  );
}
