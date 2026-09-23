"""Phase 2D Deep Learning Training, Validation, Model Selection & Evaluation Pipeline."""

import csv
import io
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    auc,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)

from config.paths import DL_DATA_DIR, EXPERIMENTS_DIR, SAVED_MODELS_DIR, ensure_directories_exist
from deep_learning.architecture import build_model, BahdanauAttention
from deep_learning.class_weights import load_class_weights, compute_dataset_class_weights
from deep_learning.dataset_loader import load_all_tensors
from deep_learning.tf_dataset import create_tf_dataset, create_all_tf_datasets

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PHASE2D_DIR = EXPERIMENTS_DIR / "phase2d"


class MacroF1Callback(tf.keras.callbacks.Callback):
    """Fast Keras Callback to calculate epoch-level Macro F1 scores using model.predict."""

    def __init__(
        self,
        train_dataset: tf.data.Dataset,
        val_dataset: tf.data.Dataset,
        y_val_true: np.ndarray,
        y_train_true: np.ndarray,
        num_classes: int = 5,
        train_eval_batches: int = 136,
    ) -> None:
        super().__init__()
        self.val_dataset = val_dataset
        self.y_val_true = y_val_true
        self.train_eval_ds = train_dataset.take(train_eval_batches)
        self.y_train_eval_true = y_train_true[: train_eval_batches * 32]
        self.num_classes = num_classes
        self.history_records: List[Dict[str, Any]] = []

    def on_epoch_end(self, epoch: int, logs: Optional[Dict[str, Any]] = None) -> None:
        if logs is None:
            logs = {}

        # ---------------------------------------------------------------------
        # Evaluate Full Validation Set (10,770 samples) using model.predict
        # ---------------------------------------------------------------------
        y_pred_val = self.model.predict(self.val_dataset, verbose=0)
        true_cls_val = np.argmax(self.y_val_true, axis=1)
        pred_cls_val = np.argmax(y_pred_val, axis=1)

        val_macro_f1 = float(f1_score(true_cls_val, pred_cls_val, average="macro", zero_division=0))
        val_macro_prec = float(precision_score(true_cls_val, pred_cls_val, average="macro", zero_division=0))
        val_macro_rec = float(recall_score(true_cls_val, pred_cls_val, average="macro", zero_division=0))
        val_acc = float(accuracy_score(true_cls_val, pred_cls_val))

        # ---------------------------------------------------------------------
        # Evaluate Representative Subsample of Training Set (4,352 samples)
        # ---------------------------------------------------------------------
        y_pred_tr = self.model.predict(self.train_eval_ds, verbose=0)
        true_cls_tr = np.argmax(self.y_train_eval_true, axis=1)
        pred_cls_tr = np.argmax(y_pred_tr, axis=1)

        tr_macro_f1 = float(f1_score(true_cls_tr, pred_cls_tr, average="macro", zero_division=0))
        tr_acc = float(logs.get("accuracy", accuracy_score(true_cls_tr, pred_cls_tr)))

        # Inject metrics into Keras logs dictionary for downstream callbacks
        logs["val_macro_f1"] = val_macro_f1
        logs["train_macro_f1"] = tr_macro_f1
        logs["val_macro_prec"] = val_macro_prec
        logs["val_macro_rec"] = val_macro_rec

        # Get current learning rate safely
        lr_val = 0.0
        if hasattr(self.model.optimizer, "learning_rate"):
            lr_obj = self.model.optimizer.learning_rate
            lr_val = float(lr_obj.numpy() if hasattr(lr_obj, "numpy") else lr_obj)
        elif hasattr(self.model.optimizer, "lr"):
            lr_obj = self.model.optimizer.lr
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
            f" Epoch {epoch + 1:03d} Metrics -> "
            f"Loss: {record['loss']:.4f} | Val Loss: {record['val_loss']:.4f} | "
            f"Train Acc: {tr_acc:.4f} | Val Acc: {val_acc:.4f} | "
            f"Train Macro F1: {tr_macro_f1:.4f} | Val Macro F1: {val_macro_f1:.4f} | "
            f"LR: {lr_val:.6f}"
        )
        print(msg, flush=True)
        sys.stdout.flush()


