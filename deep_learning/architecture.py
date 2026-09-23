"""Hybrid Multi-Input Deep Learning Architecture for Air Quality Index (AQI) Risk Prediction."""

from typing import Optional

import tensorflow as tf
from deep_learning.attention import BahdanauAttention


def build_model(
    sequence_length: int = 7,
    dynamic_features: int = 24,
    static_num_features: int = 16,
    district_vocab_size: int = 32,
    district_embed_dim: int = 16,
    land_use_vocab_size: int = 8,
    land_use_embed_dim: int = 4,
    urban_rural_vocab_size: int = 4,
    urban_rural_embed_dim: int = 2,
    conv_filters: int = 64,
    conv_kernel_size: int = 3,
    pool_size: int = 2,
    bilstm_units: int = 64,
    attention_units: int = 64,
    dynamic_proj_units: int = 64,
    static_num_dense_1: int = 64,
    static_num_dense_2: int = 32,
    static_cat_dense: int = 16,
    fusion_dense_1: int = 128,
    fusion_dense_2: int = 64,
    dropout_rate: float = 0.3,
    num_classes: int = 5,
    model_name: str = "AI_AQI_Hybrid_Model",
) -> tf.keras.Model:
    """Builds and constructs the hybrid multi-input Keras Functional AQI prediction model.

    The architecture consists of 3 independent input branches:
        1. Dynamic Temporal Branch: Conv1D -> BatchNorm -> ReLU -> MaxPool1D -> BiLSTM -> Bahdanau Attention -> Dense projection
        2. Static Numerical Branch: Dense -> BatchNorm -> ReLU -> Dropout -> Dense projection
        3. Static Categorical Branch: Sliced categorical IDs -> Embedding layers -> Concatenate -> Dense projection

    Followed by a Fusion Network:
        Concatenate -> Dense -> BatchNorm -> ReLU -> Dropout -> Dense -> Softmax Output.

    Args:
        sequence_length: Temporal sequence window size. Defaults to 7.
        dynamic_features: Number of dynamic temporal features per timestep. Defaults to 24.
        static_num_features: Number of continuous static numerical features. Defaults to 16.
        district_vocab_size: Vocabulary size for district_id embedding. Defaults to 32.
        district_embed_dim: Embedding dimension for district_id. Defaults to 16.
        land_use_vocab_size: Vocabulary size for land_use_id embedding. Defaults to 8.
        land_use_embed_dim: Embedding dimension for land_use_id. Defaults to 4.
        urban_rural_vocab_size: Vocabulary size for urban_rural_id embedding. Defaults to 4.
        urban_rural_embed_dim: Embedding dimension for urban_rural_id. Defaults to 2.
        conv_filters: Number of filters in Conv1D layer. Defaults to 64.
        conv_kernel_size: Kernel size for Conv1D layer. Defaults to 3.
        pool_size: Pooling window size for MaxPooling1D. Defaults to 2.
        bilstm_units: Number of hidden units per LSTM direction. Defaults to 64.
        attention_units: Projection units for Bahdanau Attention mechanism. Defaults to 64.
        dynamic_proj_units: Output dimension for Dynamic Branch projection. Defaults to 64.
        static_num_dense_1: First hidden units for Static Numerical Branch. Defaults to 64.
        static_num_dense_2: Projection dimension for Static Numerical Branch. Defaults to 32.
        static_cat_dense: Projection dimension for Static Categorical Branch. Defaults to 16.
        fusion_dense_1: First hidden dimension in Fusion MLP. Defaults to 128.
        fusion_dense_2: Second hidden dimension in Fusion MLP. Defaults to 64.
        dropout_rate: Dropout regularization probability rate. Defaults to 0.3.
        num_classes: Number of AQI risk classes for target output. Defaults to 5.
        model_name: Name of the constructed Keras Model. Defaults to "AI_AQI_Hybrid_Model".

    Returns:
        tf.keras.Model: Uncompiled Keras Functional API Model instance.
    """
    # -------------------------------------------------------------------------
    # Input Layer Definitions
    # -------------------------------------------------------------------------
    dynamic_input = tf.keras.layers.Input(
        shape=(sequence_length, dynamic_features),
        dtype=tf.float32,
        name="dynamic_input",
    )
    static_num_input = tf.keras.layers.Input(
        shape=(static_num_features,),
        dtype=tf.float32,
        name="static_num_input",
    )
    static_cat_input = tf.keras.layers.Input(
        shape=(3,),
        dtype=tf.int32,
        name="static_cat_input",
    )

    # -------------------------------------------------------------------------
    # Branch 1: Dynamic Temporal Branch
    # -------------------------------------------------------------------------
    x_dyn = tf.keras.layers.Conv1D(
        filters=conv_filters,
        kernel_size=conv_kernel_size,
        padding="same",
        name="dyn_conv1d",
    )(dynamic_input)
    x_dyn = tf.keras.layers.BatchNormalization(name="dyn_conv_bn")(x_dyn)
    x_dyn = tf.keras.layers.Activation("relu", name="dyn_conv_relu")(x_dyn)
    x_dyn = tf.keras.layers.MaxPooling1D(
        pool_size=pool_size,
        padding="same",
        name="dyn_maxpool",
    )(x_dyn)
    x_dyn = tf.keras.layers.Bidirectional(
        tf.keras.layers.LSTM(bilstm_units, return_sequences=True),
        name="dyn_bilstm",
    )(x_dyn)
    x_dyn = BahdanauAttention(units=attention_units, name="dyn_attention")(x_dyn)
    dynamic_vector = tf.keras.layers.Dense(
        units=dynamic_proj_units,
        activation="relu",
        name="dyn_projection",
    )(x_dyn)

    # -------------------------------------------------------------------------
    # Branch 2: Static Numerical Branch
    # -------------------------------------------------------------------------
    x_snum = tf.keras.layers.Dense(
        units=static_num_dense_1,
        name="snum_dense_1",
    )(static_num_input)
    x_snum = tf.keras.layers.BatchNormalization(name="snum_bn")(x_snum)
    x_snum = tf.keras.layers.Activation("relu", name="snum_relu")(x_snum)
    x_snum = tf.keras.layers.Dropout(rate=dropout_rate, name="snum_dropout")(x_snum)
    static_num_vector = tf.keras.layers.Dense(
        units=static_num_dense_2,
        activation="relu",
        name="snum_projection",
    )(x_snum)

    # -------------------------------------------------------------------------
    # Branch 3: Static Categorical Branch
    # -------------------------------------------------------------------------
    district_id = tf.keras.layers.Lambda(
        lambda x: x[:, 0],
        name="district_id_slice",
    )(static_cat_input)
    land_use_id = tf.keras.layers.Lambda(
        lambda x: x[:, 1],
        name="land_use_id_slice",
    )(static_cat_input)
    urban_rural_id = tf.keras.layers.Lambda(
        lambda x: x[:, 2],
        name="urban_rural_id_slice",
    )(static_cat_input)

    district_emb = tf.keras.layers.Embedding(
        input_dim=district_vocab_size,
        output_dim=district_embed_dim,
        name="district_embedding",
    )(district_id)
    district_flat = tf.keras.layers.Flatten(name="district_flatten")(district_emb)

    land_use_emb = tf.keras.layers.Embedding(
        input_dim=land_use_vocab_size,
        output_dim=land_use_embed_dim,
        name="land_use_embedding",
    )(land_use_id)
    land_use_flat = tf.keras.layers.Flatten(name="land_use_flatten")(land_use_emb)

    urban_rural_emb = tf.keras.layers.Embedding(
        input_dim=urban_rural_vocab_size,
        output_dim=urban_rural_embed_dim,
        name="urban_rural_embedding",
    )(urban_rural_id)
    urban_rural_flat = tf.keras.layers.Flatten(name="urban_rural_flatten")(urban_rural_emb)

    cat_concat = tf.keras.layers.Concatenate(name="scat_concat")(
        [district_flat, land_use_flat, urban_rural_flat]
    )
    static_cat_vector = tf.keras.layers.Dense(
        units=static_cat_dense,
        activation="relu",
        name="scat_projection",
    )(cat_concat)

    # -------------------------------------------------------------------------
    # Fusion Network
    # -------------------------------------------------------------------------
    fusion_concat = tf.keras.layers.Concatenate(name="fusion_concat")(
        [dynamic_vector, static_num_vector, static_cat_vector]
    )
    x_fusion = tf.keras.layers.Dense(
        units=fusion_dense_1,
        name="fusion_dense_1",
    )(fusion_concat)
    x_fusion = tf.keras.layers.BatchNormalization(name="fusion_bn")(x_fusion)
    x_fusion = tf.keras.layers.Activation("relu", name="fusion_relu")(x_fusion)
    x_fusion = tf.keras.layers.Dropout(rate=dropout_rate, name="fusion_dropout")(x_fusion)
    x_fusion = tf.keras.layers.Dense(
        units=fusion_dense_2,
        activation="relu",
        name="fusion_dense_2",
    )(x_fusion)

    outputs = tf.keras.layers.Dense(
        units=num_classes,
        activation="softmax",
        name="aqi_output",
    )(x_fusion)

    # -------------------------------------------------------------------------
    # Model Construction
    # -------------------------------------------------------------------------
    model = tf.keras.Model(
        inputs={
            "dynamic_input": dynamic_input,
            "static_num_input": static_num_input,
            "static_cat_input": static_cat_input,
        },
        outputs=outputs,
        name=model_name,
    )

    return model
