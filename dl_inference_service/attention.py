"""Standalone custom Bahdanau (additive) temporal attention layer for Keras 3.

Designed for standalone deployment on Hugging Face Spaces without dependency on
the full AI-AQI training codebase or GIS/database dependencies.
"""

from typing import Any, Dict, Tuple, Union
import keras
from keras import ops


@keras.saving.register_keras_serializable(package="AQI")
class BahdanauAttention(keras.layers.Layer):
    """Bahdanau (additive) temporal attention layer for 3D sequence tensors.

    Computes alignment scores across sequence time steps to produce a context vector:
        1. score = v^T * tanh(W * h + b)
        2. weights = softmax(score, axis=1)
        3. context = sum(weights * h, axis=1)

    Args:
        units: Projection dimension for attention score computation. Defaults to 64.
        **kwargs: Standard Keras layer keyword arguments.
    """

    def __init__(self, units: int = 64, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.units = units

    def build(self, input_shape: Any) -> None:
        """Builds projection weight matrices and bias vectors."""
        feature_dim = input_shape[-1]
        if feature_dim is None:
            raise ValueError("Input feature dimension must be static and specified.")

        self.W = self.add_weight(
            name="W",
            shape=(feature_dim, self.units),
            initializer="glorot_uniform",
            trainable=True,
        )
        self.b = self.add_weight(
            name="b",
            shape=(self.units,),
            initializer="zeros",
            trainable=True,
        )
        self.v = self.add_weight(
            name="v",
            shape=(self.units, 1),
            initializer="glorot_uniform",
            trainable=True,
        )
        super().build(input_shape)

    def call(
        self, inputs: Any, return_attention_weights: bool = False
    ) -> Union[Any, Tuple[Any, Any]]:
        """Executes attention transformation on temporal inputs.

        Args:
            inputs: 3D sequence tensor of shape (batch, sequence_length, feature_dim).
            return_attention_weights: If True, returns (context_vector, attention_weights).

        Returns:
            context_vector or tuple of (context_vector, attention_weights).
        """
        # score shape: (batch, sequence_length, 1)
        score = ops.matmul(ops.tanh(ops.matmul(inputs, self.W) + self.b), self.v)

        # attention_weights shape: (batch, sequence_length, 1)
        attention_weights = ops.softmax(score, axis=1)

        # context_vector shape: (batch, feature_dim)
        context_vector = ops.sum(inputs * attention_weights, axis=1)

        if return_attention_weights:
            return context_vector, attention_weights

        return context_vector

    def get_config(self) -> Dict[str, Any]:
        """Returns Keras layer configuration dictionary for serialization."""
        config = super().get_config()
        config.update({"units": self.units})
        return config
