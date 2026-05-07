from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class LogisticModel:
    weights: np.ndarray
    bias: float
    means: np.ndarray
    stds: np.ndarray
    feature_names: list[str]


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-np.clip(values, -35, 35)))


def train_logistic_regression(
    x_train: np.ndarray,
    y_train: np.ndarray,
    feature_names: list[str],
    learning_rate: float = 0.08,
    epochs: int = 1800,
    l2: float = 0.01,
) -> LogisticModel:
    means = x_train.mean(axis=0)
    stds = x_train.std(axis=0)
    stds[stds == 0] = 1
    x_scaled = (x_train - means) / stds

    weights = np.zeros(x_scaled.shape[1])
    bias = 0.0

    for _ in range(epochs):
        predictions = _sigmoid(x_scaled @ weights + bias)
        errors = predictions - y_train
        gradient_w = (x_scaled.T @ errors) / len(y_train) + l2 * weights
        gradient_b = errors.mean()
        weights -= learning_rate * gradient_w
        bias -= learning_rate * gradient_b

    return LogisticModel(weights=weights, bias=bias, means=means, stds=stds, feature_names=feature_names)


def predict_proba(model: LogisticModel, x_values: np.ndarray) -> np.ndarray:
    x_scaled = (x_values - model.means) / model.stds
    return _sigmoid(x_scaled @ model.weights + model.bias)


def classification_metrics(y_true: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    threshold = best_f1_threshold(y_true, probabilities)
    labels = (probabilities >= threshold).astype(int)
    tp = int(((labels == 1) & (y_true == 1)).sum())
    tn = int(((labels == 0) & (y_true == 0)).sum())
    fp = int(((labels == 1) & (y_true == 0)).sum())
    fn = int(((labels == 0) & (y_true == 1)).sum())

    accuracy = (tp + tn) / max(len(y_true), 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)

    return {
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "roc_auc": round(float(roc_auc(y_true, probabilities)), 4),
        "decision_threshold": round(float(threshold), 4),
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
    }


def best_f1_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    best_threshold = 0.5
    best_score = -1.0
    for threshold in np.linspace(0.15, 0.75, 61):
        labels = (probabilities >= threshold).astype(int)
        tp = int(((labels == 1) & (y_true == 1)).sum())
        fp = int(((labels == 1) & (y_true == 0)).sum())
        fn = int(((labels == 0) & (y_true == 1)).sum())
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        score = 2 * precision * recall / max(precision + recall, 1e-12)
        if score > best_score:
            best_score = score
            best_threshold = float(threshold)
    return best_threshold


def roc_auc(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    order = np.argsort(probabilities)
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(probabilities) + 1)
    positive_ranks = ranks[y_true == 1].sum()
    n_positive = int((y_true == 1).sum())
    n_negative = int((y_true == 0).sum())
    if n_positive == 0 or n_negative == 0:
        return 0.5
    return (positive_ranks - n_positive * (n_positive + 1) / 2) / (n_positive * n_negative)
