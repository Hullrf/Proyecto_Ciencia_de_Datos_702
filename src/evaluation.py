"""Temporal split and metrics shared by the modelling notebooks."""
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score


def temporal_split(df: pd.DataFrame, split: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split by year according to config `split` = {train: [...], val: [...], test: [...]}."""
    return tuple(df[df["year"].isin(split[part])] for part in ("train", "val", "test"))


def evaluate(y_true, y_proba) -> dict:
    """Accuracy (threshold 0.5), ROC-AUC and log loss for predicted probabilities of class 1."""
    y_proba = np.asarray(y_proba, dtype=float)
    return {
        "accuracy": accuracy_score(y_true, y_proba > 0.5),
        "roc_auc": roc_auc_score(y_true, y_proba),
        "log_loss": log_loss(y_true, y_proba, labels=[0, 1]),
    }
