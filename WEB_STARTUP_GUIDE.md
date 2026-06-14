# Web服务启动指南

## 🚀 启动步骤

### 1. 启动后端服务

```bash
cd "D:\完整项目\trading-strategy-center"

# 方式1: 直接启动（前台）
python main.py

# 方式2: 使用uvicorn（推荐）
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 方式3: 后台启动
start /b uvicorn main:app --host 0.0.0.0 --port 8000
```

**验证后端**:
- 访问: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### 2. 启动前端服务

```bash
cd "D:\完整项目\trading-strategy-center\frontend"

# 首次启动需要安装依赖
npm install

# 启动开发服务器
npm run dev

# 后台启动
start /b npm run dev
```

**访问前端**:
- 地址: http://localhost:3000
- 自动热重载已启用

### 3. Docker方式（推荐）

```bash
cd "D:\完整项目\trading-strategy-center"

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 🔧 常见问题

### 问题1: 端口被占用

```bash
# Windows查找占用端口的进程
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 杀死进程（替换PID）
taskkill /PID <进程ID> /F
```

### 问题2: 依赖未安装

```bash
# 后端依赖
pip install -e .

# 前端依赖
cd frontend && npm install
```

### 问题3: Python模块找不到

```bash
# 设置PYTHONPATH
set PYTHONPATH=D:\完整项目\trading-strategy-center

# 或在Python脚本中添加
import sys
sys.path.insert(0, 'D:\\完整项目\\trading-strategy-center')
```

### 问题4: Node版本不兼容

需要 Node.js 18+，检查版本：
```bash
node --version
```

如果版本过低，访问 https://nodejs.org 下载最新LTS版本。

---

## 📊 服务状态检查

### 后端状态
```bash
# 健康检查
curl http://localhost:8000/health

# API列表
curl http://localhost:8000/docs

# 策略列表
curl http://localhost:8000/api/v1/strategies
```

### 前端状态
```bash
# 访问首页
curl http://localhost:3000

# 检查构建
cd frontend && npm run build
```

---

## 🎯 快速访问

### 开发环境
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **前端界面**: http://localhost:3000

### 生产环境（Docker）
- **Nginx入口**: http://localhost
- **后端API**: http://localhost:8000
- **前端界面**: http://localhost:3000

---

## 📝 手动启动脚本

### Windows启动脚本 (start.bat)

```bat
@echo off
echo Starting Trading Strategy Center...

cd /d D:\完整项目\trading-strategy-center

echo [1/2] Starting Backend...
start /b cmd /c "uvicorn main:app --host 0.0.0.0 --port 8000 > logs\backend.log 2>&1"

timeout /t 5

echo [2/2] Starting Frontend...
cd frontend
start /b cmd /c "npm run dev > ..\logs\frontend.log 2>&1"

timeout /t 3

echo.
echo ✓ Services started!
echo.
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo Press any key to view logs...
pause > nul

type ..\logs\backend.log
type ..\logs\frontend.log
```

### 停止脚本 (stop.bat)

```bat
@echo off
echo Stopping Trading Strategy Center...

taskkill /F /IM "uvicorn.exe" > nul 2>&1
taskkill /F /IM "node.exe" > nul 2>&1

echo ✓ All services stopped!
pause
```

---

## 🌐 浏览器访问

### 推荐浏览器
- Chrome 90+ ✅
- Edge 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅

### 首次访问
1. 打开浏览器
2. 访问 http://localhost:3000
3. 系统会显示Dashboard主页
4. 可以立即浏览策略、查看数据

---

## 💡 开发提示

### 后端开发
```bash
# 自动重载（代码修改自动重启）
uvicorn main:app --reload

# 查看日志
tail -f logs/app.log
```

### 前端开发
```bash
# 开发模式（热重载）
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

---

## 🐛 调试模式

### 后端调试
```python
# main.py中启用调试
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="debug"  # 详细日志
    )
```

### 前端调试
在浏览器中按 F12 打开开发者工具，查看：
- Console: JavaScript日志
- Network: API请求
- React DevTools: 组件状态

---

## ✅ 启动成功标志

### 后端启动成功
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 前端启动成功
```
VITE v5.2.0  ready in 1234 ms

➜  Local:   http://localhost:3000/
➜  Network: http://192.168.1.x:3000/
```

---

## 📞 需要帮助？

如果启动遇到问题：

1. 查看日志文件
   - 后端: `logs/app.log`
   - 前端: 终端输出

2. 检查依赖
   - 后端: `pip list`
   - 前端: `npm list`

3. 查看文档
   - [QUICK_START.md](./QUICK_START.md)
   - [README.md](./README.md)

---

**启动成功后，尽情探索量化交易平台！** 🚀
