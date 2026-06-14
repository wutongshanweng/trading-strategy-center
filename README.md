# Trading Strategy Center

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.4+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)

**企业级量化交易平台 | Enterprise Quantitative Trading Platform**

[English](#english) | [中文](#chinese)

</div>

---

## 🌟 项目亮点

- 🚀 **101个Alpha因子** - 完整的WorldQuant Alpha101因子库
- 📊 **57+交易策略** - 覆盖趋势、均值回复、套利、动量等
- 🤖 **ML策略优化** - 贝叶斯优化 + 遗传算法自动调参
- 💡 **实时信号推送** - WebSocket秒级推送交易信号
- 🎯 **策略锦标赛** - 赛马机制自动筛选优质策略
- 🌐 **Agent API** - 完整的外部API生态系统
- 🎨 **双主题UI** - 亮色/暗色主题自由切换
- 📱 **响应式设计** - 完美支持桌面和移动端

---

## 📋 目录

- [快速开始](#快速开始)
- [核心功能](#核心功能)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [安装部署](#安装部署)
- [使用文档](#使用文档)
- [API文档](#api文档)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 🚀 快速开始

### 5分钟快速体验

```bash
# 1. 克隆项目
git clone https://github.com/wutongshanweng/trading-strategy-center.git
cd trading-strategy-center

# 2. 安装依赖
pip install -e .
cd frontend && npm install && cd ..

# 3. 启动服务
python main.py  # 后端: http://localhost:8000
cd frontend && npm run dev  # 前端: http://localhost:3000

# 4. 访问系统
打开浏览器: http://localhost:3000
```

详细文档: [QUICK_START.md](./QUICK_START.md)

---

## ✨ 核心功能

### 1. 实时信号监控
- ✅ WebSocket实时推送
- ✅ 高/中/低优先级信号分类
- ✅ 声音 + 浏览器推送通知
- ✅ 完整的信号详情（品种/价格/置信度/原因）

### 2. 策略自动进化
- ✅ ML参数自动优化（贝叶斯 + 遗传算法）
- ✅ 策略自动组合（最大化夏普比率）
- ✅ 策略共振分析
- ✅ 高胜率策略自动部署

### 3. 数据实时同步
- ✅ 分钟/小时级实时同步
- ✅ 自动填充缺失数据
- ✅ 多品种并发同步
- ✅ 同步状态实时监控

### 4. 策略锦标赛
- ✅ 自动排名和竞赛
- ✅ 前10%自动晋级实盘
- ✅ 后30%淘汰重新优化
- ✅ 赛马资金动态分配

### 5. Agent API
- ✅ JWT认证系统
- ✅ 数据API（历史+实时）
- ✅ 策略API（列表+信号计算）
- ✅ 因子API（101个Alpha因子）
- ✅ 交易API（模拟下单）

### 6. Web策略创建器
- ✅ 可视化策略构建
- ✅ 无需编程
- ✅ 一键回测
- ✅ 即时部署

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────┐
│           Frontend (React + TS)              │
│  Dashboard | Strategies | Backtest | Data   │
└─────────────────┬───────────────────────────┘
                  │ WebSocket + REST API
┌─────────────────▼───────────────────────────┐
│           Backend (FastAPI)                  │
│  ├─ API Layer (REST + WebSocket)            │
│  ├─ Core Layer (Alpha/RL/Risk)              │
│  ├─ ML Layer (Evolution/Tournament)         │
│  └─ Data Layer (Sync/Cache/Quality)         │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│     Data Sources & Storage                  │
│  AKShare | yfinance | TDX | PostgreSQL      │
└─────────────────────────────────────────────┘
```

详细架构: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI 0.104+
- **语言**: Python 3.10+
- **ML**: scikit-learn, scipy, numpy, pandas
- **数据**: PostgreSQL, Redis, SQLAlchemy
- **异步**: asyncio, aiohttp

### 前端
- **框架**: React 18 + TypeScript 5
- **UI**: Ant Design 5
- **图表**: lightweight-charts (TradingView)
- **状态**: Zustand
- **构建**: Vite 5

### 部署
- **容器**: Docker + Docker Compose
- **Web服务器**: Uvicorn + Nginx
- **任务队列**: Celery + Redis

---

## 📦 安装部署

### 开发环境

```bash
# Python环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .

# 前端环境
cd frontend
npm install
```

### Docker部署

```bash
# 一键启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

详细部署: [DEPLOYMENT.md](./docs/DEPLOYMENT.md)

---

## 📚 使用文档

### 新手入门
- [快速开始](./QUICK_START.md) - 5分钟上手指南
- [系统架构](./ARCHITECTURE.md) - 完整架构设计
- [功能说明](./IMPLEMENTATION_COMPLETE_PHASE2.md) - 所有功能详解

### 开发指南
- [贡献指南](./CONTRIBUTING.md) - 如何参与开发
- [API文档](./docs/API.md) - 完整API参考
- [策略开发](./docs/STRATEGY_DEVELOPMENT.md) - 自定义策略开发

### 用户指南
- [前端使用](./FRONTEND_UPGRADE_REPORT.md) - Web界面使用
- [主题切换](./THEME_SWITCH_GUIDE.md) - 亮色/暗色主题
- [Agent集成](./IMPLEMENTATION_COMPLETE_PHASE1.md) - 外部Agent接入

---

## 🔌 API文档

### 认证
```bash
POST /api/v1/agent/auth
Content-Type: application/json

{
  "api_key": "your_api_key"
}
```

### 获取信号
```bash
POST /api/v1/agent/signals/compute
Authorization: Bearer {token}

{
  "symbol": "RB",
  "strategy_names": ["trend_ma_cross"],
  "timeframe": "1d"
}
```

完整API文档: [API.md](./docs/API.md)

---

## 📊 项目统计

```
代码行数:     160,000+
Python文件:   420+
前端组件:     50+
策略数量:     67个
Alpha因子:    101个
RL算法:       7种
测试用例:     981个
文档数量:     23份
```

---

## 🤝 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](./CONTRIBUTING.md)

### 贡献方式
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](./LICENSE) 文件了解详情

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=wutongshanweng/trading-strategy-center&type=Date)](https://star-history.com/#wutongshanweng/trading-strategy-center&Date)

---

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/wutongshanweng/trading-strategy-center/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wutongshanweng/trading-strategy-center/discussions)

---

## 🙏 致谢

感谢所有贡献者和开源社区的支持！

---

## 🔗 相关链接

- [文档中心](./docs)
- [更新日志](./CHANGELOG.md)
- [路线图](./docs/ROADMAP.md)

---

<div align="center">

**如果这个项目对您有帮助，请给个 ⭐ Star！**

Made with ❤️ by Trading Strategy Center Team

</div>
