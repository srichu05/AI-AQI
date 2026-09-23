"""Custom Bahdanau (Additive) Attention mechanism for temporal sequence data."""

from typing import Any, Dict, Tuple, Union

import tensorflow as tf


@tf.keras.utils.register_keras_serializable(package="AQI")
class BahdanauAttention(tf.keras.layers.Layer):
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

    def build(self, input_shape: tf.TensorShape) -> None:
        """Builds attention projection weight matrices and bias vectors.

        Args:
            input_shape: Shape tuple/TensorShape of the input sequence tensor
                (batch_size, sequence_length, feature_dim).
        """
        input_shape_list = input_shape.as_list() if hasattr(input_shape, "as_list") else list(input_shape)
        feature_dim = input_shape_list[-1]
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
        self, inputs: tf.Tensor, return_attention_weights: bool = False
    ) -> Union[tf.Tensor, Tuple[tf.Tensor, tf.Tensor]]:
        """Executes attention transformation on temporal inputs.

        Args:
            inputs: 3D sequence tensor of shape (batch, sequence_length, feature_dim).
            return_attention_weights: If True, returns a tuple (context_vector, attention_weights).
                Defaults to False.

        Returns:
            tf.Tensor or Tuple[tf.Tensor, tf.Tensor]:
                - context_vector: 2D tensor of shape (batch, feature_dim).
                - attention_weights (optional): 3D tensor of shape (batch, sequence_length, 1).
        """
        # score shape: (batch, sequence_length, 1)
        score = tf.matmul(tf.tanh(tf.matmul(inputs, self.W) + self.b), self.v)

        # attention_weights shape: (batch, sequence_length, 1)
        attention_weights = tf.nn.softmax(score, axis=1)

        # context_vector shape: (batch, feature_dim)
        context_vector = tf.reduce_sum(inputs * attention_weights, axis=1)

        if return_attention_weights:
            return context_vector, attention_weights

        return context_vector

    def get_config(self) -> Dict[str, Any]:
        """Returns Keras layer configuration dictionary for serialization.

        Returns:
            Dict[str, Any]: Layer config containing 'units'.
        """
        config = super().get_config()
        config.update({"units": self.units})
        return config
