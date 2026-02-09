# cnn_builder.py — SKIN (MATCH TRAINING)

from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
from tensorflow.keras.models import Model
import tensorflow as tf


def build_skin_cnn(num_classes):
    base = EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=(96, 96, 3)
    )

    for layer in base.layers:
        layer.trainable = False

    x = GlobalAveragePooling2D()(base.output)
    x = Dense(64, activation="relu", name="image_features")(x)

    out = Dense(num_classes, activation="softmax")(x)

    return Model(base.input, out, name="skin_cnn")