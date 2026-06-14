# Trading Strategy Center — API 参考文档

## 基础信息

- **基础URL**: `http://localhost:8000`
- **API 文档 (Swagger)**: `http://localhost:8000/docs`
- **API 版本**: v1 (前缀 `/api/v1/`)
- **格式**: JSON
- **认证**: Bearer Token (可选)

---

## 一、系统健康

### `GET /health`
系统健康检查。

**响应示例**:
```json
{ "status": "healthy", "version": "0.1.0" }
```

---

## 二、策略管理

### `GET /api/v1/strategies`
获取所有策略列表。

### `GET /api/v1/strategies/{name}`
获取单个策略详情。

### `POST /api/v1/strategies/compute`
计算策略信号。

**请求体**:
```json
{
  "symbol": "AAPL",
  "timeframe": "1d",
  "strategy_names": ["trend_following", "mean_reversion"]
}
```

---

## 三、交易执行

### `GET /api/v1/trading/positions`
获取当前持仓列表。

### `POST /api/v1/trading/execute`
执行交易指令。

**请求体**:
```json
{
  "symbol": "AAPL",
  "direction": "long",
  "quantity": 100,
  "price": 150.0
}
```

### `POST /api/v1/trading/close/{symbol}`
平仓指定品种。

### `GET /api/v1/trading/summary`
获取交易概要（总收益、胜率等）。

---

## 四、回测引擎

### `POST /api/v1/backtest/run`
运行回测。

**请求体**:
```json
{
  "symbol": "AAPL",
  "strategy_name": "trend_following",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 1000000.0
}
```

### `GET /api/v1/backtest/results`
获取最近回测结果。

---

## 五、投资组合

### `GET /api/v1/portfolio/stats`
获取投资组合统计。

### `GET /api/v1/portfolio/correlation`
获取资产相关性矩阵。

### `POST /api/v1/portfolio/rebalance`
建议再平衡交易。

**请求体**:
```json
{
  "target_weights": {"AAPL": 0.5, "GOOG": 0.5}
}
```

---

## 六、机器学习

### `GET /api/v1/models`
获取可用 ML 模型列表。

### `POST /api/v1/models/{name}/train`
训练指定模型。

**请求体**:
```json
{
  "symbol": "AAPL",
  "timeframe": "1d",
  "params": {"n_estimators": 100}
}
```

### `POST /api/v1/models/{name}/predict`
使用已训练模型进行预测。

---

## 七、智能风控

### `POST /api/v1/intelligence/risk/var`
计算 VaR (Value at Risk)。

**请求体**:
```json
{
  "returns": [0.01, -0.02, 0.005, ...],
  "confidence": 0.95,
  "method": "historical"
}
```

### `POST /api/v1/intelligence/risk/cvar`
计算 CVaR (Conditional VaR)。

### `POST /api/v1/intelligence/risk/kelly`
计算凯利公式仓位。

**请求体**:
```json
{
  "win_rate": 0.6,
  "win_loss_ratio": 2.0
}
```

### `POST /api/v1/intelligence/risk/stress-test`
压力测试。

---

## 八、强化学习

### `GET /api/v1/intelligence/rl/algorithms`
获取可用 RL 算法列表。

### `POST /api/v1/intelligence/rl/dqn/train`
训练 DQN 模型。

---

## 九、Alpha 因子

### `GET /api/v1/intelligence/alpha/factors`
列出全部 101 个 Alpha 因子。

### `POST /api/v1/intelligence/alpha/compute`
计算指定 Alpha 因子。

**请求体**:
```json
{
  "factor_names": ["alpha001", "alpha002"],
  "n_rows": 100
}
```

---

## 十、策略锦标赛

### `GET /api/v1/tournament/standings`
获取排行榜（支持 `?top_n=20` 参数）。

### `POST /api/v1/tournament/register`
注册参赛策略。

**请求体**:
```json
{ "name": "Alpha因子组合" }
```

### `POST /api/v1/tournament/trade`
记录交易结果。

**请求体**:
```json
{ "name": "Alpha因子组合", "pnl": 1250.0 }
```

### `POST /api/v1/tournament/update-scores`
重新计算所有评分。

### `POST /api/v1/tournament/eliminate?pct=0.1`
淘汰底部 10% 策略。

### `GET /api/v1/tournament/summary`
获取锦标赛统计概览。

---

## 十一、监控与告警

### `POST /api/v1/intelligence/monitoring/collect`
收集系统指标。

### `GET /api/v1/intelligence/monitoring/metrics`
获取已收集的指标。

### `POST /api/v1/intelligence/monitoring/alerts/check`
检查告警规则。

### `POST /api/v1/intelligence/monitoring/alerts/rules`
添加告警规则。

### `GET /api/v1/intelligence/monitoring/alerts/rules`
列出告警规则。

---

## 错误处理

所有错误返回标准格式:
```json
{
  "detail": "错误描述信息"
}
```

| HTTP 状态码 | 含义 |
|-------------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 参数验证失败 |
| 500 | 服务器内部错误 |
