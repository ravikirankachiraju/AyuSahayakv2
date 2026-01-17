import express from "express";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

dotenv.config();

const router = express.Router();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ============= POST /api/skin_stage2 =============
router.post("/", (req, res) => {
  try {
    const { top3_classes, top3_probs, rag_summary, questions, answers } = req.body;

    if (!answers || !Array.isArray(answers)) {
      return res.status(400).json({ error: "Answers array missing or invalid" });
    }

    const payload = JSON.stringify({
      top3_classes,
      top3_probs,
      rag_summary,
      questions,
      answers
    });

    const pythonScript = path.resolve(__dirname, "../python/skin_stage2.py");
    const py = spawn("python", [pythonScript, payload]);

    let result = "";
    let errorOutput = "";

    py.stdout.on("data", (data) => (result += data.toString()));
    py.stderr.on("data", (data) => (errorOutput += data.toString()));

    py.on("close", () => {
      if (errorOutput) console.error("🐍 Python Error:\n", errorOutput);

      try {
        const jsonMatches = result.match(/{[\s\S]*}/g);
        if (!jsonMatches || jsonMatches.length === 0)
          throw new Error("No valid JSON in Python output");

        const cleanJSON = jsonMatches[jsonMatches.length - 1].trim();
        const parsed = JSON.parse(cleanJSON);
        return res.json(parsed);
      } catch (err) {
        console.error("❌ JSON Parse Error:", err);
        console.error("⚙️ Raw Output:", result);
        return res.status(500).json({
          error: "Invalid Python output",
          details: err.message,
          pythonError: errorOutput,
          rawOutput: result
        });
      }
    });
  } catch (err) {
    console.error("🚨 Server Error:", err);
    return res.status(500).json({ error: "Internal Server Error", details: err.message });
  }
});

export default router;
