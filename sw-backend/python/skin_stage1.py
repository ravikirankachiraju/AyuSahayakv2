# =========================================
# skin_stage1.py — FINAL (MERGED & TRAINING-CORRECT)
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

from cnn_builder import build_skin_cnn
from fusion_model_builder import build_skin_fusion
from QUESTION_BANK import QUESTION_BANK

# -----------------------------
# ENV
# -----------------------------
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.stdout.reconfigure(encoding="utf-8")

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
    "redness","itching","pain","swelling","blistering","scaling",
    "circular rash","burning","fluid filled bumps","skin peeling",
    "yellow thick nails","crusting","tingling pain","fever rash",
    "track-like rash"
]

def semantic_map(text, model):
    U = model.encode(UNIVERSAL_SYMPTOMS, convert_to_numpy=True)
    U /= np.linalg.norm(U, axis=1, keepdims=True)
    v = model.encode([text], convert_to_numpy=True)
    v /= np.linalg.norm(v)
    return UNIVERSAL_SYMPTOMS[int(np.argmax(U @ v.T))]

def normalize_name(name: str) -> str:
    name = re.sub(r"^[A-Z]{2}-", "", name, flags=re.I)
    name = re.sub(r"\([^)]*\)", "", name)
    return name.replace("-", " ").replace("_", " ").lower().strip()

def load_rag(rag_path):
    raw = open(rag_path, "r", encoding="utf-8").read()
    sections = re.split(r'\n(?=\d+\. )', raw.strip())
    rag = {}
    for sec in sections:
        m = re.match(r'(\d+)\.\s*([A-Za-z\s’\'\-()]+)', sec)
        if m:
            key = normalize_name(m.group(2))
            rag[key] = sec.strip()
    return rag

NORMALIZED_QBANK = {
    normalize_name(k): v for k, v in QUESTION_BANK.items()
}

# -----------------------------
# OpenCV ABC extraction
# -----------------------------
def extract_abc(image_path):
    img = cv2.imread(image_path)
    img = cv2.resize(img, (96,96))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # A – Asymmetry
    A = np.mean(np.abs(gray[:,:48] - cv2.flip(gray[:,48:],1))) / 255.0
    # B – Border
    edges = cv2.Canny(gray, 80, 160)
    B = np.sum(edges > 0) / edges.size
    # C – Color
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    C = np.std(hsv[:,:,1]) / 255.0

    return A, B, C

def interpret_abc(A, B, C, D):
    def bar(v, max_blocks=6):
        filled = int(round(v * max_blocks))
        return "▓" * filled + "░" * (max_blocks - filled)

    return [
        {
            "label": "Asymmetry",
            "value": round(float(A), 2),
            "bar": bar(A),
            "note": "Higher means left and right sides look less similar"
        },
        {
            "label": "Border",
            "value": round(float(B), 2),
            "bar": bar(B),
            "note": "Higher means rough or irregular edges"
        },
        {
            "label": "Color variation",
            "value": round(float(C), 2),
            "bar": bar(C),
            "note": "Higher means multiple colors present"
        },
        {
            "label": "Diameter",
            "value": f"{int(D)} mm",
            "bar": "▓" * 8,
            "note": "User-reported lesion size"
        }
    ]