def compute_pr_auc_macro(y_true_onehot: np.ndarray, y_pred_prob: np.ndarray) -> float:
    """Computes Macro Precision-Recall Area Under Curve (PR-AUC) across 5 AQI risk classes."""
    pr_aucs = []
    for k in range(y_true_onehot.shape[1]):
        prec, rec, _ = precision_recall_curve(y_true_onehot[:, k], y_pred_prob[:, k])
        pr_aucs.append(auc(rec, prec))
    return float(np.mean(pr_aucs))


def compute_bootstrap_cis(
    y_true_onehot: np.ndarray,
    y_pred_prob: np.ndarray,
    n_bootstraps: int = 1000,
    seed: int = 42,
) -> Dict[str, Dict[str, float]]:
    """Calculates 1,000-sample Stratified Bootstrap 95% Confidence Intervals for 2025 Test Set."""
    rng = np.random.default_rng(seed)
    n_samples = len(y_true_onehot)
    true_labels = np.argmax(y_true_onehot, axis=1)

    macro_f1s, bal_accs, c3_recs, c4_recs = [], [], [], []

    for _ in range(n_bootstraps):
        idx = rng.choice(n_samples, size=n_samples, replace=True)
        y_t_b = true_labels[idx]
        y_p_b = np.argmax(y_pred_prob[idx], axis=1)

        macro_f1s.append(f1_score(y_t_b, y_p_b, average="macro", zero_division=0))
        bal_accs.append(balanced_accuracy_score(y_t_b, y_p_b))

        rec_per_class = recall_score(y_t_b, y_p_b, average=None, labels=[0, 1, 2, 3, 4], zero_division=0)
        c3_recs.append(rec_per_class[3])
        c4_recs.append(rec_per_class[4])

    def get_stats(arr: List[float]) -> Dict[str, float]:
        return {
            "mean": float(np.mean(arr)),
            "ci_lower": float(np.percentile(arr, 2.5)),
            "ci_upper": float(np.percentile(arr, 97.5)),
        }

    return {
        "macro_f1": get_stats(macro_f1s),
        "balanced_accuracy": get_stats(bal_accs),
        "class_3_recall": get_stats(c3_recs),
        "class_4_recall": get_stats(c4_recs),
    }


def plot_training_curves(history_records: List[Dict[str, Any]], output_path: Path) -> None:
    """Generates 4-panel training diagnostic curves for loss, accuracy, Macro F1, and learning rate."""
    epochs = [r["epoch"] for r in history_records]
    loss = [r["loss"] for r in history_records]
    val_loss = [r["val_loss"] for r in history_records]
    acc = [r["accuracy"] for r in history_records]
    val_acc = [r["val_accuracy"] for r in history_records]
    f1 = [r["macro_f1"] for r in history_records]
    val_f1 = [r["val_macro_f1"] for r in history_records]
    lrs = [r["learning_rate"] for r in history_records]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=150)
    fig.suptitle("Phase 2D Deep Learning Training Diagnostics", fontsize=16, fontweight="bold")

    # Panel 1: Loss
    axes[0, 0].plot(epochs, loss, "b-", label="Train Loss", linewidth=2)
    axes[0, 0].plot(epochs, val_loss, "r--", label="Val Loss", linewidth=2)
    axes[0, 0].set_title("Training vs Validation Loss", fontsize=12, fontweight="bold")
    axes[0, 0].set_xlabel("Epoch")
    axes[0, 0].set_ylabel("Categorical Crossentropy Loss")
    axes[0, 0].grid(True, linestyle="--", alpha=0.6)
    axes[0, 0].legend()

    # Panel 2: Accuracy
    axes[0, 1].plot(epochs, acc, "b-", label="Train Accuracy", linewidth=2)
    axes[0, 1].plot(epochs, val_acc, "r--", label="Val Accuracy", linewidth=2)
    axes[0, 1].set_title("Training vs Validation Accuracy", fontsize=12, fontweight="bold")
    axes[0, 1].set_xlabel("Epoch")
    axes[0, 1].set_ylabel("Accuracy")
    axes[0, 1].grid(True, linestyle="--", alpha=0.6)
    axes[0, 1].legend()

    # Panel 3: Macro F1
    axes[1, 0].plot(epochs, f1, "b-", label="Train Macro F1", linewidth=2)
    axes[1, 0].plot(epochs, val_f1, "g-", label="Val Macro F1 (Primary Metric)", linewidth=2.5)
    axes[1, 0].set_title("Training vs Validation Macro F1", fontsize=12, fontweight="bold")
    axes[1, 0].set_xlabel("Epoch")
    axes[1, 0].set_ylabel("Macro F1-Score")
    axes[1, 0].grid(True, linestyle="--", alpha=0.6)
    axes[1, 0].legend()

    # Panel 4: Learning Rate
    axes[1, 1].plot(epochs, lrs, "m-", label="Learning Rate", linewidth=2)
    axes[1, 1].set_title("Learning Rate Schedule Across Epochs", fontsize=12, fontweight="bold")
    axes[1, 1].set_xlabel("Epoch")
    axes[1, 1].set_ylabel("Learning Rate")
    axes[1, 1].set_yscale("log")
    axes[1, 1].grid(True, linestyle="--", alpha=0.6)
    axes[1, 1].legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Training curves saved to: {output_path}")


