"""Model summary generation, plot visualization, and hyperparameter reporting utilities."""

import io
import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

import tensorflow as tf

from config.paths import EXPERIMENTS_DIR, ensure_directories_exist
from deep_learning.architecture import build_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def export_model_summary(
    model: tf.keras.Model,
    output_path: Optional[Path] = None,
) -> str:
    """Captures model.summary() output and writes it to a plain text file.

    Args:
        model: Built Keras Model instance.
        output_path: Target text file path. Defaults to EXPERIMENTS_DIR / 'model_summary.txt'.

    Returns:
        str: Model summary formatted string.
    """
    if output_path is None:
        output_path = EXPERIMENTS_DIR / "model_summary.txt"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    stream = io.StringIO()
    model.summary(print_fn=lambda x: stream.write(x + "\n"))
    summary_str = stream.getvalue()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(summary_str)

    logger.info(f"Model summary saved to: {output_path}")
    return summary_str


def _render_matplotlib_architecture(model: tf.keras.Model, output_path: Path) -> None:
    """Generates a high-quality visual diagram of the hybrid multi-input network using matplotlib."""
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
    ax.axis("off")
    ax.set_title("AI-AQI Hybrid Multi-Input Model Architecture", fontsize=16, fontweight="bold", pad=20)

    # Define color scheme
    c_dyn = "#e3f2fd"
    c_snum = "#e8f5e9"
    c_scat = "#fff3e0"
    c_fusion = "#f3e5f5"
    c_out = "#ffebee"
    border = "#37474f"

    def draw_box(x, y, w, h, text, color):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.03",
            linewidth=1.5,
            edgecolor=border,
            facecolor=color,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, fontweight="bold")

    def draw_arrow(x1, y1, x2, y2):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", lw=1.5, color="#263238")
        )

    # Branch 1: Dynamic
    draw_box(0.05, 0.82, 0.26, 0.10, "Dynamic Input\n(batch, 7, 24)", c_dyn)
    draw_box(0.05, 0.68, 0.26, 0.10, "Conv1D (64 filters, k=3)\n+ BatchNorm + ReLU + MaxPool1D", c_dyn)
    draw_box(0.05, 0.54, 0.26, 0.10, "Bidirectional LSTM\n(64 units, return_seq=True)", c_dyn)
    draw_box(0.05, 0.40, 0.26, 0.10, "Bahdanau Attention\n(Additive Attention, 64 u)", c_dyn)
    draw_box(0.05, 0.26, 0.26, 0.10, "Dense Projection\n(64 units, ReLU)", c_dyn)

    draw_arrow(0.18, 0.82, 0.18, 0.78)
    draw_arrow(0.18, 0.68, 0.18, 0.64)
    draw_arrow(0.18, 0.54, 0.18, 0.50)
    draw_arrow(0.18, 0.40, 0.18, 0.36)

    # Branch 2: Static Numerical
    draw_box(0.37, 0.82, 0.26, 0.10, "Static Numerical Input\n(batch, 16)", c_snum)
    draw_box(0.37, 0.61, 0.26, 0.13, "Dense (64) + BatchNorm\n+ ReLU + Dropout (0.3)", c_snum)
    draw_box(0.37, 0.26, 0.26, 0.10, "Dense Projection\n(32 units, ReLU)", c_snum)

    draw_arrow(0.50, 0.82, 0.50, 0.74)
    draw_arrow(0.50, 0.61, 0.50, 0.36)

    # Branch 3: Static Categorical
    draw_box(0.69, 0.82, 0.26, 0.10, "Static Categorical Input\n(batch, 3)", c_scat)
    draw_box(0.69, 0.61, 0.26, 0.13, "3 x Embedding Layers\n(district:16, land:4, urban:2)\n+ Flatten + Concatenate", c_scat)
    draw_box(0.69, 0.26, 0.26, 0.10, "Dense Projection\n(16 units, ReLU)", c_scat)

    draw_arrow(0.82, 0.82, 0.82, 0.74)
    draw_arrow(0.82, 0.61, 0.82, 0.36)

    # Fusion Network
    draw_box(0.20, 0.12, 0.60, 0.08, "Fusion Concatenation (64 + 32 + 16 = 112 dims)", c_fusion)
    draw_box(0.20, 0.02, 0.28, 0.07, "MLP (128 -> BN -> ReLU -> Drop -> 64)", c_fusion)
    draw_box(0.52, 0.02, 0.28, 0.07, "Softmax Output\n(batch, 5)", c_out)

    draw_arrow(0.18, 0.26, 0.35, 0.20)
    draw_arrow(0.50, 0.26, 0.50, 0.20)
    draw_arrow(0.82, 0.26, 0.65, 0.20)

    draw_arrow(0.50, 0.12, 0.34, 0.09)
    draw_arrow(0.48, 0.055, 0.52, 0.055)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"Rendered architecture plot saved to: {output_path}")