# =========================================
# MAIN
# =========================================
def main():
    print("🔁 Starting Skin Stage-1 (FINAL Engine)")

    image_path   = sys.argv[1]
    symptoms_txt = sys.argv[2]
    diameter_mm  = float(sys.argv[3]) if len(sys.argv) > 3 else 50.0

    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

    # -----------------------------
    # Load class names
    # -----------------------------
    with open(os.path.join(BASE, "skin_class_names.pkl"), "rb") as f:
        CLASS_NAMES = pickle.load(f)

    NUM_CLASSES = len(CLASS_NAMES)

    # -----------------------------
    # Load models (MATCH TRAINING)
    # -----------------------------
    cnn = build_skin_cnn(NUM_CLASSES)
    cnn.load_weights(os.path.join(BASE, "skin_cnn.weights.h5"))

    fusion = build_skin_fusion(
        img_dim=64, txt_dim=384, abcd_dim=4,
        num_classes=NUM_CLASSES
    )
    fusion.load_weights(os.path.join(BASE, "skin_fusion.weights.h5"))

    feature_extractor = tf.keras.Model(
        cnn.input, cnn.get_layer("image_features").output
    )

    text_encoder = SentenceTransformer("all-MiniLM-L6-v2")

    # -----------------------------
    # Image → embedding
    # -----------------------------
    img = Image.open(image_path).convert("RGB").resize((96,96))
    arr = preprocess_input(img_to_array(img))[None,...]
    img_emb = feature_extractor.predict(arr, verbose=0)

    # -----------------------------
    # ABCD
    # -----------------------------
    A,B,C = extract_abc(image_path)
    abc_ui = interpret_abc(A, B, C, diameter_mm)

    abcd = np.array([[A, B, C, diameter_mm]])

    # -----------------------------
    # Text
    # -----------------------------
    txt_emb = text_encoder.encode([symptoms_txt], convert_to_numpy=True)

    # ======================================================
    # 🔥 TRUE GRAD-CAM
    # ======================================================
    conv_layers = [l for l in cnn.layers if isinstance(l, tf.keras.layers.Conv2D)]
    target_layer = conv_layers[-1].name

    grad_model = tf.keras.Model(
        inputs=cnn.input,
        outputs=[cnn.get_layer(target_layer).output, cnn.output]
    )

    with tf.GradientTape() as tape:
        conv_out, preds = grad_model(arr)
        class_idx = tf.argmax(preds[0])
        loss = preds[:, class_idx]

    grads = tape.gradient(loss, conv_out)
    weights = tf.reduce_mean(grads, axis=(1,2))
    cam = tf.reduce_sum(weights * conv_out, axis=-1)[0]

    heatmap = np.maximum(cam, 0)
    heatmap /= heatmap.max() + 1e-8

    original = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
    heatmap = cv2.resize(heatmap, (original.shape[1], original.shape[0]))
    heatmap = cv2.applyColorMap(np.uint8(255*heatmap), cv2.COLORMAP_JET)
    overlay = cv2.addWeighted(original, 0.6, heatmap, 0.4, 0)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "uploads", "gradcam")
    os.makedirs(out_dir, exist_ok=True)
    fname = f"skin_gradcam_{int(time.time())}.png"
    cv2.imwrite(os.path.join(out_dir, fname), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

    # -----------------------------
    # Prediction
    # -----------------------------
    probs = fusion.predict([img_emb, txt_emb, abcd], verbose=0)[0]
    top3 = probs.argsort()[-3:][::-1]
    top3_classes = [CLASS_NAMES[i] for i in top3]

    # -----------------------------
    # RAG
    # -----------------------------
    rag_data = load_rag(os.path.join(os.path.dirname(__file__), "..", "rag_data", "skin.txt"))

    rag_summary = ""
    for i, d in enumerate(top3_classes):
        rag_summary += f"[{i+1}] {d}\n{rag_data.get(normalize_name(d), '')}\n\n"

    # -----------------------------
    # QUESTION BANK
    # -----------------------------
    selected_questions = []
    for d in top3_classes:
        qlist = NORMALIZED_QBANK.get(normalize_name(d), [])
        if qlist:
            selected_questions.append(qlist[0])

    rewrite_prompt = (
       "Rewrite each medical question into ONE very simple, nurse-friendly sentence.\n"
       "Rules:\n"
       "1. Return ONLY the rewritten questions\n"
       "2. One question per line\n"
       "3. NO headings\n"
       "4. NO bullet points\n"
       "5. Keep the same order\n\n" +
       "\n".join(q["canonical"] for q in selected_questions)
     )

    raw = gemini.generate_content(rewrite_prompt).text

    lines = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("here are"):
            continue
        if line.startswith(("-", "*", "•")):
            line = line.lstrip("-*• ").strip()
        lines.append(line)
    
    rewritten = lines[:len(selected_questions)]


    final_questions = []
    for q, rw, d in zip(selected_questions, rewritten, top3_classes):
        final_questions.append({
            "id": q["id"],
            "canonical": q["canonical"],
            "display": rw,
            "disease": d,
            "feature_phrases": q["feature_phrases"]
        })

    # -----------------------------
    # FINAL JSON
    # -----------------------------
    result = {
        "mapped_symptom": semantic_map(symptoms_txt, text_encoder),
        "top3_classes": top3_classes,
        "top3_probs": [float(probs[i]) for i in top3],
        "gradcam_url": f"/backend/uploads/gradcam/{fname}",
        "questions": final_questions,
        "rag_summary": rag_summary,
        "abc_values": abc_ui,

        "explainability": "ABCD + GradCAM"
    }

    print("###JSON_START###")
    print(json.dumps(result, ensure_ascii=False))
    print("###JSON_END###")

# =========================================
if __name__ == "__main__":
    main()