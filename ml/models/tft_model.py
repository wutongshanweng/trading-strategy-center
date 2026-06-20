"""
Temporal Fusion Transformer (TFT)
现代时序预测模型 - 多视野预测 + 可解释性
"""
import warnings

warnings.warn(
    "DEPRECATED: This model is a placeholder implementation. "
    "Use ml.models.sklearn_wrapper.SklearnModel instead.",
    DeprecationWarning, stacklevel=2,
)

import numpy as np
import pandas as pd
from typing import Optional, Tuple, Dict
import pickle
from pathlib import Path


class TFTModel:
    """
    Temporal Fusion Transformer 简化实现

    特性:
    - 多视野预测 (可同时预测多个时间步)
    - 变量选择机制 (自动选择重要特征)
    - 可解释性 (attention权重可视化)
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_heads: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1,
        prediction_horizon: int = 5,
    ):
        """
        Args:
            input_size: 输入特征数量
            hidden_size: 隐藏层大小
            num_heads: 注意力头数
            num_layers: Transformer层数
            dropout: Dropout比率
            prediction_horizon: 预测视野（未来N步）
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.dropout = dropout
        self.prediction_horizon = prediction_horizon

        # 模型参数（简化版，实际需要神经网络）
        self.weights = None
        self.fitted = False

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2,
    ):
        """
        训练TFT模型

        Args:
            X: 输入特征 [samples, sequence_length, features]
            y: 目标值 [samples, prediction_horizon]
            epochs: 训练轮数
            batch_size: 批大小
            validation_split: 验证集比例
        """
        # 简化实现：使用线性回归作为替代
        # 实际应该使用PyTorch/TensorFlow实现完整的TFT

        print(f"Training TFT model...")
        print(f"  Input shape: {X.shape}")
        print(f"  Target shape: {y.shape}")
        print(f"  Epochs: {epochs}")

        # Reshape为2D用于简单线性回归
        X_flat = X.reshape(X.shape[0], -1)

        # 添加偏置项
        X_bias = np.c_[np.ones(X_flat.shape[0]), X_flat]

        # 对每个预测步训练一个模型
        self.weights = []
        for i in range(self.prediction_horizon):
            # 最小二乘法
            w = np.linalg.lstsq(X_bias, y[:, i], rcond=None)[0]
            self.weights.append(w)

        self.fitted = True
        print(f"✓ TFT model trained successfully")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测未来值

        Args:
            X: 输入特征 [samples, sequence_length, features]

        Returns:
            predictions: [samples, prediction_horizon]
        """
        if not self.fitted:
            raise ValueError("Model not fitted. Call fit() first.")

        X_flat = X.reshape(X.shape[0], -1)
        X_bias = np.c_[np.ones(X_flat.shape[0]), X_flat]

        predictions = np.zeros((X.shape[0], self.prediction_horizon))
        for i, w in enumerate(self.weights):
            predictions[:, i] = X_bias @ w

        return predictions

    def get_attention_weights(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """
        获取注意力权重（可解释性）

        Returns:
            attention_weights: 各特征的重要性权重
        """
        if not self.fitted:
            return {}

        # 简化：返回权重的绝对值作为特征重要性
        importance = {}
        for i, w in enumerate(self.weights):
            importance[f'step_{i+1}'] = np.abs(w[1:])  # 排除偏置项

        return importance

    def save(self, path: str):
        """保存模型"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'weights': self.weights,
                'config': {
                    'input_size': self.input_size,
                    'hidden_size': self.hidden_size,
                    'num_heads': self.num_heads,
                    'num_layers': self.num_layers,
                    'dropout': self.dropout,
                    'prediction_horizon': self.prediction_horizon,
                },
                'fitted': self.fitted,
            }, f)
        print(f"✓ Model saved to {path}")

    def load(self, path: str):
        """加载模型"""
        with open(path, 'rb') as f:
            data = pickle.load(f)

        self.weights = data['weights']
        self.fitted = data['fitted']

        # 更新配置
        config = data['config']
        self.input_size = config['input_size']
        self.hidden_size = config['hidden_size']
        self.num_heads = config['num_heads']
        self.num_layers = config['num_layers']
        self.dropout = config['dropout']
        self.prediction_horizon = config['prediction_horizon']

        print(f"✓ Model loaded from {path}")


# 便捷函数

def create_sequences(
    data: pd.DataFrame,
    sequence_length: int,
    prediction_horizon: int,
    target_col: str = 'close',
) -> Tuple[np.ndarray, np.ndarray]:
    """
    创建时序序列数据

    Args:
        data: DataFrame with features
        sequence_length: 输入序列长度
        prediction_horizon: 预测视野
        target_col: 目标列名

    Returns:
        X: [samples, sequence_length, features]
        y: [samples, prediction_horizon]
    """
    features = data.values
    X, y = [], []

    for i in range(len(data) - sequence_length - prediction_horizon + 1):
        X.append(features[i:i+sequence_length])

        # 提取未来N步的目标值
        future_targets = data[target_col].iloc[
            i+sequence_length:i+sequence_length+prediction_horizon
        ].values
        y.append(future_targets)

    return np.array(X), np.array(y)


def train_tft_for_symbol(
    data: pd.DataFrame,
    symbol: str,
    sequence_length: int = 20,
    prediction_horizon: int = 5,
    model_path: Optional[str] = None,
) -> TFTModel:
    """
    为特定品种训练TFT模型

    Example:
        >>> df = get_data('RB')
        >>> model = train_tft_for_symbol(df, 'RB', sequence_length=20, prediction_horizon=5)
        >>> X_test = create_test_sequences(df_test)
        >>> predictions = model.predict(X_test)
    """
    # 准备数据
    X, y = create_sequences(data, sequence_length, prediction_horizon)

    # 创建并训练模型
    model = TFTModel(
        input_size=X.shape[2],
        hidden_size=64,
        num_heads=4,
        prediction_horizon=prediction_horizon,
    )

    model.fit(X, y, epochs=100)

    # 保存模型
    if model_path:
        model.save(model_path)
    elif model_path is None:
        default_path = f"models/tft/{symbol}_tft.pkl"
        model.save(default_path)

    return model
