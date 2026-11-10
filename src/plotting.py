"""Shared plot style and figure saving."""
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from src.config import FIGURES_DIR


def set_style() -> None:
    sns.set_theme(style="whitegrid", palette="deep")
    plt.rcParams["figure.figsize"] = (9, 5)


def save_fig(name: str) -> Path:
    """Save the current figure to reports/figures/<name>.png and return its path."""
    path = FIGURES_DIR / f"{name}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    return path