def generate_architecture_plot(
    model: tf.keras.Model,
    output_path: Optional[Path] = None,
    show_shapes: bool = True,
    show_layer_names: bool = True,
    show_layer_activations: bool = True,
) -> Path:
    """Generates visual architecture diagram using tf.keras.utils.plot_model.

    Args:
        model: Built Keras Model instance.
        output_path: Target PNG file path. Defaults to EXPERIMENTS_DIR / 'model_architecture.png'.
        show_shapes: Whether to display tensor shape information. Defaults to True.
        show_layer_names: Whether to display layer names. Defaults to True.
        show_layer_activations: Whether to display layer activation functions. Defaults to True.

    Returns:
        Path: Path to the generated architecture plot PNG.
    """
    if output_path is None:
        output_path = EXPERIMENTS_DIR / "model_architecture.png"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    has_dot = shutil.which("dot") is not None or shutil.which("dot.exe") is not None
    plot_success = False

    if has_dot:
        try:
            tf.keras.utils.plot_model(
                model,
                to_file=str(output_path),
                show_shapes=show_shapes,
                show_layer_names=show_layer_names,
                show_layer_activations=show_layer_activations,
                expand_nested=True,
                dpi=150,
            )
            if output_path.exists() and output_path.stat().st_size > 0:
                plot_success = True
                logger.info(f"Architecture plot saved via plot_model to: {output_path}")
        except Exception as e:
            logger.warning(f"tf.keras.utils.plot_model failed ({e}). Falling back to diagram renderer.")

    if not plot_success:
        logger.info("Rendering high-quality matplotlib architecture diagram...")
        _render_matplotlib_architecture(model, output_path)

    return output_path


def generate_parameter_report(
    model: tf.keras.Model,
    output_path: Optional[Path] = None,
    config_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Computes parameter counts and network layer metadata into a JSON report.

    Args:
        model: Built Keras Model instance.
        output_path: Target JSON file path. Defaults to EXPERIMENTS_DIR / 'model_report.json'.
        config_overrides: Optional dict containing architecture hyperparameter values.

    Returns:
        Dict[str, Any]: Dictionary containing total/trainable parameter counts and hyperparameter specs.
    """
    if output_path is None:
        output_path = EXPERIMENTS_DIR / "model_report.json"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_params = int(model.count_params())
    trainable_params = int(sum(tf.keras.backend.count_params(p) for p in model.trainable_weights))
    non_trainable_params = int(sum(tf.keras.backend.count_params(p) for p in model.non_trainable_weights))

    input_shapes = {}
    if isinstance(model.input, dict):
        for name, inp in model.input.items():
            shape_tuple = inp.shape.as_list() if hasattr(inp.shape, "as_list") else list(inp.shape)
            input_shapes[name] = [dim if dim is not None else -1 for dim in shape_tuple]
    else:
        for i, inp in enumerate(model.inputs):
            shape_tuple = inp.shape.as_list() if hasattr(inp.shape, "as_list") else list(inp.shape)
            input_shapes[f"input_{i}"] = [dim if dim is not None else -1 for dim in shape_tuple]

    out_shape_tuple = model.output.shape.as_list() if hasattr(model.output.shape, "as_list") else list(model.output.shape)
    output_shape = [dim if dim is not None else -1 for dim in out_shape_tuple]

    report: Dict[str, Any] = {
        "model_name": model.name,
        "total_parameters": total_params,
        "trainable_parameters": trainable_params,
        "non_trainable_parameters": non_trainable_params,
        "input_tensor_shapes": input_shapes,
        "output_tensor_shape": output_shape,
        "embedding_dimensions": {
            "district_id": {"vocab_size": 32, "embedding_dim": 16},
            "land_use_id": {"vocab_size": 8, "embedding_dim": 4},
            "urban_rural_id": {"vocab_size": 4, "embedding_dim": 2},
        },
        "conv1d_configuration": {
            "filters": 64,
            "kernel_size": 3,
            "padding": "same",
            "activation": "relu",
            "max_pooling": {"pool_size": 2, "padding": "same"},
        },
        "bilstm_units": 64,
        "attention_layer_configuration": {
            "type": "BahdanauAttention",
            "units": 64,
            "score_formula": "v^T * tanh(W * h + b)",
        },
        "dense_layer_sizes": {
            "dynamic_projection": 64,
            "static_num_dense_1": 64,
            "static_num_projection": 32,
            "static_cat_projection": 16,
            "fusion_dense_1": 128,
            "fusion_dense_2": 64,
            "aqi_output": 5,
        },
        "dropout_rates": {
            "static_num_branch": 0.3,
            "fusion_network": 0.3,
        },
    }

    if config_overrides:
        report.update(config_overrides)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Parameter report saved to: {output_path}")
    return report


def main() -> None:
    """CLI execution entrypoint to generate all Phase 2C architecture artifacts."""
    ensure_directories_exist()

    logger.info("Building Phase 2C Hybrid AQI Deep Learning Model...")
    model = build_model()

    logger.info("Generating model_summary.txt...")
    export_model_summary(model)

    logger.info("Generating model_architecture.png...")
    generate_architecture_plot(model)

    logger.info("Generating model_report.json...")
    generate_parameter_report(model)

    logger.info("Phase 2C model artifact generation complete!")


if __name__ == "__main__":
    main()
