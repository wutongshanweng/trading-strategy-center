"""initial_schema

Revision ID: 5622da4f0062
Revises: 
Create Date: 2026-06-13 08:12:14.299019

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5622da4f0062'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # Table: backtest_results
    # ============================================================
    op.create_table('backtest_results',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('strategy', sa.String(length=50), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.String(length=10), nullable=False),
        sa.Column('end_date', sa.String(length=10), nullable=False),
        sa.Column('total_return', sa.Float(), nullable=False),
        sa.Column('sharpe_ratio', sa.Float(), nullable=False),
        sa.Column('max_drawdown', sa.Float(), nullable=False),
        sa.Column('win_rate', sa.Float(), nullable=False),
        sa.Column('total_trades', sa.Integer(), nullable=False),
        sa.Column('params', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'strategy', 'start_date', 'end_date', name='uq_backtest_run')
    )

    # ============================================================
    # Table: contracts
    # ============================================================
    op.create_table('contracts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='品种中文名'),
        sa.Column('exchange', sa.String(length=20), nullable=False, comment='交易所 SHFE/DCE/CZCE/CFFEX/INE/GFEX'),
        sa.Column('category', sa.String(length=20), nullable=False, comment='分类 metal/energy/chemical/agri/equity/rate'),
        sa.Column('multiplier', sa.Integer(), nullable=False, server_default=sa.text('1'), comment='合约乘数'),
        sa.Column('min_tick', sa.Float(), nullable=False, server_default=sa.text('0.01'), comment='最小变动价位'),
        sa.Column('margin_rate', sa.Float(), nullable=False, server_default=sa.text('0.1'), comment='保证金比例'),
        sa.Column('commission', sa.Float(), nullable=False, server_default=sa.text('0.0'), comment='手续费'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'), comment='是否启用'),
        sa.Column('delivery_months', sa.String(length=50), nullable=True, comment='交割月份列表,逗号分隔'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )
    op.create_index('idx_contract_exchange', 'contracts', ['exchange'])
    op.create_index('idx_contract_category', 'contracts', ['category'])

    # ============================================================
    # Table: klines
    # ============================================================
    op.create_table('klines',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('period', sa.String(length=10), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('open', sa.Float(), nullable=False),
        sa.Column('high', sa.Float(), nullable=False),
        sa.Column('low', sa.Float(), nullable=False),
        sa.Column('close', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        sa.Column('open_interest', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'period', 'timestamp')
    )
    op.create_index('idx_kline_symbol_period', 'klines', ['symbol', 'period'])

    # ============================================================
    # Table: model_versions
    # ============================================================
    op.create_table('model_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True, comment='训练指标'),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('trained_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_name', 'version', name='uq_model_version')
    )

    # ============================================================
    # Table: monitor_alerts
    # ============================================================
    op.create_table('monitor_alerts',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=True),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=True),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('threshold', sa.Float(), nullable=True),
        sa.Column('acknowledged', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_alert_level_time', 'monitor_alerts', ['level', 'created_at'])

    # ============================================================
    # Table: monitor_rules
    # ============================================================
    op.create_table('monitor_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='规则名称'),
        sa.Column('rule_type', sa.String(length=50), nullable=False, comment='规则类型: drawdown/var/volume/signal'),
        sa.Column('symbol', sa.String(length=20), nullable=True),
        sa.Column('params', sa.JSON(), nullable=False, comment='规则参数JSON'),
        sa.Column('level', sa.String(length=20), nullable=False, server_default=sa.text("'WARNING'")),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # ============================================================
    # Table: parameter_versions
    # ============================================================
    op.create_table('parameter_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('strategy_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('params', sa.JSON(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('strategy_name', 'version', name='uq_strategy_version')
    )
    op.create_index('idx_parameter_strategy_name', 'parameter_versions', ['strategy_name'])

    # ============================================================
    # Table: performance_snapshots
    # ============================================================
    op.create_table('performance_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('snapshot_date', sa.DateTime(), nullable=False),
        sa.Column('strategy_name', sa.String(length=100), nullable=False),
        sa.Column('total_equity', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('cash', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('positions_value', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('daily_pnl', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('total_pnl', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('drawdown', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('metrics', sa.JSON(), nullable=True, comment='扩展指标JSON'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('snapshot_date', 'strategy_name', name='uq_snapshot_strategy')
    )

    # ============================================================
    # Table: positions
    # ============================================================
    op.create_table('positions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('stop_loss', sa.Float(), nullable=True),
        sa.Column('take_profit', sa.Float(), nullable=True),
        sa.Column('pnl', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('strategy', sa.String(length=100), nullable=False, server_default=sa.text("''"), comment='关联策略名称'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'OPEN'")),
        sa.Column('opened_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # ============================================================
    # Table: signals
    # ============================================================
    op.create_table('signals',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('contract', sa.String(length=20), nullable=False),
        sa.Column('period', sa.String(length=10), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('strategy_name', sa.String(length=50), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('extra', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract', 'period', 'timestamp', 'strategy_name')
    )

    # ============================================================
    # Table: tournament_records
    # ============================================================
    op.create_table('tournament_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('round', sa.Integer(), nullable=False),
        sa.Column('mode', sa.String(length=20), nullable=False, comment='DUEL/TOURNAMENT/EXPLORATION'),
        sa.Column('total_strategies', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('eliminated_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # ============================================================
    # Table: tournament_strategies
    # ============================================================
    op.create_table('tournament_strategies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('strategy_name', sa.String(length=100), nullable=False),
        sa.Column('tournament_round', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('score', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('sharpe', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('win_rate', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('total_trades', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('total_pnl', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_eliminated', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('strategy_name', 'tournament_round', name='uq_tournament_strategy')
    )

    # ============================================================
    # Table: trade_records
    # ============================================================
    op.create_table('trade_records',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('exit_price', sa.Float(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('entry_time', sa.DateTime(), nullable=False),
        sa.Column('exit_time', sa.DateTime(), nullable=True),
        sa.Column('pnl', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('pnl_pct', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('strategy', sa.String(length=100), nullable=False),
        sa.Column('stop_loss', sa.Float(), nullable=True),
        sa.Column('take_profit', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default=sa.text("'open'")),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_trade_symbol_time', 'trade_records', ['symbol', 'entry_time'])


def downgrade() -> None:
    op.drop_index('idx_trade_symbol_time', table_name='trade_records')
    op.drop_table('trade_records')
    op.drop_table('tournament_strategies')
    op.drop_table('tournament_records')
    op.drop_table('signals')
    op.drop_table('positions')
    op.drop_table('performance_snapshots')
    op.drop_index('idx_parameter_strategy_name', table_name='parameter_versions')
    op.drop_table('parameter_versions')
    op.drop_table('monitor_rules')
    op.drop_index('idx_alert_level_time', table_name='monitor_alerts')
    op.drop_table('monitor_alerts')
    op.drop_table('model_versions')
    op.drop_index('idx_kline_symbol_period', table_name='klines')
    op.drop_table('klines')
    op.drop_index('idx_contract_category', table_name='contracts')
    op.drop_index('idx_contract_exchange', table_name='contracts')
    op.drop_table('contracts')
    op.drop_table('backtest_results')
