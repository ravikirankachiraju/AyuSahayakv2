# =========================================
# skin_stage1.py — FINAL
# File-2 inference + TRUE Grad-CAM
# File-1 style RAG + Question Bank
# Gemini ONLY for language rewriting
# =========================================

import os, sys, json, time, pickle, re
import numpy as np
import cv2
import tensorflow as tf
from PIL import Image
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.efficientnet import preprocess_input
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import google.generativeai as genai

# -----------------------------
# ENV
# -----------------------------
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(__file__))

from cnn_builder import build_skin_cnn
from fusion_model_builder import build_skin_fusion
from QUESTION_BANK import QUESTION_BANK

# -----------------------------
# Gemini (LANGUAGE ONLY)
# -----------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print(json.dumps({"error": "Missing GEMINI_API_KEY"}))
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)
gemini = genai.GenerativeModel("gemini-2.5-flash")

# -----------------------------
# FILE-1 STYLE UTILITIES
# -----------------------------

UNIVERSAL_SYMPTOMS = [
    "redness", "itching", "pain", "swelling", "blistering", "scaling",
    "circular rash", "burning", "fluid filled bumps", "skin peeling",
    "yellow thick nails", "crusting", "tingling pain", "fever rash",
    "track-like rash"
]

def semantic_map(text, text_model):
    univ_emb = text_model.encode(UNIVERSAL_SYMPTOMS, convert_to_numpy=True)
    univ_emb /= np.linalg.norm(univ_emb, axis=1, keepdims=True)

    emb = text_model.encode([text], convert_to_numpy=True)
    emb /= np.linalg.norm(emb)

    sims = np.dot(univ_emb, emb.T).reshape(-1)
    return UNIVERSAL_SYMPTOMS[int(np.argmax(sims))]

def normalize_name(name: str) -> str:
    name = re.sub(r"^[A-Z]{2}-", "", name, flags=re.I)
    name = re.sub(r"\([^)]*\)", "", name)
    return name.replace("-", " ").replace("_", " ").lower().strip()

def load_rag(rag_path):
    raw_text = open(rag_path, "r", encoding="utf-8").read()
    sections = re.split(r'\n(?=\d+\. )', raw_text.strip())
    rag_data = {}

    for sec in sections:
        m = re.match(r'(\d+)\.\s*([A-Za-z\s’\'\-()]+)', sec)
        if m:
            name = re.sub(r"\([^)]*\)", "", m.group(2)).lower().strip()
            rag_data[name] = sec.strip()

    return rag_data

# Normalize QUESTION_BANK keys
NORMALIZED_QBANK = {
    normalize_name(k): v for k, v in QUESTION_BANK.items()
}

# =========================================
# MAIN
# =========================================

