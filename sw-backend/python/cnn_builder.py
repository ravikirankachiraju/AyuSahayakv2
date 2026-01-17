# cnn_builder.py — SKIN (EfficientNet)
# SAME architecture as build_wound_cnn

from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.models import Model
import tensorflow as tf


def build_skin_cnn(num_classes):
    base = EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=(150, 150, 3)
    )

    for layer in base.layers:
        layer.trainable = False

    x = tf.keras.layers.GlobalAveragePooling2D()(base.output)
    x = Dense(512, activation="relu", name="image_features")(x)
    x = BatchNormalization()(x)
    x = Dropout(0.5)(x)

    x = Dense(128, activation="relu")(x)
    x = Dropout(0.4)(x)

    out = Dense(num_classes, activation="softmax")(x)
    return Model(base.input, out)