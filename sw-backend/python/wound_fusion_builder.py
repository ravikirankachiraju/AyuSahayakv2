import tensorflow as tf
from tensorflow.keras.layers import (
    Input, Dense, Dropout, BatchNormalization, Concatenate
)
from tensorflow.keras.models import Model

def build_wound_fusion(img_dim, txt_dim, num_classes):
    img_in = Input(shape=(img_dim,), name="img_in")
    txt_in = Input(shape=(txt_dim,), name="txt_in")

    txt_proj = Dense(img_dim, activation="relu")(txt_in)
    txt_proj = BatchNormalization()(txt_proj)
    txt_proj = Dropout(0.2)(txt_proj)

    fusion = Concatenate()([img_in, txt_proj])

    x = Dense(512, activation="relu")(fusion)
    x = BatchNormalization()(x)
    x = Dropout(0.3)(x)

    x = Dense(256, activation="relu")(x)
    x = BatchNormalization()(x)
    x = Dropout(0.2)(x)

    x = Dense(128, activation="relu")(x)
    x = Dropout(0.15)(x)

    out = Dense(num_classes, activation="softmax")(x)

    return Model([img_in, txt_in], out, name="wound_fusion_model")