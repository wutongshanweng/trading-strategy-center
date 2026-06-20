import { App as AntApp, ConfigProvider, theme } from "antd";
import { lazy, Suspense, useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import zhCN from "antd/locale/zh_CN";

// 样式
import "./App.css";

// 布局组件
import Layout from "./components/Layout";

// 动态导入页面组件
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Strategy = lazy(() => import("./pages/Strategy"));
const Trading = lazy(() => import("./pages/Trading"));
const Backtest = lazy(() => import("./pages/Backtest"));
const Portfolio = lazy(() => import("./pages/Portfolio"));
const ML = lazy(() => import("./pages/ML"));
const DataCenter = lazy(() => import("./pages/DataCenter"));
const Tournament = lazy(() => import("./pages/Tournament"));
const Settings = lazy(() => import("./pages/Settings"));
const Monitoring = lazy(() => import("./pages/Monitoring"));
const FactorResearch = lazy(() => import("./pages/FactorResearch"));
const Phase3 = lazy(() => import("./pages/Phase3"));

function PageLoading() {
  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "60vh" }}>
      <div>加载中...</div>
    </div>
  );
}

export default function App() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  // 监听主题变化
  useEffect(() => {
    const checkTheme = () => {
      const hasDarkClass = document.documentElement.classList.contains("dark-theme");
      setIsDarkMode(hasDarkClass);
    };

    // 初始检查
    checkTheme();

    // 监听class变化
    const observer = new MutationObserver(checkTheme);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });

    return () => observer.disconnect();
  }, []);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: "#1890ff",
          borderRadius: 6,
        },
      }}
    >
      <AntApp>
        <BrowserRouter>
          <Suspense fallback={<PageLoading />}>
            <Routes>
              <Route path="/" element={<Layout />}>
                <Route index element={<Dashboard />} />
                <Route path="strategies" element={<Strategy />} />
                <Route path="trading" element={<Trading />} />
                <Route path="backtest" element={<Backtest />} />
                <Route path="portfolio" element={<Portfolio />} />
                <Route path="ml" element={<ML />} />
                <Route path="factors" element={<FactorResearch />} />
                <Route path="phase3" element={<Phase3 />} />
                <Route path="data" element={<DataCenter />} />
                <Route path="tournament" element={<Tournament />} />
                <Route path="settings" element={<Settings />} />
                <Route path="monitoring" element={<Monitoring />} />
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AntApp>
    </ConfigProvider>
  );
}
