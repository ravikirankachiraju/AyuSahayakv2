print("RUNNING wound_stage1.py FILE:", __file__)

# =========================================
# wound_stage1.py — FINAL (Merged Output)
# =========================================

import os, sys, json, time, re, pickle
import numpy as np
import cv2
import tensorflow as tf
from PIL import Image
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.efficientnet import preprocess_input
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import faiss
import google.generativeai as genai

# 🔒 Silence TF noise
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.stdout.reconfigure(encoding="utf-8")

# Local imports
sys.path.append(os.path.dirname(__file__))
from wound_cnn_builder import build_wound_cnn
from wound_fusion_builder import build_wound_fusion
from WOUND_QUESTION_BANK import WOUND_QUESTION_BANK


# =========================================
# MAIN
# =========================================
def main():
    print("🔁 Starting Wound Stage 1")
    load_dotenv()

    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: wound_stage1.py <image_path> <symptoms_text>"}))
        return

    image_path = sys.argv[1]
    symptoms_text = sys.argv[2]

    if not os.path.exists(image_path):
        print(json.dumps({"error": "Image not found"}))
        return

    BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

    # -------------------------------------
    # Load classes
    # -------------------------------------
    with open(os.path.join(BASE, "wound_class_names.pkl"), "rb") as f:
        CLASS_NAMES = pickle.load(f)
    NUM_CLASSES = len(CLASS_NAMES)

    # -------------------------------------
    # Load CNN + extractor
    # -------------------------------------
    cnn = build_wound_cnn(NUM_CLASSES)
    cnn.load_weights(os.path.join(BASE, "wound_cnn.weights.h5"))

    feature_extractor = tf.keras.Model(
        cnn.input,
        cnn.get_layer("image_features").output
    )

    # -------------------------------------
    # Load Fusion
    # -------------------------------------
    fusion = build_wound_fusion(512, 384, NUM_CLASSES)
    fusion.load_weights(os.path.join(BASE, "wound_fusion.weights.h5"))

    # -------------------------------------
    # Encoders
    # -------------------------------------
    text_encoder = SentenceTransformer("all-MiniLM-L6-v2")

    # -------------------------------------
    # Image → embedding
    # -------------------------------------
    img = Image.open(image_path).convert("RGB").resize((150, 150))
    arr = preprocess_input(img_to_array(img))
    img_emb = feature_extractor.predict(arr[None], verbose=0)

    # -------------------------------------
    # TRUE Grad-CAM
    # -------------------------------------
    last_conv = next(l.name for l in reversed(cnn.layers) if isinstance(l, tf.keras.layers.Conv2D))
    cam_model = tf.keras.Model(cnn.input, cnn.get_layer(last_conv).output)

    conv_out = cam_model(arr[None])[0]
    heatmap = np.maximum(np.mean(conv_out, axis=-1), 0)
    heatmap /= heatmap.max() + 1e-8

    original = cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2RGB)
    heatmap = cv2.resize(heatmap, (original.shape[1], original.shape[0]))
    heatmap_color = cv2.applyColorMap((255 * heatmap).astype(np.uint8), cv2.COLORMAP_JET)

    overlay = original.copy()
    mask = heatmap > np.percentile(heatmap, 85)
    overlay[mask] = cv2.addWeighted(original[mask], 0.65, heatmap_color[mask], 0.35, 0)

    gradcam_dir = os.path.join(os.path.dirname(__file__), "..", "uploads", "gradcam")
    os.makedirs(gradcam_dir, exist_ok=True)
    fname = f"wound_gradcam_{int(time.time())}.png"
    cv2.imwrite(os.path.join(gradcam_dir, fname), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

    # -------------------------------------
    # Symptom normalization (same as File-2)
    # -------------------------------------
    keyword_map = {
        "red":"redness","pain":"pain","tender":"tenderness","burn":"burning",
        "swel":"swelling","blister":"blistering","bleed":"bleeding",
        "pus":"fluid discharge","smell":"foul smell","slow":"slow healing"
    }

    mapped = "unspecified wound complaint"
    txt = symptoms_text.lower()
    for k, v in keyword_map.items():
        if k in txt:
            mapped = v
            break

    txt_emb = text_encoder.encode([mapped], convert_to_numpy=True)

    # -------------------------------------
    # Fusion prediction
    # -------------------------------------
    probs = fusion.predict([img_emb, txt_emb], verbose=0)[0]
    top3 = probs.argsort()[-3:][::-1]
    top3_classes = [CLASS_NAMES[i] for i in top3]
    top3_probs = [float(probs[i]) for i in top3]

    # -------------------------------------
    # RAG Retrieval (FAISS)
    # -------------------------------------
    def normalize(x):
        return re.sub(r"\([^)]*\)", "", x.lower()).replace("-", " ").strip()

    RAG_FILE = os.path.join(os.path.dirname(__file__), "..", "rag_data", "wound.txt")
    with open(RAG_FILE, "r", encoding="utf-8") as f:
        raw = f.read()

    sections = re.split(r'\n(?=\d+\.\s)', raw.strip())
    rag = {}
    for s in sections:
        m = re.match(r'(\d+)\.\s*([A-Za-z\s’\'\-()]+)', s)
        if m:
            rag[normalize(m.group(2))] = s.strip()

    keys = list(rag.keys())
    emb = text_encoder.encode(keys, convert_to_numpy=True)
    index = faiss.IndexFlatL2(emb.shape[1])
    index.add(emb)

    rag_summary = ""
    for d in top3_classes:
        k = normalize(d)
        if k not in rag:
            qv = text_encoder.encode([k], convert_to_numpy=True)
            _, I = index.search(qv, 1)
            k = keys[I[0][0]]
        rag_summary += f"### {d}\n{rag[k]}\n\n"

    # -------------------------------------
    # Question selection + Gemini rewrite
    # -------------------------------------
    selected = []
    for d in top3_classes:
        qs = WOUND_QUESTION_BANK.get(d, [])
        if qs:
            selected.append(qs[0])

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    gemini = genai.GenerativeModel("gemini-2.5-flash")

    prompt = "Rewrite these wound assessment questions in simple nurse-friendly language:\n" + \
             "\n".join(f"- {q['canonical']}" for q in selected)

    raw = gemini.generate_content(prompt).text.split("\n")

    clean = [re.sub(r"^[\-\d\.\)]\s*", "", l).strip()
             for l in raw if l.strip().endswith("?")]

    while len(clean) < len(selected):
        clean.append(selected[len(clean)]["canonical"])

    final_questions = []
    for o, d, q in zip(selected, top3_classes, clean):
        final_questions.append({
            "id": o["id"],
            "canonical": o["canonical"],
            "display": q,
            "disease": d,
            "feature_phrases": o["feature_phrases"]
        })

    # -------------------------------------
    # FINAL OUTPUT (SAME AS FILE-2)
    # -------------------------------------
    result = {
        "top3_classes": top3_classes,
        "top3_probs": top3_probs,
        "rag_summary": rag_summary,
        "questions": final_questions,
        "gradcam_url": f"/backend/uploads/gradcam/{fname}"
    }

    print("###JSON_START###")
    print(json.dumps(result, ensure_ascii=False))
    print("###JSON_END###")


if __name__ == "__main__":
    main()
