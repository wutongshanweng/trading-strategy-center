import { useState, useEffect } from "react";
import {
  Card, Input, Button, Typography, Space, Tag, Empty, message, Divider, Alert,
} from "antd";
import { ApiOutlined, SendOutlined } from "@ant-design/icons";
import { llmAgentApi } from "../services/phase4Api";

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

export default function LLMConfig() {
  const [providers, setProviders] = useState<string[]>([]);
  const [question, setQuestion] = useState("螺纹钢目前适合用什么策略?");
  const [regime, setRegime] = useState("trending");
  const [advice, setAdvice] = useState("");
  const [asking, setAsking] = useState(false);
  const [desc, setDesc] = useState("价格突破20日高点且成交量放大2倍时做多");
  const [draft, setDraft] = useState<any>(null);
  const [drafting, setDrafting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const d = await llmAgentApi.providers();
        setProviders(d?.providers || []);
      } catch { /* 后端未启动 */ }
    })();
  }, []);

  const ask = async () => {
    setAsking(true); setAdvice("");
    try {
      const d = await llmAgentApi.advise(question, { regime });
      setAdvice(d?.advice || "");
    } catch (e: any) {
      message.error("查询失败: " + (e?.message || ""));
    } finally { setAsking(false); }
  };

  const genDraft = async () => {
    setDrafting(true); setDraft(null);
    try {
      setDraft(await llmAgentApi.draft(desc));
    } catch (e: any) {
      message.error("生成失败: " + (e?.message || ""));
    } finally { setDrafting(false); }
  };

  return (
    <div>
      <Title level={3}><ApiOutlined /> LLM 配置 + 策略智能体</Title>

      <Card title="LLM 提供商状态" style={{ marginBottom: 16 }}>
        {providers.length ? (
          <Space wrap>
            {providers.map((p) => <Tag color="blue" key={p}>{p}</Tag>)}
          </Space>
        ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="未检测到已配置的 LLM 提供商" />}
        <Alert style={{ marginTop: 12 }} type="info" showIcon
          message="LLM API key 在 .env 中配置 (DEEPSEEK_API_KEY / OPENAI_API_KEY 等)。未配置时下方功能自动降级为本地规则建议。" />
      </Card>

      <Card title="策略建议 (Agent → LLM)" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: "100%" }}>
          <Input addonBefore="市态" value={regime} onChange={(e) => setRegime(e.target.value)}
            placeholder="trending / ranging / volatile" />
          <Space.Compact style={{ width: "100%" }}>
            <Input value={question} onChange={(e) => setQuestion(e.target.value)}
              onPressEnter={ask} placeholder="向策略顾问提问..." />
            <Button type="primary" icon={<SendOutlined />} loading={asking} onClick={ask}>提问</Button>
          </Space.Compact>
          {advice && (
            <Card size="small" style={{ background: "#fafafa" }}>
              <Paragraph style={{ whiteSpace: "pre-wrap", margin: 0 }}>{advice}</Paragraph>
            </Card>
          )}
        </Space>
      </Card>

      <Card title="策略代码生成">
        <Space direction="vertical" style={{ width: "100%" }}>
          <TextArea rows={2} value={desc} onChange={(e) => setDesc(e.target.value)}
            placeholder="用自然语言描述策略逻辑..." />
          <Button type="primary" loading={drafting} onClick={genDraft}>生成代码草稿</Button>
          {draft && (
            <>
              <Divider style={{ margin: "8px 0" }} />
              <Text type="secondary">来源: {draft.source === "llm" ? "LLM 生成" : "本地模板 (LLM 未配置)"}</Text>
              <pre style={{ background: "#1e1e1e", color: "#d4d4d4", padding: 12,
                borderRadius: 6, overflow: "auto", fontSize: 12 }}>{draft.code}</pre>
            </>
          )}
        </Space>
      </Card>
    </div>
  );
}
