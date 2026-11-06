"""Model evaluation metrics for DebtSight default risk classification.

Evaluates models using:
- ROC-AUC (Area Under Receiver Operating Characteristic)
- PR-AUC / Average Precision (Critical for imbalanced credit default)
- Brier Score (Probability calibration accuracy)
- Precision, Recall, F1-Score
- Confusion Matrix
"""

from typing import Dict, Any


def evaluate_classifier(model, X_test, y_test) -> Dict[str, Any]:
    """Computes comprehensive evaluation metrics for a trained classifier."""
    try:
        from sklearn.metrics import (
            average_precision_score,
            brier_score_loss,
            classification_report,
            confusion_matrix,
            f1_score,
            precision_score,
            recall_score,
            roc_auc_score,
        )
    except ImportError as e:
        raise ImportError("scikit-learn is required for evaluation.") from e

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    roc_auc = float(roc_auc_score(y_test, y_prob))
    pr_auc = float(average_precision_score(y_test, y_prob))
    brier = float(brier_score_loss(y_test, y_prob))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    precision = float(precision_score(y_test, y_pred, zero_division=0))
    recall = float(recall_score(y_test, y_pred, zero_division=0))
    cm = confusion_matrix(y_test, y_pred).tolist()

    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    return {
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
        "f1_score": round(f1, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "confusion_matrix": cm,
        "classification_report": report,
    }


def format_evaluation_summary(metrics: Dict[str, Any]) -> str:
    """Formats metrics dictionary into a clean markdown summary."""
    cm = metrics["confusion_matrix"]
    tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]

    return f"""
### Model Evaluation Report
* **ROC-AUC Score**: {metrics['roc_auc']:.4f} (Separation between defaults and non-defaults)
* **PR-AUC (Avg Precision)**: {metrics['pr_auc']:.4f} (Crucial for imbalanced default data)
* **Brier Score**: {metrics['brier_score']:.4f} (Closer to 0.0 indicates well-calibrated probabilities)
* **F1-Score**: {metrics['f1_score']:.4f}
* **Precision**: {metrics['precision']:.4f}
* **Recall (Sensitivity)**: {metrics['recall']:.4f}

#### Confusion Matrix:
| | Predicted Non-Default (0) | Predicted Default (1) |
| :--- | :---: | :---: |
| **Actual Non-Default (0)** | TN: {tn} | FP: {fp} |
| **Actual Default (1)** | FN: {fn} | TP: {tp} |
"""
