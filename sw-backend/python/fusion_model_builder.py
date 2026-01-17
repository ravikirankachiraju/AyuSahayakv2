# fusion_model_builder.py — SKIN (FIXED)
# MUST MATCH TRAINING EXACTLY

import tensorflow as tf
from tensorflow.keras.layers import (
    Input, Dense, Dropout, BatchNormalization, Concatenate
)
from tensorflow.keras.models import Model


def build_skin_fusion(img_dim=512, txt_dim=384, num_classes=8):
    img_in = Input(shape=(img_dim,), name="img_in")
    txt_in = Input(shape=(txt_dim,), name="txt_in")

    # Text projection (MATCH TRAINING)
    txt_proj = Dense(img_dim, activation="relu")(txt_in)
    txt_proj = BatchNormalization()(txt_proj)
    txt_proj = Dropout(0.2)(txt_proj)

    fusion = Concatenate()([img_in, txt_proj])

    # Block 1
    x = Dense(512, activation="relu")(fusion)
    x = BatchNormalization()(x)
    x = Dropout(0.3)(x)

    # Block 2  ✅ NO BatchNorm here
    x = Dense(256, activation="relu")(x)
    x = Dropout(0.2)(x)

    # Output
    out = Dense(num_classes, activation="softmax")(x)

    return Model([img_in, txt_in], out, name="skin_fusion_model")