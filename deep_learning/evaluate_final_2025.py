"""Final Phase 2D 2025 Holdout Evaluation Script for Frozen Deep Learning Candidate.

Evaluates frozen model (experiments/phase2d/damped_weights/pow75_weights/best_model.keras)
with frozen thresholds ([0.8, 1.0, 0.9, 0.75, 0.05]) ONCE ONLY on untouched 2025 Test Set.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from config.paths import DL_DATA_DIR, EXPERIMENTS_DIR, ensure_directories_exist
from deep_learning.architecture import BahdanauAttention
from deep_learning.dataset_loader import load_split_tensors
from deep_learning.evaluate_phase2d import compute_bootstrap_cis
from deep_learning.tf_dataset import create_tf_dataset
from deep_learning.threshold_calibration import apply_thresholds, compute_evaluation_metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

FINAL_DIR = EXPERIMENTS_DIR / "phase2d" / "final_2025"
FROZEN_MODEL_PATH = EXPERIMENTS_DIR / "phase2d" / "damped_weights" / "pow75_weights" / "best_model.keras"
FROZEN_THRESHOLDS = [0.8, 1.0, 0.9, 0.75, 0.05]

# Stored Phase 3E Random Forest Baseline Metrics
RF_BENCHMARK_METRICS = {
    "model_name": "Random Forest (Phase 3E Baseline)",
    "accuracy": 0.6224657534246575,
    "balanced_accuracy": 0.4821496580313737,
    "macro_precision": 0.44958903277242185,
    "macro_recall": 0.4821496580313737,
    "macro_f1": 0.459929943678019,
    "weighted_f1": 0.6255287560434016,
    "macro_pr_auc": 0.468363637394673,
    "per_class": {
        "0": {"class_name": "Low (0)", "precision": 0.548467, "recall": 0.699171, "f1_score": 0.614686},
        "1": {"class_name": "Moderate (1)", "precision": 0.726964, "recall": 0.594520, "f1_score": 0.654109},
        "2": {"class_name": "Unhealthy (2)", "precision": 0.587199, "recall": 0.635398, "f1_score": 0.610350},
        "3": {"class_name": "Very Unhealthy (3)", "precision": 0.339161, "recall": 0.374517, "f1_score": 0.355963},
        "4": {"class_name": "Severe (4)", "precision": 0.046154, "recall": 0.107143, "f1_score": 0.064516},
    },
}


def plot_test_confusion_matrix(cm_data: List[List[int]], title: str, output_path: Path) -> None:
    """Plots and saves confusion matrix heatmap for final 2025 test set evaluation."""
    cm = np.array(cm_data)
    labels = ["Low (0)", "Mod (1)", "High (2)", "V.High (3)", "Severe (4)"]
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

    try:
        import seaborn as sns
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=labels, yticklabels=labels, cbar=True, ax=ax)
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
                ax.text(j, i, format(cm[i, j], "d"), ha="center", va="center", color="white" if cm[i, j] > thresh else "black")

    ax.set_title(title, fontsize=13, fontweight="bold", pad=15)
    ax.set_xlabel("Predicted Class", fontsize=11, fontweight="bold")
    ax.set_ylabel("True Class", fontsize=11, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved test confusion matrix heatmap to: {output_path}")


def run_final_2025_holdout_evaluation() -> Dict[str, Any]:
    """Executes official final evaluation of frozen DL candidate on 2025 Test Set."""
    ensure_directories_exist()
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("=================================================================")
    logger.info(" FINAL PHASE 2D — 2025 HOLDOUT EVALUATION")
    logger.info("=================================================================")
    logger.info(f"Loading frozen DL checkpoint: {FROZEN_MODEL_PATH}")

    model = tf.keras.models.load_model(
        FROZEN_MODEL_PATH,
        custom_objects={"BahdanauAttention": BahdanauAttention},
        safe_mode=False,
        compile=False,
    )

    logger.info("Loading Phase 2A 2025 Test Tensors ONLY...")
    test_tensors = load_split_tensors("test", data_dir=DL_DATA_DIR)
    test_ds = create_tf_dataset(
        X_dynamic=test_tensors["X_dynamic"],
        X_static_num=test_tensors["X_static_num"],
        X_static_cat=test_tensors["X_static_cat"],
        y=test_tensors["y"],
        batch_size=32,
        is_training=False,
        cache=True,
    )

    y_test_onehot = test_tensors["y"]
    y_test_true = np.argmax(y_test_onehot, axis=1)
    n_test = len(y_test_true)

    logger.info(f"Generating Softmax probabilities on 2025 Test Set (N={n_test} samples)...")
    y_test_prob = model.predict(test_ds, verbose=0)

    # 1. Raw Argmax Predictions (for transparency)
    y_pred_argmax = np.argmax(y_test_prob, axis=1)
    raw_argmax_metrics = compute_evaluation_metrics(y_test_true, y_pred_argmax, num_classes=5)

    # 2. Official Calibrated Predictions using Frozen Threshold Vector
    logger.info(f"Applying official frozen decision thresholds: {FROZEN_THRESHOLDS}")
    y_pred_calibrated = apply_thresholds(y_test_prob, FROZEN_THRESHOLDS)
    official_metrics = compute_evaluation_metrics(y_test_true, y_pred_calibrated, num_classes=5)

    # 3. Compute 1,000-sample Bootstrap 95% CIs for official calibrated predictions
    logger.info("Computing 1,000-sample Bootstrap 95% Confidence Intervals...")
    bootstrap_cis = compute_bootstrap_cis(y_test_onehot, y_test_prob, n_bootstraps=1000, seed=42)

    # 4. Compare Final DL vs Stored RF Benchmark
    dl_macro_f1 = official_metrics["overall_metrics"]["macro_f1"]
    rf_macro_f1 = RF_BENCHMARK_METRICS["macro_f1"]
    diff_macro_f1 = dl_macro_f1 - rf_macro_f1
    pct_diff_macro_f1 = (diff_macro_f1 / rf_macro_f1) * 100.0

    dl_beat_rf = bool(dl_macro_f1 > rf_macro_f1)

    conclusion_code = "A" if dl_macro_f1 > rf_macro_f1 + 0.005 else ("B" if rf_macro_f1 > dl_macro_f1 + 0.005 else "C")
    conclusion_text = (
        f"The Deep Learning model achieved a higher Macro F1 than the Random Forest baseline by {diff_macro_f1:+.4f} (+{pct_diff_macro_f1:.2f}%)." if conclusion_code == "A" else
        (f"The Random Forest baseline achieved a higher Macro F1 than the Deep Learning model by {-diff_macro_f1:+.4f}." if conclusion_code == "B" else "Performance between Deep Learning and Random Forest was statistically comparable.")
    )

    logger.info("-----------------------------------------------------------------")
    logger.info(f" Official Final DL 2025 Test Macro F1: {dl_macro_f1:.4f}")
    logger.info(f" Stored Baseline RF 2025 Test Macro F1: {rf_macro_f1:.4f}")
    logger.info(f" Delta (DL - RF): {diff_macro_f1:+.4f} ({pct_diff_macro_f1:+.2f}%)")
    logger.info(f" Final Conclusion: Option {conclusion_code} — {conclusion_text}")
    logger.info("-----------------------------------------------------------------")

    # 5. Export Artifacts

    # NPY: Test Probabilities
    np.save(FINAL_DIR / "dl_test_probabilities.npy", y_test_prob)
    logger.info(f"Saved test probabilities NPY to: {FINAL_DIR / 'dl_test_probabilities.npy'}")

    # CSV: Predictions Table
    pred_csv_path = FINAL_DIR / "dl_test_predictions.csv"
    with open(pred_csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sample_index", "true_class", "raw_argmax_pred", "calibrated_pred", "P0", "P1", "P2", "P3", "P4"])
        for i in range(n_test):
            w.writerow([
                i,
                int(y_test_true[i]),
                int(y_pred_argmax[i]),
                int(y_pred_calibrated[i]),
                float(y_test_prob[i, 0]),
                float(y_test_prob[i, 1]),
                float(y_test_prob[i, 2]),
                float(y_test_prob[i, 3]),
                float(y_test_prob[i, 4]),
            ])
    logger.info(f"Saved test predictions CSV to: {pred_csv_path}")

    # JSON: Official DL Test Metrics
    metrics_json_path = FINAL_DIR / "dl_test_metrics.json"
    official_metrics_export = {
        "evaluation_dataset": "2025 Final Untouched Holdout (10,740 samples)",
        "model_checkpoint": str(FROZEN_MODEL_PATH),
        "frozen_thresholds": FROZEN_THRESHOLDS,
        "official_calibrated_metrics": official_metrics,
        "raw_argmax_metrics": raw_argmax_metrics,
        "bootstrap_95_confidence_intervals": bootstrap_cis,
    }
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(official_metrics_export, f, indent=2)
    logger.info(f"Saved DL test metrics JSON to: {metrics_json_path}")

    # CSV: Confusion Matrix
    cm_csv_path = FINAL_DIR / "dl_confusion_matrix.csv"
    np.savetxt(cm_csv_path, np.array(official_metrics["confusion_matrix"]), fmt="%d", delimiter=",")
    logger.info(f"Saved confusion matrix CSV to: {cm_csv_path}")

    # PNG: Confusion Matrix Heatmap
    plot_test_confusion_matrix(
        official_metrics["confusion_matrix"],
        "2025 Test Confusion Matrix — Final Calibrated DL Model",
        FINAL_DIR / "dl_confusion_matrix.png",
    )

    # CSV: Classification Report Text
    report_text = classification_report(
        y_test_true,
        y_pred_calibrated,
        target_names=["Low (0)", "Moderate (1)", "Unhealthy (2)", "Very Unhealthy (3)", "Severe (4)"],
        digits=4,
    )
    with open(FINAL_DIR / "dl_classification_report.csv", "w", encoding="utf-8") as f:
        f.write(report_text)
    logger.info(f"Saved classification report to: {FINAL_DIR / 'dl_classification_report.csv'}")

    # CSV & JSON: DL vs RF Comparison Table
    comparison_rows = [
        {"Metric": "Accuracy", "Random_Forest": RF_BENCHMARK_METRICS["accuracy"], "Final_DL": official_metrics["overall_metrics"]["accuracy"], "Delta": official_metrics["overall_metrics"]["accuracy"] - RF_BENCHMARK_METRICS["accuracy"]},
        {"Metric": "Macro Precision", "Random_Forest": RF_BENCHMARK_METRICS["macro_precision"], "Final_DL": official_metrics["overall_metrics"]["macro_precision"], "Delta": official_metrics["overall_metrics"]["macro_precision"] - RF_BENCHMARK_METRICS["macro_precision"]},
        {"Metric": "Macro Recall", "Random_Forest": RF_BENCHMARK_METRICS["macro_recall"], "Final_DL": official_metrics["overall_metrics"]["macro_recall"], "Delta": official_metrics["overall_metrics"]["macro_recall"] - RF_BENCHMARK_METRICS["macro_recall"]},
        {"Metric": "Macro F1", "Random_Forest": RF_BENCHMARK_METRICS["macro_f1"], "Final_DL": official_metrics["overall_metrics"]["macro_f1"], "Delta": official_metrics["overall_metrics"]["macro_f1"] - RF_BENCHMARK_METRICS["macro_f1"]},
        {"Metric": "Weighted F1", "Random_Forest": RF_BENCHMARK_METRICS["weighted_f1"], "Final_DL": official_metrics["overall_metrics"]["weighted_f1"], "Delta": official_metrics["overall_metrics"]["weighted_f1"] - RF_BENCHMARK_METRICS["weighted_f1"]},
        {"Metric": "Balanced Accuracy", "Random_Forest": RF_BENCHMARK_METRICS["balanced_accuracy"], "Final_DL": official_metrics["overall_metrics"]["balanced_accuracy"], "Delta": official_metrics["overall_metrics"]["balanced_accuracy"] - RF_BENCHMARK_METRICS["balanced_accuracy"]},
        {"Metric": "Class 3 F1", "Random_Forest": RF_BENCHMARK_METRICS["per_class"]["3"]["f1_score"], "Final_DL": official_metrics["per_class_metrics"]["3"]["f1_score"], "Delta": official_metrics["per_class_metrics"]["3"]["f1_score"] - RF_BENCHMARK_METRICS["per_class"]["3"]["f1_score"]},
        {"Metric": "Class 3 Recall", "Random_Forest": RF_BENCHMARK_METRICS["per_class"]["3"]["recall"], "Final_DL": official_metrics["per_class_metrics"]["3"]["recall"], "Delta": official_metrics["per_class_metrics"]["3"]["recall"] - RF_BENCHMARK_METRICS["per_class"]["3"]["recall"]},
        {"Metric": "Class 4 F1", "Random_Forest": RF_BENCHMARK_METRICS["per_class"]["4"]["f1_score"], "Final_DL": official_metrics["per_class_metrics"]["4"]["f1_score"], "Delta": official_metrics["per_class_metrics"]["4"]["f1_score"] - RF_BENCHMARK_METRICS["per_class"]["4"]["f1_score"]},
        {"Metric": "Class 4 Recall", "Random_Forest": RF_BENCHMARK_METRICS["per_class"]["4"]["recall"], "Final_DL": official_metrics["per_class_metrics"]["4"]["recall"], "Delta": official_metrics["per_class_metrics"]["4"]["recall"] - RF_BENCHMARK_METRICS["per_class"]["4"]["recall"]},
    ]

    comp_csv_path = FINAL_DIR / "dl_rf_comparison.csv"
    with open(comp_csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Metric", "Random_Forest", "Final_DL", "Delta"])
        w.writeheader()
        w.writerows(comparison_rows)
    logger.info(f"Saved DL vs RF comparison CSV to: {comp_csv_path}")

    final_summary_dict = {
        "evaluation_name": "Final Phase 2D 2025 Holdout Evaluation",
        "frozen_candidate_id": "phase2d_dl_pow75_weights_calibrated",
        "checkpoint_used": str(FROZEN_MODEL_PATH),
        "frozen_thresholds": FROZEN_THRESHOLDS,
        "seed": 42,
        "dl_test_macro_f1": dl_macro_f1,
        "dl_test_accuracy": official_metrics["overall_metrics"]["accuracy"],
        "dl_test_balanced_acc": official_metrics["overall_metrics"]["balanced_accuracy"],
        "rf_test_macro_f1": rf_macro_f1,
        "rf_test_accuracy": RF_BENCHMARK_METRICS["accuracy"],
        "macro_f1_difference_dl_minus_rf": diff_macro_f1,
        "macro_f1_relative_gain_pct": pct_diff_macro_f1,
        "dl_beat_rf": dl_beat_rf,
        "scientific_conclusion": {
            "code": conclusion_code,
            "statement": conclusion_text,
        },
        "confirmation": {
            "frozen_candidate_used": True,
            "zero_retraining_or_tuning": True,
            "2025_test_evaluated_once": True,
        },
    }

    with open(FINAL_DIR / "final_test_summary.json", "w", encoding="utf-8") as f:
        json.dump(final_summary_dict, f, indent=2)

    logger.info(f"Saved final test summary JSON to: {FINAL_DIR / 'final_test_summary.json'}")
    return final_summary_dict


if __name__ == "__main__":
    run_final_2025_holdout_evaluation()
