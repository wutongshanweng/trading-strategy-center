import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { App as AntApp, Spin } from "antd";
import Layout from "./components/Layout";

// Dynamic imports for code splitting — each page is a separate chunk
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

function PageLoading() {
  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "60vh" }}>
      <Spin size="large">
        <div style={{ padding: 100 }} />
      </Spin>
    </div>
  );
}

export default function App() {
  return (
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
              <Route path="data" element={<DataCenter />} />
              <Route path="tournament" element={<Tournament />} />
              <Route path="settings" element={<Settings />} />
              <Route path="monitoring" element={<Monitoring />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </AntApp>
  );
}
