import express from "express";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";

dotenv.config();
const router = express.Router();
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

router.post("/", (req, res) => {
  try {
    const payload = JSON.stringify(req.body);
    const pythonScript = path.resolve(__dirname, "../python/wound_stage2.py");
    const py = spawn("python", [pythonScript, payload]);

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
  } catch (err) {
    res.status(500).json({ error: "Server error", details: err.message });
  }
});

export default router;
