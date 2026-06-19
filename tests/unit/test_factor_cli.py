"""factor_cli 统一入口 — 单元测试 (CSV 路径, 不依赖仓库/网络)。"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pandas as pd
import pytest

from core.alpha import factor_cli


@pytest.fixture(autouse=True)
def _ensure_factor_registry():
    """每个 CLI 测试前确保因子注册表就绪 (隔离其他测试的 reset 污染)。"""
    from core.alpha.alpha101.factor_registry import FactorRegistry
    reg = FactorRegistry()
    reg.ensure_initialized()
    if not reg.list_all():
        reg.reset(); reg.ensure_initialized()
    yield


@pytest.fixture
def csv_path(tmp_path):
    np.random.seed(3)
    n = 250
    close = pd.Series(100 * (1 + np.random.randn(n) * 0.02).cumprod())
    df = pd.DataFrame({
        "datetime": pd.date_range("2024-01-01", periods=n, freq="D"),
        "open": close * 1.001, "high": close * 1.01, "low": close * 0.99,
        "close": close, "volume": np.random.randint(1e6, 1e7, n),
    })
    p = tmp_path / "data.csv"
    df.to_csv(p, index=False)
    return str(p)


def test_load_data_csv(csv_path):
    df = factor_cli._load_data(None, csv_path)
    assert len(df) == 250 and "close" in df.columns


def test_load_data_requires_source():
    with pytest.raises(SystemExit):
        factor_cli._load_data(None, None)


def test_alpha101_factors_instantiates(csv_path):
    df = factor_cli._load_data(None, csv_path)
    factors = factor_cli._alpha101_factors(df, ["alpha001", "alpha002", "alpha003"])
    assert not factors.empty
    assert factors.shape[1] >= 1   # 至少算出一个因子


def test_cmd_health_csv(csv_path, capsys):
    args = factor_cli.build_parser().parse_args(
        ["health", "--data", csv_path, "--factors", "alpha001,alpha002"])
    args.func(args)
    out = capsys.readouterr().out
    assert "alpha001" in out

def test_cmd_report_outputs(csv_path, tmp_path, capsys):
    html = tmp_path / "r.html"
    js = tmp_path / "r.json"
    args = factor_cli.build_parser().parse_args(
        ["report", "--data", csv_path, "--factors", "alpha001,alpha002,alpha003",
         "--html", str(html), "--json", str(js)])
    args.func(args)
    assert html.exists() and js.exists()


def test_cmd_mine_save(csv_path, tmp_path):
    out = tmp_path / "mined.json"
    args = factor_cli.build_parser().parse_args(
        ["mine", "--data", csv_path, "--generations", "3", "--population", "15",
         "--top", "3", "--save", str(out)])
    args.func(args)
    assert out.exists()


def test_cmd_layered_csv(csv_path, capsys):
    args = factor_cli.build_parser().parse_args(
        ["layered", "--data", csv_path, "--factor", "alpha001", "--quantiles", "5"])
    args.func(args)
    assert "layered" in capsys.readouterr().out


def test_split_helper():
    assert factor_cli._split("a,b, c") == ["a", "b", "c"]
    assert factor_cli._split(None) is None
