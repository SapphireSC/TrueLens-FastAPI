"""
TrueLens AI - Pipeline Pelatihan Model Transfer Learning EfficientNet-B0
Dataset: CIFAKE: Real and AI-Generated Synthetic Images (Kaggle)
URL Dataset: https://www.kaggle.com/datasets/birdy654/cifake-real-and-ai-generated-synthetic-images
"""
import os
import json
import argparse
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42


def build_datasets(dataset_dir: str):
    """
    Memuat dataset CIFAKE dari struktur direktori:
    dataset_dir/
      train/
        REAL/
        FAKE/
      test/
        REAL/
        FAKE/
    Kelas dikodekan secara eksplisit: REAL = 0, FAKE (AI-Generated) = 1.
    """
    train_dir = os.path.join(dataset_dir, "train")
    test_dir = os.path.join(dataset_dir, "test")

    class_names = ["REAL", "FAKE"]

    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        validation_split=0.10,
        subset="training",
        seed=SEED,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="binary",
        class_names=class_names,
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        validation_split=0.10,
        subset="validation",
        seed=SEED,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="binary",
        class_names=class_names,
    )

    test_ds = tf.keras.utils.image_dataset_from_directory(
        test_dir,
        image_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        label_mode="binary",
        class_names=class_names,
        shuffle=False,
    )

    # PENTING: EfficientNetB0 di Keras sudah memiliki layer Rescaling internal.
    # Jangan membagi piksel dengan 255.0 secara manual! Gunakan preprocess_input (skala float32 [0, 255]).
    def preprocess_batch(images, labels):
        images = tf.cast(images, tf.float32)
        images = preprocess_input(images)
        return images, labels

    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.map(preprocess_batch, num_parallel_calls=autotune).prefetch(autotune)
    val_ds = val_ds.map(preprocess_batch, num_parallel_calls=autotune).prefetch(autotune)
    test_ds = test_ds.map(preprocess_batch, num_parallel_calls=autotune).prefetch(autotune)

    return train_ds, val_ds, test_ds


def build_truelens_model() -> tuple[tf.keras.Model, tf.keras.Model]:
    """
    Membangun arsitektur Transfer Learning EfficientNet-B0 dengan Custom Classification Head.
    """
    inputs = layers.Input(shape=(224, 224, 3), name="input_image")

    # Data Augmentation (Hanya aktif saat training=True)
    augmentation = models.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.08),
            layers.RandomZoom(0.10),
        ],
        name="data_augmentation",
    )
    x = augmentation(inputs)

    # Backbone Pre-trained ImageNet
    base_model = EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_tensor=x,
    )
    base_model.trainable = False  # Dibekukan pada Tahap 1 (Warm-up Head)

    # Custom Classification Head
    x = layers.GlobalAveragePooling2D(name="global_avg_pool")(base_model.output)
    x = layers.BatchNormalization(name="head_batch_norm")(x)
    x = layers.Dropout(0.40, name="head_dropout_1")(x)
    x = layers.Dense(128, activation="relu", name="head_dense_128")(x)
    x = layers.Dropout(0.20, name="head_dropout_2")(x)
    outputs = layers.Dense(1, activation="sigmoid", name="sigmoid_output")(x)

    model = models.Model(inputs=inputs, outputs=outputs, name="TrueLens_EfficientNetB0")
    return model, base_model


def train_two_stage(dataset_dir: str, output_model_path: str, epochs_warmup: int = 5, epochs_finetune: int = 10):
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    train_ds, val_ds, _ = build_datasets(dataset_dir)
    model, base_model = build_truelens_model()

    # ------------------------------------------------------------------
    # TAHAP 1: WARM-UP CLASSIFICATION HEAD (Backbone Dibekukan)
    # ------------------------------------------------------------------
    print("=== [Tahap 1] Melatih Custom Classification Head (Warm-up) ===")
    model.compile(
        optimizer=optimizers.AdamW(learning_rate=1e-3, weight_decay=1e-4),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="auc"),
        ],
    )

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs_warmup,
    )

    # ------------------------------------------------------------------
    # TAHAP 2: FINE-TUNING 30 LAYER TERATAS BACKBONE
    # ------------------------------------------------------------------
    print("=== [Tahap 2] Fine-Tuning 30 Layer Teratas EfficientNet-B0 ===")
    base_model.trainable = True
    for layer in base_model.layers[:-30]:
        layer.trainable = False
    for layer in base_model.layers:
        if isinstance(layer, layers.BatchNormalization):
            layer.trainable = False  # Jaga statistik mean/var BatchNorm tetap stabil

    model.compile(
        optimizer=optimizers.AdamW(learning_rate=1e-4, weight_decay=1e-5),
        loss="binary_crossentropy",
        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="auc"),
        ],
    )

    cb_list = [
        callbacks.ModelCheckpoint(
            filepath=output_model_path,
            monitor="val_loss",
            save_best_only=True,
            verbose=1,
        ),
        callbacks.EarlyStopping(
            monitor="val_loss",
            patience=3,
            restore_best_weights=True,
            verbose=1,
        ),
        callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-6,
            verbose=1,
        ),
    ]

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs_finetune,
        callbacks=cb_list,
    )

    model.save(output_model_path)
    print(f"Model berhasil disimpan ke: {output_model_path}")
    return history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train TrueLens AI EfficientNet-B0 on CIFAKE Dataset")
    parser.add_argument("--data_dir", type=str, default="dataset/cifake", help="Path ke folder dataset CIFAKE")
    parser.add_argument(
        "--output_model",
        type=str,
        default="ai/saved_model/truelens_efficientnet.keras",
        help="Path penyimpanan model .keras",
    )
    parser.add_argument("--warmup_epochs", type=int, default=5)
    parser.add_argument("--finetune_epochs", type=int, default=10)
    args = parser.parse_args()

    if not os.path.exists(args.data_dir):
        print(
            f"[INFO] Direktori dataset '{args.data_dir}' belum ditemukan. "
            "Unduh CIFAKE dari https://www.kaggle.com/datasets/birdy654/cifake-real-and-ai-generated-synthetic-images "
            "dan ekstrak ke folder dataset/cifake/{train,test}/{REAL,FAKE}."
        )
    else:
        train_two_stage(args.data_dir, args.output_model, args.warmup_epochs, args.finetune_epochs)