def main():
    print("🔁 Starting Skin Stage-1 (File-2 Engine)")

    image_path = sys.argv[1]
    symptoms_text = sys.argv[2]

    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

    # -----------------------------
    # Load class names
    # -----------------------------
    with open(os.path.join(BASE, "skin_class_names.pkl"), "rb") as f:
        CLASS_NAMES = pickle.load(f)

    NUM_CLASSES = len(CLASS_NAMES)

    # -----------------------------
    # Load models (UNCHANGED)
    # -----------------------------
    cnn = build_skin_cnn(NUM_CLASSES)
    cnn.load_weights(os.path.join(BASE, "skin_cnn.weights.h5"))

    fusion = build_skin_fusion(512, 384, NUM_CLASSES)
    fusion.load_weights(os.path.join(BASE, "skin_fusion.weights.h5"))

    feature_extractor = tf.keras.Model(
        cnn.input, cnn.get_layer("image_features").output
    )

    text_encoder = SentenceTransformer("all-MiniLM-L6-v2")

    # -----------------------------
    # Image preprocessing
    # -----------------------------
    img = Image.open(image_path).convert("RGB").resize((150, 150))
    arr = preprocess_input(img_to_array(img))
    arr_batch = arr[None, ...]

    img_emb = feature_extractor.predict(arr_batch, verbose=0)

    # ======================================================
    # 🔥 TRUE GRAD-CAM (UNCHANGED)
    # ======================================================
    conv_layers = [l for l in cnn.layers if isinstance(l, tf.keras.layers.Conv2D)]
    target_layer = conv_layers[-2].name

    grad_model = tf.keras.Model(
        inputs=cnn.input,
        outputs=[cnn.get_layer(target_layer).output, cnn.output]
    )

    with tf.GradientTape() as tape:
        conv_out, preds = grad_model(arr_batch)
        class_idx = tf.argmax(preds[0])
        loss = preds[:, class_idx]

    grads = tape.gradient(loss, conv_out)
    weights = tf.reduce_mean(grads, axis=(1, 2))
    cam = tf.reduce_sum(weights * conv_out, axis=-1)[0]

    heatmap = tf.maximum(cam, 0)
    heatmap /= tf.reduce_max(heatmap) + 1e-8
    heatmap = heatmap.numpy()

    original = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)

    heatmap = cv2.resize(
        heatmap,
        (original.shape[1], original.shape[0]),
        interpolation=cv2.INTER_LINEAR
    )

    heatmap = cv2.GaussianBlur(heatmap, (31, 31), 0)

    heatmap_color = cv2.applyColorMap(
        np.uint8(255 * heatmap),
        cv2.COLORMAP_JET
    )

    overlay = cv2.addWeighted(original, 0.6, heatmap_color, 0.4, 0)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "uploads", "gradcam")
    os.makedirs(out_dir, exist_ok=True)

    fname = f"skin_gradcam_{int(time.time())}.png"
    cv2.imwrite(
        os.path.join(out_dir, fname),
        cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
    )

    # -----------------------------
    # Prediction (UNCHANGED)
    # -----------------------------
    txt_emb = text_encoder.encode([symptoms_text], convert_to_numpy=True)
    probs = fusion.predict([img_emb, txt_emb], verbose=0)[0]
    top3 = probs.argsort()[-3:][::-1]
    top3_classes = [CLASS_NAMES[i] for i in top3]

    # ======================================================
    # 🧠 FILE-1 STYLE ENRICHMENT
    # ======================================================
    mapped_symptom = semantic_map(symptoms_text, text_encoder)

    rag_data = load_rag(
        os.path.join(os.path.dirname(__file__), "..", "rag_data", "skin.txt")
    )

    rag_summary = ""
    for i, disease in enumerate(top3_classes):
        key = normalize_name(disease)
        retrieved = rag_data.get(key, "")
        rag_summary += f"[{i+1}] {disease}\n{retrieved}\n\n"

    # ======================================================
    # ❓ QUESTION BANK (Deterministic)
    # ======================================================
    selected_questions = []

    for disease in top3_classes:
        key = normalize_name(disease)
        q_list = NORMALIZED_QBANK.get(key, [])
        if q_list:
            selected_questions.append(q_list[0])  # deterministic

    selected_questions = selected_questions[:3]

    # -----------------------------
    # Gemini rewrite (LANGUAGE ONLY)
    # -----------------------------
    rewrite_prompt = (
        "Rewrite these medical questions in very simple, nurse-friendly language.\n"
        "Do NOT change meaning. One question per line.\n\n" +
        "\n".join(f"- {q['canonical']}" for q in selected_questions)
    )

    rewritten = gemini.generate_content(rewrite_prompt).text.strip().split("\n")
    rewritten = [ln.strip("- ").strip() for ln in rewritten if ln.strip()]

    final_questions = []
    for q, rw, disease in zip(selected_questions, rewritten, top3_classes):
        final_questions.append({
            "id": q["id"],
            "canonical": q["canonical"],
            "display": rw,
            "disease": disease,
            "feature_phrases": q["feature_phrases"]
        })

    # -----------------------------
    # FINAL JSON (File-1 STYLE)
    # -----------------------------
    result = {
        "mapped_symptom": mapped_symptom,
        "top3_classes": top3_classes,
        "top3_probs": [float(probs[i]) for i in top3],
        "gradcam_url": f"/backend/uploads/gradcam/{fname}",
        "questions": final_questions,
        "rag_summary": rag_summary,
        "explainability": "gradcam"
    }

    print("###JSON_START###")
    print(json.dumps(result, ensure_ascii=False))
    print("###JSON_END###")

# =========================================
if __name__ == "__main__":
    main()
