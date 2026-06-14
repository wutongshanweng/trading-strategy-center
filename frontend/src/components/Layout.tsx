import { useState } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout as AntLayout, Menu, Button, Typography, theme } from "antd";
import {
  DashboardOutlined,
  FundOutlined,
  StockOutlined,
  ExperimentOutlined,
  PieChartOutlined,
  RobotOutlined,
  DatabaseOutlined,
  TrophyOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  GithubOutlined,
} from "@ant-design/icons";

const { Sider, Header, Content, Footer } = AntLayout;
const { Text } = Typography;

const menuItems = [
  { key: "/", icon: <DashboardOutlined />, label: "Dashboard" },
  { key: "/strategies", icon: <FundOutlined />, label: "策略" },
  { key: "/trading", icon: <StockOutlined />, label: "交易" },
  { key: "/backtest", icon: <ExperimentOutlined />, label: "回测" },
  { key: "/portfolio", icon: <PieChartOutlined />, label: "组合" },
  { key: "/ml", icon: <RobotOutlined />, label: "机器学习" },
  { key: "/factors", icon: <ExperimentOutlined />, label: "因子研究" },
  { key: "/data", icon: <DatabaseOutlined />, label: "数据中心" },
  { key: "/tournament", icon: <TrophyOutlined />, label: "锦标赛" },
  { key: "/settings", icon: <SettingOutlined />, label: "设置" },
];

export default function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const { token } = theme.useToken();

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
        theme="dark"
        style={{
          overflow: "auto",
          height: "100vh",
          position: "fixed",
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          borderRight: `1px solid ${token.colorBorderSecondary}`,
        }}
      >
        {/* Logo */}
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
            margin: "0 16px",
          }}
        >
          <Text
            strong
            style={{
              fontSize: collapsed ? 16 : 18,
              background: "linear-gradient(135deg, #1677ff, #00d4aa)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              whiteSpace: "nowrap",
            }}
          >
            {collapsed ? "TSC" : "Trading Strategy Center"}
          </Text>
        </div>

        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 8, borderRight: 0 }}
        />
      </Sider>

      <AntLayout style={{ marginLeft: collapsed ? 80 : 240, transition: "margin-left 0.2s" }}>
        <Header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 24px",
            position: "sticky",
            top: 0,
            zIndex: 99,
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ color: token.colorTextSecondary, fontSize: 16 }}
          />
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Text type="secondary" style={{ fontSize: 13 }}>
              {new Date().toLocaleString("zh-CN")}
            </Text>
          </div>
        </Header>

        <Content style={{ margin: 24, minHeight: "calc(100vh - 64px - 48px - 48px)" }}>
          <Outlet />
        </Content>

        <Footer
          style={{
            textAlign: "center",
            color: token.colorTextDisabled,
            fontSize: 12,
            borderTop: `1px solid ${token.colorBorderSecondary}`,
            padding: "12px 24px",
          }}
        >
          Trading Strategy Center v0.1.0 &copy; {new Date().getFullYear()} &mdash; Built with React +
          Ant Design
        </Footer>
      </AntLayout>
    </AntLayout>
  );
}
