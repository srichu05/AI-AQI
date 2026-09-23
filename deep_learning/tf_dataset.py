"""TensorFlow tf.data.Dataset pipeline creation module."""

from typing import Dict, Union

import numpy as np
import tensorflow as tf


def create_tf_dataset(
    X_dynamic: np.ndarray,
    X_static_num: np.ndarray,
    X_static_cat: np.ndarray,
    y: np.ndarray,
    batch_size: int = 32,
    is_training: bool = False,
    shuffle_buffer_size: int = 10000,
    cache: bool = True,
) -> tf.data.Dataset:
    """Converts Phase 2A NumPy arrays into an optimized tf.data.Dataset pipeline.

    Format matches multi-input Keras Functional model expectations:
    (
        {
            "dynamic_input": X_dynamic,
            "static_num_input": X_static_num,
            "static_cat_input": X_static_cat
        },
        y
    )

    Args:
        X_dynamic: Dynamic environmental feature array (samples, 7, dynamic_features).
        X_static_num: Static numerical feature array (samples, static_num_features).
        X_static_cat: Static categorical feature array (samples, static_cat_features).
        y: One-hot encoded target array (samples, num_classes).
        batch_size: Batch size for dataset iteration. Defaults to 32.
        is_training: If True, applies shuffling for training data. Defaults to False.
        shuffle_buffer_size: Buffer size for training dataset shuffle. Defaults to 10000.
        cache: If True, caches dataset elements in memory. Defaults to True.

    Returns:
        tf.data.Dataset: Configured, batched, cached, and prefetched dataset pipeline.
    """
    inputs = {
        "dynamic_input": X_dynamic,
        "static_num_input": X_static_num,
        "static_cat_input": X_static_cat,
    }

    dataset = tf.data.Dataset.from_tensor_slices((inputs, y))

    if cache:
        dataset = dataset.cache()

    if is_training:
        actual_buffer_size = min(len(X_dynamic), shuffle_buffer_size)
        dataset = dataset.shuffle(
            buffer_size=actual_buffer_size,
            reshuffle_each_iteration=True,
        )

    dataset = dataset.batch(batch_size)
    dataset = dataset.prefetch(tf.data.AUTOTUNE)

    return dataset


def create_all_tf_datasets(
    data: Dict[str, Dict[str, np.ndarray]],
    batch_size: int = 32,
    shuffle_buffer_size: int = 10000,
    cache: bool = True,
) -> Dict[str, tf.data.Dataset]:
    """Creates tf.data.Dataset pipelines for all dataset splits.

    Shuffles only the training split. Validation and testing splits preserve
    their chronological ordering.

    Args:
        data: Nested dictionary containing tensors for 'train', 'validation', and 'test'.
        batch_size: Batch size for all dataset splits. Defaults to 32.
        shuffle_buffer_size: Shuffle buffer size for the training split. Defaults to 10000.
        cache: Whether to cache datasets. Defaults to True.

    Returns:
        Dict[str, tf.data.Dataset]: Dictionary mapping split names ('train', 'validation',
            'test') to their corresponding tf.data.Dataset instances.
    """
    datasets: Dict[str, tf.data.Dataset] = {}

    for split_name, tensors in data.items():
        is_training = (split_name.lower() == "train")
        datasets[split_name] = create_tf_dataset(
            X_dynamic=tensors["X_dynamic"],
            X_static_num=tensors["X_static_num"],
            X_static_cat=tensors["X_static_cat"],
            y=tensors["y"],
            batch_size=batch_size,
            is_training=is_training,
            shuffle_buffer_size=shuffle_buffer_size,
            cache=cache,
        )

    return datasets
