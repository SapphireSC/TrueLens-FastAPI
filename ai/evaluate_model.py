"""
TrueLens AI - Skrip Evaluasi Model pada 20.000 Citra Testing Set CIFAKE
Menghitung Accuracy, Precision, Recall, F1-Score, ROC-AUC, & Confusion Matrix
dan menyimpannya ke ai/saved_model/evaluation_metrics.json.
"""
import os
import json
import argparse
from datetime import datetime
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from train_efficientnet import build_datasets


def evaluate_truelens_model(dataset_dir: str, model_path: str, output_json_path: str):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model tidak ditemukan di {model_path}. Jalankan train_efficientnet.py terlebih dahulu.")

    _, _, test_ds = build_datasets(dataset_dir)
    model = tf.keras.models.load_model(model_path)

    y_true = []
    y_probs = []

    print("=== Menjalankan Inferensi pada Data Testing CIFAKE ===")
    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_probs.extend(preds.flatten().tolist())
        y_true.extend(labels.numpy().flatten().tolist())

    y_true_arr = np.array(y_true, dtype=int)
    y_probs_arr = np.array(y_probs, dtype=float)
    y_pred_arr = (y_probs_arr >= 0.50).astype(int)

    acc = float(accuracy_score(y_true_arr, y_pred_arr))
    prec = float(precision_score(y_true_arr, y_pred_arr, zero_division=0))
    rec = float(recall_score(y_true_arr, y_pred_arr, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))
    auc = float(roc_auc_score(y_true_arr, y_probs_arr))
    tn, fp, fn, tp = confusion_matrix(y_true_arr, y_pred_arr).ravel()

    metrics_payload = {
        "evaluated": True,
        "model_name": "EfficientNet-B0 (Transfer Learning CNN)",
        "dataset": "CIFAKE (Real and AI-Generated Synthetic Images)",
        "test_samples": int(len(y_true_arr)),
        "threshold": 0.50,
        "accuracy": round(acc * 100, 2),
        "precision": round(prec * 100, 2),
        "recall": round(rec * 100, 2),
        "f1_score": round(f1 * 100, 2),
        "roc_auc": round(auc, 4),
        "confusion_matrix": {
            "true_negative_real": int(tn),
            "false_positive_ai": int(fp),
            "false_negative_real": int(fn),
            "true_positive_ai": int(tp),
        },
        "evaluated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    print("=== Hasil Evaluasi Model TrueLens AI ===")
    print(json.dumps(metrics_payload, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate TrueLens AI Model on CIFAKE Test Split")
    parser.add_argument("--data_dir", type=str, default="dataset/cifake")
    parser.add_argument("--model_path", type=str, default="ai/saved_model/truelens_efficientnet.keras")
    parser.add_argument("--output_json", type=str, default="ai/saved_model/evaluation_metrics.json")
    args = parser.parse_args()

    if not os.path.exists(args.data_dir) or not os.path.exists(args.model_path):
        print("[INFO] Dataset atau file model .keras belum tersedia. Menyimpan template status evaluasi.")
    else:
        evaluate_truelens_model(args.data_dir, args.model_path, args.output_json)
