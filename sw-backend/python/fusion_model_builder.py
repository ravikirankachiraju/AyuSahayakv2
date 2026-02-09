# fusion_model_builder.py — SKIN (MATCH TRAINING WITH ABCD)

import tensorflow as tf
from tensorflow.keras.layers import (
    Input, Dense, Dropout, Concatenate
)
from tensorflow.keras.models import Model


def build_skin_fusion(img_dim=64, txt_dim=384, abcd_dim=4, num_classes=8):
    img_in  = Input(shape=(img_dim,),  name="img_in")
    txt_in  = Input(shape=(txt_dim,),  name="txt_in")
    abcd_in = Input(shape=(abcd_dim,), name="abcd_in")

    # Text projection (as trained)
    txt_proj = Dense(64, activation="relu")(txt_in)

    fusion = Concatenate()([img_in, txt_proj, abcd_in])

    x = Dense(96, activation="relu")(fusion)
    x = Dropout(0.6)(x)

    out = Dense(num_classes, activation="softmax")(x)

    return Model(
        inputs=[img_in, txt_in, abcd_in],
        outputs=out,
        name="skin_fusion_model"
    )