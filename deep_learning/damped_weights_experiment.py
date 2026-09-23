"""Phase 2D — Experiment 2: Damped Class Weighting Study.

Trains candidate DL models with alternative damped/capped class weighting strategies
and evaluates them strictly on the 2024 Validation set (both Argmax & Threshold Calibrated).

STRICT DATA INTEGRITY: 2025 Test set is NOT loaded, accessed, or evaluated.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from config.paths import DL_DATA_DIR, EXPERIMENTS_DIR, SAVED_MODELS_DIR, ensure_directories_exist
from deep_learning.architecture import BahdanauAttention, build_model
from deep_learning.dataset_loader import load_all_tensors
from deep_learning.tf_dataset import create_all_tf_datasets, create_tf_dataset
from deep_learning.threshold_calibration import apply_thresholds, compute_evaluation_metrics, optimize_thresholds_validation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DAMPED_DIR = EXPERIMENTS_DIR / "phase2d" / "damped_weights"


class CorrectedMacroF1Callback(tf.keras.callbacks.Callback):
    """Keras Callback that correctly evaluates epoch-level Train and Validation Macro F1.

    Fixes ISSUE-DL-001 by using un-shuffled datasets for both training evaluation and validation.
    """

    def __init__(
        self,
        train_eval_ds: tf.data.Dataset,
        val_dataset: tf.data.Dataset,
        y_train_eval_true: np.ndarray,
        y_val_true: np.ndarray,
    ) -> None:
        super().__init__()
        self.train_eval_ds = train_eval_ds
        self.val_dataset = val_dataset
        self.y_train_eval_true = y_train_eval_true
        self.y_val_true = y_val_true
        self.history_records: List[Dict[str, Any]] = []

    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, Any]] = None) -> None:
        if logs is None:
            logs = {}

        # Validation set evaluation (un-shuffled)
        y_pred_val = self.model.predict(self.val_dataset, verbose=0)
        true_cls_val = np.argmax(self.y_val_true, axis=1)
        pred_cls_val = np.argmax(y_pred_val, axis=1)

        val_macro_f1 = float(f1_score(true_cls_val, pred_cls_val, average="macro", zero_division=0))
        val_acc = float(accuracy_score(true_cls_val, pred_cls_val))

        # Train set evaluation (un-shuffled sample slice)
        y_pred_tr = self.model.predict(self.train_eval_ds, verbose=0)
        true_cls_tr = np.argmax(self.y_train_eval_true, axis=1)
        pred_cls_tr = np.argmax(y_pred_tr, axis=1)

        tr_macro_f1 = float(f1_score(true_cls_tr, pred_cls_tr, average="macro", zero_division=0))
        tr_acc = float(accuracy_score(true_cls_tr, pred_cls_tr))

        logs["val_macro_f1"] = val_macro_f1
        logs["train_macro_f1"] = tr_macro_f1

        lr_val = 0.0
        if hasattr(self.model.optimizer, "learning_rate"):
            lr_obj = self.model.optimizer.learning_rate
            lr_val = float(lr_obj.numpy() if hasattr(lr_obj, "numpy") else lr_obj)

        record = {
            "epoch": epoch + 1,
            "loss": float(logs.get("loss", 0.0)),
            "val_loss": float(logs.get("val_loss", 0.0)),
            "accuracy": tr_acc,
            "val_accuracy": val_acc,
            "macro_f1": tr_macro_f1,
            "val_macro_f1": val_macro_f1,
            "learning_rate": lr_val,
        }
        self.history_records.append(record)

        msg = (
            f" Epoch {epoch + 1:03d} -> "
            f"Loss: {record['loss']:.4f} | Val Loss: {record['val_loss']:.4f} | "
            f"Train Macro F1: {tr_macro_f1:.4f} | Val Macro F1: {val_macro_f1:.4f} | "
            f"LR: {lr_val:.6f}"
        )
        logger.info(msg)


def get_weight_strategies() -> Dict[str, Dict[int, float]]:
    """Defines candidate class weighting strategies for Experiment 2."""
    orig_w = {0: 0.70134, 1: 0.47568, 2: 0.79273, 3: 5.78898, 4: 26.51672}

    sqrt_w = {k: float(np.sqrt(v)) for k, v in orig_w.items()}
    pow75_w = {k: float(v**0.75) for k, v in orig_w.items()}
    capped_w = {k: float(min(v, 10.0)) for k, v in orig_w.items()}

    return {
        "original_weights": orig_w,
        "sqrt_weights": sqrt_w,
        "pow75_weights": pow75_w,
        "capped_weights": capped_w,
    }


def train_candidate_model(
    strategy_name: str,
    class_weights: Dict[int, float],
    tensors: Dict[str, Dict[str, np.ndarray]],
    datasets: Dict[str, tf.data.Dataset],
    output_dir: Path,
    epochs: int = 40,
    seed: int = 42,
) -> Tuple[tf.keras.Model, List[Dict[str, Any]]]:
    """Trains a candidate DL model with specified class weights using seed 42."""
    tf.keras.utils.set_random_seed(seed)
    np.random.seed(seed)

    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "best_model.keras"

    # Build fresh un-trained model architecture
    model = build_model(
        sequence_length=7,
        dynamic_features=24,
        static_num_features=16,
        conv_filters=64,
        bilstm_units=64,
        attention_units=64,
        dynamic_proj_units=64,
        static_num_dense_1=64,
        static_num_dense_2=32,
        static_cat_dense=16,
        fusion_dense_1=128,
        fusion_dense_2=64,
        dropout_rate=0.3,
        num_classes=5,
        model_name=f"DL_{strategy_name}",
    )

    optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3)
    loss_fn = tf.keras.losses.CategoricalCrossentropy()

    model.compile(
        optimizer=optimizer,
        loss=loss_fn,
        metrics=["accuracy"],
    )

    # Build un-shuffled train eval dataset for accurate train Macro F1 logging (4,352 samples)
    n_train_eval = 4352
    train_eval_ds = create_tf_dataset(
        X_dynamic=tensors["train"]["X_dynamic"][:n_train_eval],
        X_static_num=tensors["train"]["X_static_num"][:n_train_eval],
        X_static_cat=tensors["train"]["X_static_cat"][:n_train_eval],
        y=tensors["train"]["y"][:n_train_eval],
        batch_size=32,
        is_training=False,
        cache=True,
    )
    y_train_eval_true = tensors["train"]["y"][:n_train_eval]
    y_val_true = tensors["validation"]["y"]

    macro_f1_cb = CorrectedMacroF1Callback(
        train_eval_ds=train_eval_ds,
        val_dataset=datasets["validation"],
        y_train_eval_true=y_train_eval_true,
        y_val_true=y_val_true,
    )

    checkpoint_cb = tf.keras.callbacks.ModelCheckpoint(
        filepath=checkpoint_path,
        monitor="val_macro_f1",
        mode="max",
        save_best_only=True,
        verbose=1,
    )

    early_stop_cb = tf.keras.callbacks.EarlyStopping(
        monitor="val_macro_f1",
        mode="max",
        patience=10,
        restore_best_weights=True,
        verbose=1,
    )

    reduce_lr_cb = tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_macro_f1",
        mode="max",
        factor=0.5,
        patience=4,
        min_lr=1e-6,
        verbose=1,
    )

    callbacks = [macro_f1_cb, checkpoint_cb, early_stop_cb, reduce_lr_cb]

    logger.info(f"--- Training {strategy_name} for up to {epochs} epochs ---")
    logger.info(f"Class Weights: {class_weights}")

    model.fit(
        datasets["train"],
        validation_data=datasets["validation"],
        epochs=epochs,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=0,
    )

    # Save training history CSV
    history_records = macro_f1_cb.history_records
    history_csv = output_dir / "training_history.csv"
    if history_records:
        fieldnames = list(history_records[0].keys())
        with open(history_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(history_records)

    # Plot training curves
    plot_curves(history_records, output_dir / "training_curves.png", strategy_name)

    # Load best checkpoint
    best_model = tf.keras.models.load_model(
        checkpoint_path,
        custom_objects={"BahdanauAttention": BahdanauAttention},
        safe_mode=False,
        compile=False,
    )

    return best_model, history_records


def plot_curves(history_records: List[Dict[str, Any]], output_path: Path, strategy_name: str) -> None:
    """Plots training and validation loss, accuracy, and Macro F1 curves."""
    epochs = [r["epoch"] for r in history_records]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), dpi=150)
    fig.suptitle(f"Training Curves — {strategy_name}", fontsize=14, fontweight="bold")

    axes[0].plot(epochs, [r["loss"] for r in history_records], label="Train Loss", color="#1f77b4")
    axes[0].plot(epochs, [r["val_loss"] for r in history_records], label="Val Loss", color="#ff7f0e")
    axes[0].set_title("Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].grid(True, linestyle="--", alpha=0.5)
    axes[0].legend()

    axes[1].plot(epochs, [r["accuracy"] for r in history_records], label="Train Acc", color="#1f77b4")
    axes[1].plot(epochs, [r["val_accuracy"] for r in history_records], label="Val Acc", color="#ff7f0e")
    axes[1].set_title("Accuracy")
    axes[1].set_xlabel("Epoch")
    axes[1].grid(True, linestyle="--", alpha=0.5)
    axes[1].legend()

    axes[2].plot(epochs, [r["macro_f1"] for r in history_records], label="Train Macro F1", color="#1f77b4")
    axes[2].plot(epochs, [r["val_macro_f1"] for r in history_records], label="Val Macro F1", color="#2ca02c", linewidth=2)
    axes[2].set_title("Macro F1-Score")
    axes[2].set_xlabel("Epoch")
    axes[2].grid(True, linestyle="--", alpha=0.5)
    axes[2].legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def run_damped_weights_study() -> Dict[str, Any]:
    """Executes the full Damped Class Weighting experiment suite."""
    ensure_directories_exist()
    DAMPED_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Loading Phase 2A NumPy Tensors (Train & Validation ONLY)...")
    tensors = load_all_tensors(DL_DATA_DIR)
    datasets = create_all_tf_datasets(tensors, batch_size=32, cache=True)

    y_val_true = tensors["validation"]["y"]
    y_val_true_cls = np.argmax(y_val_true, axis=1)

    strategies = get_weight_strategies()
    results_summary: Dict[str, Any] = {}

    for strat_name, weights in strategies.items():
        logger.info(f"\n=======================================================")
        logger.info(f" Running Strategy: {strat_name}")
        logger.info(f"=======================================================")

        strat_dir = DAMPED_DIR / strat_name
        model, history = train_candidate_model(
            strategy_name=strat_name,
            class_weights=weights,
            tensors=tensors,
            datasets=datasets,
            output_dir=strat_dir,
            epochs=40,
            seed=42,
        )

        # 1. Evaluate on Validation Set probabilities
        val_probs = model.predict(datasets["validation"], verbose=0)

        # 2. Argmax Baseline Metrics (thresholds = [1,1,1,1,1])
        base_preds = apply_thresholds(val_probs, [1.0, 1.0, 1.0, 1.0, 1.0])
        base_metrics = compute_evaluation_metrics(y_val_true_cls, base_preds, 5)

        # 3. Validation Threshold Calibration on this model's probabilities
        best_tau, cal_metrics, _ = optimize_thresholds_validation(val_probs, y_val_true, 5, seed=42)

        # Save strategy metrics JSON
        strat_metrics = {
            "strategy_name": strat_name,
            "weights": weights,
            "argmax_validation_metrics": base_metrics,
            "calibrated_validation_metrics": cal_metrics,
            "calibrated_thresholds": [float(v) for v in best_tau],
        }

        with open(strat_dir / "validation_metrics.json", "w", encoding="utf-8") as f:
            json.dump(strat_metrics, f, indent=2)

        # Save confusion matrix CSV
        cm_csv = strat_dir / "confusion_matrix.csv"
        np.savetxt(cm_csv, np.array(cal_metrics["confusion_matrix"]), fmt="%d", delimiter=",")

        results_summary[strat_name] = {
            "argmax_val_macro_f1": base_metrics["overall_metrics"]["macro_f1"],
            "calibrated_val_macro_f1": cal_metrics["overall_metrics"]["macro_f1"],
            "argmax_val_acc": base_metrics["overall_metrics"]["accuracy"],
            "calibrated_val_acc": cal_metrics["overall_metrics"]["accuracy"],
            "best_thresholds": [float(v) for v in best_tau],
            "class_3_f1_argmax": base_metrics["per_class_metrics"]["3"]["f1_score"],
            "class_3_f1_calibrated": cal_metrics["per_class_metrics"]["3"]["f1_score"],
            "class_3_recall_calibrated": cal_metrics["per_class_metrics"]["3"]["recall"],
            "class_4_f1_argmax": base_metrics["per_class_metrics"]["4"]["f1_score"],
            "class_4_f1_calibrated": cal_metrics["per_class_metrics"]["4"]["f1_score"],
            "class_4_recall_calibrated": cal_metrics["per_class_metrics"]["4"]["recall"],
        }

    # Save summary JSON
    summary_path = DAMPED_DIR / "damped_weights_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    logger.info("=======================================================")
    logger.info(" Damped Class Weighting Experiment Suite Completed!")
    logger.info("=======================================================")

    return results_summary


if __name__ == "__main__":
    run_damped_weights_study()
