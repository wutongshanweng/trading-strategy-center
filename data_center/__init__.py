"""
Trading Strategy Center — Data Center
======================================

统一数据中心：管理多数据源接入、历史数据下载、合约知识库、
实时同步、多源校验，覆盖中国期货/期权/A股及国际市场。

架构:
    data_center/
    ├── core/          # 基础框架 (BaseFetcher, DataSource, Cache)
    ├── fetchers/      # 11个数据源获取器
    ├── knowledge/     # 合约知识库、主力合约、交易所信息
    ├── history/       # 历史数据下载、实时同步
    ├── verification/  # 跨数据源校验、数据质量
    └── api/           # Data Center API 路由
"""

from .core.base_fetcher import BaseFetcher
from .core.data_source import DataSourceManager
from .knowledge.main_contract import MainContractResolver
from .knowledge.contract_knowledge import ContractKnowledgeBase

__all__ = [
    'BaseFetcher',
    'DataSourceManager',
    'MainContractResolver',
    'ContractKnowledgeBase',
]
