# 启动指南

## 快速启动

本项目需要同时启动 **后端 API 服务** 和 **前端 UI**。

### 方式一：使用启动脚本 (Windows)

```powershell
# 在项目根目录执行
.\start.ps1
```

### 方式二：手动启动

**1. 启动后端** (端口 8000)

```powershell
cd d:\完整项目\trading-strategy-center
python main.py
```

**2. 启动前端** (端口 3000)

```powershell
cd d:\完整项目\trading-strategy-center\frontend
npm run dev
```

## 访问地址

| 服务 | 地址 |
|------|------|
| 前端 UI | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

## 环境要求

- Python 3.10+
- Node.js 18+
- 依赖已安装: `pip install -e .` (后端), `npm install` (前端)

## 注意事项

- 后端需要先启动，前端才能正常调用 API
- 部分功能需要配置 `.env` 文件中的 API Key
- 新闻数据会在后端启动时自动抓取
