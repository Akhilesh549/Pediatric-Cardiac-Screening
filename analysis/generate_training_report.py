"""Generate training curves and reconstructed validation confusion matrices.

The repository does not currently contain TensorBoard event files or saved
validation predictions. This report therefore uses the epoch metrics and
validation-set sizes documented in TRAINING_LOG.md. Confusion-matrix counts
are reconstructed from rounded sensitivity and specificity values and must
not be presented as sample-level evaluation output.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


EPOCHS = {
    "Ultrasound": {
        "epoch": [1, 2, 3, 4, 5],
        "train_loss": [0.7582, 0.5478, 0.3826, 0.2957, 0.2395],
        "val_loss": [0.6841, 0.4921, 0.2818, 0.2995, 0.1644],
        "train_accuracy": [0.806, 0.873, 0.921, 0.944, 0.957],
        "val_accuracy": [0.826, 0.856, 0.920, 0.959, 0.976],
    },
    "Audio": {
        "epoch": [1, 2, 3, 4, 11],
        "train_loss": [1.0671, 0.8505, 0.6426, 0.4853, 0.1118],
        "val_loss": [0.9570, 0.7923, 1.7205, 1.6794, 3.3228],
        "train_accuracy": [0.638, 0.802, 0.856, 0.908, 0.988],
        "val_accuracy": [0.620, 0.795, 0.795, 0.801, 0.789],
    },
    "X-ray": {
        "epoch": [1, 2, 3, 4, 7, 8, 10, 17],
        "train_loss": [np.nan] * 8,
        "val_loss": [np.nan] * 8,
        "train_accuracy": [0.729, 0.756, 0.802, 0.806, 0.869, 0.878, 0.899, 0.947],
        "val_accuracy": [0.740, 0.756, 0.797, 0.813, 0.837, 0.846, 0.894, 0.870],
    },
}


def load_gmu_history() -> dict[str, list[float]]:
    """Read the validation accuracy saved in each GMU checkpoint."""
    checkpoint_dir = Path(__file__).resolve().parents[1] / "checkpoints" / "gmu"
    history = {"epoch": [], "train_accuracy": [], "val_accuracy": [],
               "train_loss": [], "val_loss": []}
    try:
        import torch
    except ImportError:
        return history

    for checkpoint_path in sorted(checkpoint_dir.glob("gmu_epoch*.pth")):
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        history["epoch"].append(int(checkpoint["epoch"]) + 1)
        history["val_accuracy"].append(checkpoint["val_metrics"]["accuracy"])
        history["train_accuracy"].append(np.nan)
        history["train_loss"].append(np.nan)
        history["val_loss"].append(np.nan)
    return history


# (validation samples, positive prevalence, sensitivity, specificity)
VALIDATION_METRICS = {
    "Ultrasound": (1073, 0.163, 0.938, 0.983),
    "X-ray": (123, 0.749, 0.978, 0.645),
    "Audio": (171, 0.399, 0.721, 0.854),
}


def reconstruct_matrix(total: int, prevalence: float, sensitivity: float, specificity: float):
    positives = round(total * prevalence)
    negatives = total - positives
    true_positive = round(positives * sensitivity)
    true_negative = round(negatives * specificity)
    return np.array(
        [[true_negative, negatives - true_negative],
         [positives - true_positive, true_positive]],
        dtype=int,
    )


def plot_training_curves(output_path: Path, histories: dict[str, dict[str, list[float]]]) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=False)
    figure.subplots_adjust(bottom=0.18, hspace=0.34, wspace=0.30)
    colors = {"accuracy": "#1672b8", "loss": "#ef5350"}
    legend_handles = None

    for axis, (modality, values) in zip(axes.flat, histories.items()):
        epochs = values["epoch"]
        accuracy_axis = axis
        loss_axis = axis.twinx()
        train_accuracy, = accuracy_axis.plot(
            epochs, np.array(values["train_accuracy"]) * 100,
            color=colors["accuracy"], linewidth=1.5, label="Train acc."
        )
        val_accuracy, = accuracy_axis.plot(
            epochs, np.array(values["val_accuracy"]) * 100,
            color=colors["accuracy"], linestyle="--", linewidth=1.5, label="Val. acc."
        )
        train_loss, = loss_axis.plot(
            epochs, values["train_loss"], color=colors["loss"],
            linewidth=1.5, label="Train loss"
        )
        val_loss, = loss_axis.plot(
            epochs, values["val_loss"], color=colors["loss"],
            linestyle="--", linewidth=1.5, label="Val. loss"
        )

        accuracy_axis.set_title(modality, fontsize=11)
        accuracy_axis.set_xlabel("Epoch")
        accuracy_axis.set_ylabel("Accuracy (%)", color=colors["accuracy"])
        accuracy_axis.tick_params(axis="y", labelcolor=colors["accuracy"])
        accuracy_axis.set_ylim(45, 102)
        loss_axis.set_ylabel("Loss", color=colors["loss"])
        loss_axis.tick_params(axis="y", labelcolor=colors["loss"])
        if modality == "X-ray":
            loss_axis.set_ylim(0, 1.05)
        accuracy_axis.grid(alpha=0.25)

        plotted_values = np.asarray(values["val_accuracy"], dtype=float)
        if np.isfinite(plotted_values).any():
            best_index = np.nanargmax(plotted_values)
            accuracy_axis.annotate(
                f"{plotted_values[best_index] * 100:.1f}%",
                (epochs[best_index], plotted_values[best_index] * 100),
                xytext=(5, -3), textcoords="offset points", fontsize=8,
                fontweight="bold"
            )
        if legend_handles is None:
            legend_handles = [train_accuracy, val_accuracy, train_loss, val_loss]

    figure.legend(
        legend_handles,
        ["Train acc.", "Val. acc.", "Train loss", "Val. loss"],
        loc="lower center", bbox_to_anchor=(0.5, 0.02),
        ncol=4, fontsize=9, frameon=True
    )

    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def plot_confusion_matrices(output_path: Path, matrices: dict[str, np.ndarray]) -> None:
    figure, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    figure.suptitle("Reconstructed validation confusion matrices", fontsize=16)
    labels = ["Normal (0)", "CHD (1)"]

    for axis, (modality, matrix) in zip(axes, matrices.items()):
        image = axis.imshow(matrix, cmap="Blues")
        axis.set_title(modality)
        axis.set_xlabel("Predicted label")
        axis.set_ylabel("True label")
        axis.set_xticks(range(2), labels=labels)
        axis.set_yticks(range(2), labels=labels)
        threshold = matrix.max() / 2
        for row in range(2):
            for column in range(2):
                axis.text(
                    column,
                    row,
                    str(matrix[row, column]),
                    ha="center",
                    va="center",
                    color="white" if matrix[row, column] > threshold else "black",
                    fontsize=14,
                )
        figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)

    figure.savefig(output_path, dpi=180)
    plt.close(figure)


def write_csv(output_path: Path, matrices: dict[str, np.ndarray]) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["modality", "true_label", "predicted_0", "predicted_1"])
        for modality, matrix in matrices.items():
            writer.writerow([modality, "Normal (0)", matrix[0, 0], matrix[0, 1]])
            writer.writerow([modality, "CHD (1)", matrix[1, 0], matrix[1, 1]])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    matrices = {
        modality: reconstruct_matrix(*metrics)
        for modality, metrics in VALIDATION_METRICS.items()
    }
    histories = {
        "CRNN2D (Audio)": EPOCHS["Audio"],
        "NTS-Net (Ultrasound)": EPOCHS["Ultrasound"],
        "EfficientNetV2-S (X-ray)": EPOCHS["X-ray"],
        "GMU Fusion (Phase-2)": load_gmu_history(),
    }
    plot_training_curves(args.output_dir / "training_curves.png", histories)
    plot_confusion_matrices(args.output_dir / "confusion_matrices_reconstructed.png", matrices)
    write_csv(args.output_dir / "confusion_matrices_reconstructed.csv", matrices)
    (args.output_dir / "README.md").write_text(
        "# Training report\n\n"
        "These figures are generated from the epoch tables and validation metrics in "
        "`TRAINING_LOG.md`. The training curves contain only epochs explicitly "
        "documented there; missing X-ray loss values are intentionally blank.\n\n"
        "The confusion matrices are reconstructed from rounded sensitivity, "
        "specificity, validation-set size, and class prevalence. They are useful "
        "for a project report, but they are not a substitute for matrices computed "
        "from saved sample-level predictions.\n",
        encoding="utf-8",
    )
    print(f"Generated report files in {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()