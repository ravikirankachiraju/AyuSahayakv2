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

const uploadDir = path.join(__dirname, "../uploads");
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) =>
    cb(null, `${Date.now()}_${file.originalname.replace(/\s+/g, "_")}`)
});
const upload = multer({ storage });

router.post("/", upload.single("image"), (req, res) => {
  if (!req.file) return res.status(400).json({ error: "No image uploaded" });

  const imagePath = req.file.path.replace(/\\/g, "/");
  const pythonScript = path.resolve(__dirname, "../python/wound_stage1.py");

  console.log("📷 Received Image for Wound Stage 1:", imagePath);

  const symptoms = req.body.symptoms || "";
  const py = spawn("python", [pythonScript, imagePath, symptoms]);


  let result = "", errorOutput = "";
  py.stdout.on("data", (data) => (result += data.toString()));
  py.stderr.on("data", (data) => (errorOutput += data.toString()));

  py.on("close", () => {
    if (errorOutput) console.error("🐍 Python Error:\n", errorOutput);
    try {
      const jsonMatches = result.match(/{[\s\S]*}/g);
      if (!jsonMatches) throw new Error("No valid JSON found");
      const parsed = JSON.parse(jsonMatches.pop());
      res.json(parsed);
    } catch (err) {
      res.status(500).json({ error: "Invalid Python output", raw: result, stderr: errorOutput });
    }
  });
});

export default router;
