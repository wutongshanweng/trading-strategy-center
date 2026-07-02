import { useState, useEffect } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout as AntLayout, Menu, Button, Typography, theme, Switch } from "antd";
import {
  DashboardOutlined,
  FundOutlined,
  StockOutlined,
  ExperimentOutlined,
  PieChartOutlined,
  DatabaseOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
  AppstoreOutlined,
  SyncOutlined,
  ApiOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  GithubOutlined,
  BulbOutlined,
  BranchesOutlined,
  SafetyCertificateOutlined,
  DollarOutlined,
  CloudServerOutlined,
} from "@ant-design/icons";

const { Sider, Header, Content, Footer } = AntLayout;
const { Text } = Typography;

const menuItems = [
  { key: "/", icon: <DashboardOutlined />, label: "Dashboard" },
  { key: "/macro-news", icon: <FundOutlined />, label: "新闻聚合" },
  { key: "/research-center", icon: <ThunderboltOutlined />, label: "研究中枢" },
  { key: "/vstock", icon: <SafetyCertificateOutlined />, label: "游资分析" },
  { key: "/factors", icon: <ExperimentOutlined />, label: "因子研究" },
  { key: "/china-finance", icon: <DollarOutlined />, label: "金融框架" },
  { key: "/phase3", icon: <ThunderboltOutlined />, label: "机器学习" },
  { key: "/strategy-library", icon: <AppstoreOutlined />, label: "策略工坊" },
  { key: "/iteration", icon: <BranchesOutlined />, label: "智能中心" },
  { key: "/tournament", icon: <TrophyOutlined />, label: "策略赛马" },
  { key: "/trading", icon: <StockOutlined />, label: "模拟交易" },
  { key: "/feedback", icon: <SyncOutlined />, label: "反馈闭环" },
  { key: "/backtest", icon: <ExperimentOutlined />, label: "策略回测" },
  { key: "/portfolio", icon: <PieChartOutlined />, label: "模拟持仓" },
  { key: "/llm-config", icon: <ApiOutlined />, label: "LLM配置" },
  { key: "/settings", icon: <SettingOutlined />, label: "系统设置" },
  { key: "/data", icon: <DatabaseOutlined />, label: "数据中心" },
];

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const { token } = theme.useToken();

  // 从localStorage读取主题设置
  useEffect(() => {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      setIsDarkMode(true);
      document.documentElement.classList.add("dark-theme");
    }
  }, []);

  // 切换主题
  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);

    if (newTheme) {
      document.documentElement.classList.add("dark-theme");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark-theme");
      localStorage.setItem("theme", "light");
    }
  };

  const selectedKey = menuItems
    .filter((m) => location.pathname.startsWith(m.key))
    .sort((a, b) => b.key.length - a.key.length)[0]?.key || "/";

  return (
    <AntLayout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        width={240}
        style={{
          background: isDarkMode ? "#141414" : token.colorBgContainer,
          borderRight: `1px solid ${isDarkMode ? "#303030" : token.colorBorderSecondary}`,
        }}
      >
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderBottom: `1px solid ${isDarkMode ? "#303030" : token.colorBorderSecondary}`,
            background: isDarkMode ? "#1f1f1f" : token.colorBgElevated,
          }}
        >
          <Text
            strong
            style={{
              fontSize: collapsed ? 16 : 18,
              color: isDarkMode ? "#ffffff" : token.colorText,
            }}
          >
            {collapsed ? "TSC" : "Trading Center"}
          </Text>
        </div>

        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{
            background: isDarkMode ? "#141414" : "transparent",
            border: "none",
          }}
          theme={isDarkMode ? "dark" : "light"}
        />
      </Sider>

      <AntLayout>
        <Header
          style={{
            padding: "0 24px",
            background: isDarkMode ? "#1f1f1f" : token.colorBgContainer,
            borderBottom: `1px solid ${isDarkMode ? "#303030" : token.colorBorderSecondary}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{
              color: isDarkMode ? "#ffffff" : token.colorTextSecondary,
              fontSize: 16
            }}
          />

          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {/* 主题切换开关 */}
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <BulbOutlined style={{ color: isDarkMode ? "#ffd666" : "#faad14", fontSize: 16 }} />
              <Switch
                checked={isDarkMode}
                onChange={toggleTheme}
                checkedChildren="暗色"
                unCheckedChildren="亮色"
              />
            </div>

            <Button
              type="text"
              icon={<GithubOutlined />}
              href="https://github.com"
              target="_blank"
              style={{ color: isDarkMode ? "#ffffff" : token.colorTextSecondary }}
            />

            <Text type="secondary" style={{ fontSize: 13, color: isDarkMode ? "#8c8c8c" : undefined }}>
              {new Date().toLocaleString("zh-CN")}
            </Text>
          </div>
        </Header>

        <Content
          style={{
            margin: 24,
            minHeight: "calc(100vh - 64px - 48px - 48px)",
            background: isDarkMode ? "#000000" : token.colorBgLayout,
          }}
        >
          <Outlet />
        </Content>

        <Footer
          style={{
            textAlign: "center",
            color: isDarkMode ? "#8c8c8c" : token.colorTextDisabled,
            fontSize: 12,
            borderTop: `1px solid ${isDarkMode ? "#303030" : token.colorBorderSecondary}`,
            padding: "12px 24px",
            background: isDarkMode ? "#141414" : token.colorBgContainer,
          }}
        >
          Trading Strategy Center v0.1.0 &copy; {new Date().getFullYear()} &mdash; Built with React +
          Ant Design
        </Footer>
      </AntLayout>
    </AntLayout>
  );
}
