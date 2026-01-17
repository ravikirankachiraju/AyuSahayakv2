import express from "express";
import multer from "multer";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";
import dotenv from "dotenv";

dotenv.config();

const router = express.Router();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============= Directory Setup =============
const uploadDir = path.join(__dirname, "../uploads");
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });

// ============= Multer Config =============
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) =>
    cb(null, `${Date.now()}_${file.originalname.replace(/\s+/g, "_")}`)
});
const upload = multer({ storage });

// ============= POST /api/skin_stage1 =============
router.post("/", upload.single("image"), (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "No image uploaded" });

    const imagePath = req.file.path.replace(/\\/g, "/"); // ✅ Windows-safe
    const symptomText = req.body.symptoms || ""; 
    const pythonScript = path.resolve(__dirname, "../python/skin_stage1.py");

    console.log("📷 Received Image for Stage 1:", imagePath);
    console.log("📝 Symptoms:", symptomText);

    
    const py = spawn("python", [pythonScript, imagePath, symptomText])

    let result = "";
    let errorOutput = "";

    py.stdout.on("data", (data) => (result += data.toString()));
    py.stderr.on("data", (data) => (errorOutput += data.toString()));

    py.on("close", () => {
      if (errorOutput) console.error("🐍 Python Error:\n", errorOutput);
try {
  const startIndex = result.indexOf("###JSON_START###");
  const endIndex = result.indexOf("###JSON_END###");

  if (startIndex === -1 || endIndex === -1) {
    throw new Error("JSON markers not found in Python output");
  }

  const jsonString = result.substring(
    startIndex + "###JSON_START###".length,
    endIndex
  ).trim();

  const parsed = JSON.parse(jsonString);
  console.log("📤 SENDING TO FRONTEND:", JSON.stringify(parsed, null, 2));

  return res.json(parsed);

} catch (err) {
  console.error("❌ JSON Parse Error:", err);
  console.error("⚙️ Raw Output:", result);
  return res.status(500).json({
    error: "Invalid Python output",
    details: err.message,
    pythonError: errorOutput,
    rawOutput: result,
  });
}


    });
  } catch (err) {
    console.error("❌ Server Error:", err);
    return res.status(500).json({ error: "Internal Server Error", details: err.message });
  }
});

export default router;
