import tensorflow as tf
from tensorflow.keras.models import load_model

MODEL_PATH = "C:/Users/Venka/OneDrive/Desktop/medical_ai/medical_ai/backend/models/wound_model.h5"

model = load_model(MODEL_PATH)
model.summary()
