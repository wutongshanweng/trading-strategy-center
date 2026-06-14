"""
WebSocket实时信号推送服务
Real-time Signal Push via WebSocket
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import json
from datetime import datetime
from loguru import logger


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_subscriptions: Dict[WebSocket, set] = {}

    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_subscriptions[websocket] = set()
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_subscriptions:
            del self.client_subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast: {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)

    async def send_to_subscribers(self, topic: str, message: dict):
        """发送消息给特定主题的订阅者"""
        for connection, subscriptions in self.client_subscriptions.items():
            if topic in subscriptions:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    def subscribe(self, websocket: WebSocket, topic: str):
        """订阅主题"""
        if websocket in self.client_subscriptions:
            self.client_subscriptions[websocket].add(topic)

    def unsubscribe(self, websocket: WebSocket, topic: str):
        """取消订阅"""
        if websocket in self.client_subscriptions:
            self.client_subscriptions[websocket].discard(topic)


# 全局连接管理器
manager = ConnectionManager()


async def signal_generator():
    """
    信号生成器 - 模拟实时信号生成
    实际使用时，这里应该连接到策略引擎获取真实信号
    """
    import random

    symbols = ["RB", "CU", "AU", "AG", "IF"]
    contracts = ["2501", "2502", "2503"]
    strategies = ["双均线趋势", "RSI超买超卖", "MACD动量", "布林带突破"]

    while True:
        await asyncio.sleep(10)  # 每10秒生成一个信号

        symbol = random.choice(symbols)
        direction = random.choice(["BUY", "SELL"])
        confidence = 0.6 + random.random() * 0.35
        priority = "high" if confidence > 0.85 else "medium" if confidence > 0.7 else "low"

        signal = {
            "type": "signal",
            "data": {
                "id": f"signal_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "contract": f"{symbol}{random.choice(contracts)}",
                "price": 3000 + random.random() * 2000,
                "direction": direction,
                "strategy": random.choice(strategies),
                "reason": f"{'上穿' if direction == 'BUY' else '下穿'}关键点位",
                "confidence": round(confidence, 2),
                "priority": priority,
            },
        }

        yield signal


async def market_data_generator():
    """
    行情数据生成器 - 模拟实时行情推送
    """
    import random

    symbols = ["RB2501", "CU2501", "AU2501"]

    while True:
        await asyncio.sleep(1)  # 每秒更新行情

        for symbol in symbols:
            price = 3000 + random.random() * 2000
            yield {
                "type": "market_data",
                "data": {
                    "symbol": symbol,
                    "price": round(price, 2),
                    "volume": random.randint(1000, 10000),
                    "timestamp": datetime.now().isoformat(),
                },
            }


# WebSocket路由处理
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket主端点"""
    await manager.connect(websocket)

    try:
        # 发送欢迎消息
        await manager.send_personal_message(
            {
                "type": "connection",
                "message": "Connected to Trading Strategy Center",
                "timestamp": datetime.now().isoformat(),
            },
            websocket,
        )

        # 启动后台任务发送实时数据
        async def send_signals():
            async for signal in signal_generator():
                if websocket in manager.active_connections:
                    await manager.send_to_subscribers("signals", signal)

        async def send_market_data():
            async for data in market_data_generator():
                if websocket in manager.active_connections:
                    await manager.send_to_subscribers("market_data", data)

        # 创建后台任务
        signal_task = asyncio.create_task(send_signals())
        market_task = asyncio.create_task(send_market_data())

        # 接收客户端消息
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # 处理订阅请求
            if message.get("action") == "subscribe":
                topic = message.get("topic")
                manager.subscribe(websocket, topic)
                await manager.send_personal_message(
                    {"type": "subscription", "topic": topic, "status": "subscribed"},
                    websocket,
                )

            # 处理取消订阅
            elif message.get("action") == "unsubscribe":
                topic = message.get("topic")
                manager.unsubscribe(websocket, topic)
                await manager.send_personal_message(
                    {"type": "subscription", "topic": topic, "status": "unsubscribed"},
                    websocket,
                )

            # 回显消息（用于测试）
            else:
                await manager.send_personal_message(
                    {"type": "echo", "data": message}, websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# 广播实时信号的辅助函数
async def broadcast_signal(signal: dict):
    """广播信号到所有连接的客户端"""
    await manager.broadcast(
        {
            "type": "signal",
            "data": signal,
            "timestamp": datetime.now().isoformat(),
        }
    )


async def broadcast_market_data(symbol: str, price: float, volume: int):
    """广播行情数据"""
    await manager.send_to_subscribers(
        "market_data",
        {
            "type": "market_data",
            "data": {
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "timestamp": datetime.now().isoformat(),
            },
        },
    )