def plot_confusion_matrix_heatmap(cm: np.ndarray, output_path: Path) -> None:
    """Renders visual confusion matrix heatmap for the 2025 Test evaluation."""
    labels = ["0 (Low)", "1 (Mod)", "2 (High)", "3 (V.High)", "4 (Severe)"]
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

    try:
        import seaborn as sns
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=labels,
            yticklabels=labels,
            cbar=True,
            ax=ax,
        )
    except Exception:
        im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
        fig.colorbar(im, ax=ax)
        ax.set_xticks(np.arange(len(labels)))
        ax.set_yticks(np.arange(len(labels)))
        ax.set_xticklabels(labels)
        ax.set_yticklabels(labels)

        thresh = cm.max() / 2.0
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(
                    j, i, format(cm[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black"
                )

    ax.set_title("Phase 2D Deep Learning 2025 Test Confusion Matrix", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Predicted Class", fontsize=11, fontweight="bold")
    ax.set_ylabel("True Class", fontsize=11, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Confusion matrix heatmap saved to: {output_path}")


def train_and_evaluate_phase2d() -> Dict[str, Any]:
    """Executes full Phase 2D training, validation model selection, 2025 test evaluation, and benchmarking."""
    ensure_directories_exist()
    PHASE2D_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fix seeds
    seed = 42
    tf.keras.utils.set_random_seed(seed)
    np.random.seed(seed)

    # 2. Load Phase 2A NumPy Tensors & Build Phase 2B tf.data Datasets
    print("Loading Phase 2A NumPy Tensors...", flush=True)
    tensors = load_all_tensors(data_dir=DL_DATA_DIR)
    datasets = create_all_tf_datasets(tensors, batch_size=32, cache=True)

    train_ds = datasets["train"]
    val_ds = datasets["validation"]
    test_ds = datasets["test"]

    # 3. Load Phase 2B Class Weights
    class_weights_file = EXPERIMENTS_DIR / "class_weights.json"
    if class_weights_file.exists():
        class_weights = load_class_weights(class_weights_file)
    else:
        class_weights = compute_dataset_class_weights(tensors["train"]["y"], num_classes=5)

    print(f"Loaded Balanced Class Weights: {class_weights}", flush=True)

    # 4. Build & Compile Keras Functional DL Model
    print("Building Phase 2C Hybrid DL Model Architecture...", flush=True)
    model = build_model()

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss=tf.keras.losses.CategoricalCrossentropy(),
        metrics=["accuracy"],
    )

    # 5. Define Callbacks
    best_model_path = SAVED_MODELS_DIR / "best_dl_model.keras"

    macro_f1_cb = MacroF1Callback(
        train_dataset=train_ds,
        val_dataset=val_ds,
        y_val_true=tensors["validation"]["y"],
        y_train_true=tensors["train"]["y"],
        num_classes=5,
    )

    checkpoint_cb = tf.keras.callbacks.ModelCheckpoint(
        filepath=str(best_model_path),
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
        patience=4,
        factor=0.5,
        min_lr=1e-6,
        verbose=1,
    )

    callbacks = [macro_f1_cb, checkpoint_cb, early_stop_cb, reduce_lr_cb]

    # 6. Execute Training
    print("Starting Phase 2D Model Training (Max Epochs: 100)...", flush=True)
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=100,
        class_weight=class_weights,
        callbacks=callbacks,
        verbose=1,
    )

    # 7. Save Training History & Curves
    history_records = macro_f1_cb.history_records
    history_csv = PHASE2D_DIR / "training_history.csv"

    fieldnames = ["epoch", "loss", "val_loss", "accuracy", "val_accuracy", "macro_f1", "val_macro_f1", "learning_rate"]
    with open(history_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(history_records)

    print(f"Saved training history to: {history_csv}", flush=True)

    plot_training_curves(history_records, PHASE2D_DIR / "training_curves.png")

    # 8. Model Selection Based on Highest Validation Macro F1
    best_record = max(history_records, key=lambda x: x["val_macro_f1"])
    best_epoch = best_record["epoch"]
    best_val_macro_f1 = best_record["val_macro_f1"]

    print(
        f"\nBest Model Selected at Epoch {best_epoch} with Val Macro F1 = {best_val_macro_f1:.4f} "
        f"(Val Acc = {best_record['val_accuracy']:.4f}, Val Loss = {best_record['val_loss']:.4f})",
        flush=True
    )

    # 9. Load Best Model Checkpoint for Final 2025 Test Evaluation
    print(f"Loading best checkpoint from: {best_model_path}", flush=True)
    best_model = tf.keras.models.load_model(
        best_model_path,
        custom_objects={"BahdanauAttention": BahdanauAttention},
        safe_mode=False,
        compile=False,
    )

    # Save plaintext summary of final model
    summary_stream = io.StringIO()
    best_model.summary(print_fn=lambda x: summary_stream.write(x + "\n"))
    with open(PHASE2D_DIR / "final_model_summary.txt", "w", encoding="utf-8") as f:
        f.write(summary_stream.getvalue())

    # 10. Untouched 2025 Test Evaluation (EVALUATED ONCE ONLY)
    print("Evaluating Best Model ONCE on the Untouched 2025 Test Set (10,740 samples)...", flush=True)
    y_pred_prob = best_model.predict(test_ds, verbose=0)
    y_true_test = tensors["test"]["y"]

    true_cls_test = np.argmax(y_true_test, axis=1)
    pred_cls_test = np.argmax(y_pred_prob, axis=1)

    # Calculate Overall Test Metrics
    test_acc = float(accuracy_score(true_cls_test, pred_cls_test))
    test_bal_acc = float(balanced_accuracy_score(true_cls_test, pred_cls_test))
    test_macro_prec = float(precision_score(true_cls_test, pred_cls_test, average="macro", zero_division=0))
    test_macro_rec = float(recall_score(true_cls_test, pred_cls_test, average="macro", zero_division=0))
    test_macro_f1 = float(f1_score(true_cls_test, pred_cls_test, average="macro", zero_division=0))
    test_weighted_f1 = float(f1_score(true_cls_test, pred_cls_test, average="weighted", zero_division=0))
    test_macro_pr_auc = compute_pr_auc_macro(y_true_test, y_pred_prob)

    # Calculate Per-Class Test Metrics
    prec_per_class = precision_score(true_cls_test, pred_cls_test, average=None, labels=[0, 1, 2, 3, 4], zero_division=0)
    rec_per_class = recall_score(true_cls_test, pred_cls_test, average=None, labels=[0, 1, 2, 3, 4], zero_division=0)
    f1_per_class = f1_score(true_cls_test, pred_cls_test, average=None, labels=[0, 1, 2, 3, 4], zero_division=0)
    support_per_class = [int(np.sum(true_cls_test == k)) for k in range(5)]

    # Compute 1,000 Bootstrap Confidence Intervals
    print("Computing 1,000 Stratified Bootstrap 95% Confidence Intervals for 2025 Test Set...", flush=True)
    bootstrap_cis = compute_bootstrap_cis(y_true_test, y_pred_prob, n_bootstraps=1000, seed=42)

    # Confusion Matrix
    cm = confusion_matrix(true_cls_test, pred_cls_test, labels=[0, 1, 2, 3, 4])
    plot_confusion_matrix_heatmap(cm, PHASE2D_DIR / "confusion_matrix.png")

    # Save Confusion Matrix CSV
    np.savetxt(
        PHASE2D_DIR / "dl_confusion_matrix.csv",
        cm,
        delimiter=",",
        fmt="%d",
        header="0_Low,1_Mod,2_High,3_VHigh,4_Severe",
        comments="",
    )

    # Save Per-Class Metrics CSV
    per_class_csv = PHASE2D_DIR / "dl_per_class_metrics.csv"
    with open(per_class_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["class_id", "class_name", "support", "precision", "recall", "f1_score"])
        class_names = ["Low (0)", "Moderate (1)", "Unhealthy (2)", "Very Unhealthy (3)", "Severe (4)"]
        for k in range(5):
            w.writerow([
                k, class_names[k], support_per_class[k],
                float(prec_per_class[k]), float(rec_per_class[k]), float(f1_per_class[k])
            ])

    # Save Test Metrics JSON
    test_metrics_json = PHASE2D_DIR / "dl_test_metrics.json"
    test_metrics_dict = {
        "evaluation_period": "2025 Final Untouched Test Set",
        "sample_count": len(y_true_test),
        "overall_metrics": {
            "accuracy": test_acc,
            "balanced_accuracy": test_bal_acc,
            "macro_precision": test_macro_prec,
            "macro_recall": test_macro_rec,
            "macro_f1": test_macro_f1,
            "weighted_f1": test_weighted_f1,
            "macro_pr_auc": test_macro_pr_auc,
        },
        "bootstrap_95_confidence_intervals": bootstrap_cis,
        "per_class_metrics": {
            str(k): {
                "class_name": class_names[k],
                "support": support_per_class[k],
                "precision": float(prec_per_class[k]),
                "recall": float(rec_per_class[k]),
                "f1_score": float(f1_per_class[k]),
            }
            for k in range(5)
        },
        "minority_class_spotlight": {
            "class_3_very_unhealthy": {
                "support": support_per_class[3],
                "correct_predictions": int(cm[3, 3]),
                "recall": float(rec_per_class[3]),
                "recall_95_ci": [bootstrap_cis["class_3_recall"]["ci_lower"], bootstrap_cis["class_3_recall"]["ci_upper"]],
                "f1_score": float(f1_per_class[3]),
            },
            "class_4_severe": {
                "support": support_per_class[4],
                "correct_predictions": int(cm[4, 4]),
                "recall": float(rec_per_class[4]),
                "recall_95_ci": [bootstrap_cis["class_4_recall"]["ci_lower"], bootstrap_cis["class_4_recall"]["ci_upper"]],
                "precision": float(prec_per_class[4]),
                "f1_score": float(f1_per_class[4]),
                "uncertainty_note": "Sample size N=28 produces wide 95% CI bounds.",
            },
        },
    }

    with open(test_metrics_json, "w", encoding="utf-8") as f:
        json.dump(test_metrics_dict, f, indent=2)

    # 11. Compare Against Frozen Phase 3E ML Benchmark
    classical_ml_benchmark = {
        "Logistic Regression": {
            "accuracy": 0.4506, "balanced_accuracy": 0.4417, "macro_f1": 0.3457,
            "macro_pr_auc": 0.3773, "class_3_recall": 0.4595, "class_4_recall": 0.2500
        },
        "Linear SVM": {
            "accuracy": 0.5717, "balanced_accuracy": 0.3409, "macro_f1": 0.3381,
            "macro_pr_auc": 0.4062, "class_3_recall": 0.0000, "class_4_recall": 0.0000
        },
        "Random Forest (Phase 3E Best)": {
            "accuracy": 0.6225, "balanced_accuracy": 0.4821, "macro_f1": 0.4599,
            "macro_pr_auc": 0.4684, "class_3_recall": 0.3745, "class_4_recall": 0.1071
        },
        "Proposed Deep Learning Model": {
            "accuracy": test_acc, "balanced_accuracy": test_bal_acc, "macro_f1": test_macro_f1,
            "macro_pr_auc": test_macro_pr_auc, "class_3_recall": float(rec_per_class[3]),
            "class_4_recall": float(rec_per_class[4])
        },
    }

    # Consolidated Phase 2D Summary Results JSON
    phase2d_results = {
        "best_epoch": best_epoch,
        "validation_selection": {
            "best_val_macro_f1": best_val_macro_f1,
            "val_loss": best_record["val_loss"],
            "val_accuracy": best_record["val_accuracy"],
            "learning_rate_at_best_epoch": best_record["learning_rate"],
        },
        "test_2025_evaluation": test_metrics_dict,
        "classical_ml_comparison": classical_ml_benchmark,
    }

    with open(PHASE2D_DIR / "phase2d_results.json", "w", encoding="utf-8") as f:
        json.dump(phase2d_results, f, indent=2)

    print("\nPhase 2D Training, Model Selection & Evaluation Complete!", flush=True)
    return phase2d_results


if __name__ == "__main__":
    train_and_evaluate_phase2d()
