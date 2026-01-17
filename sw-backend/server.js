import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";

import skinStage1Routes from "./routes/skin_stage1.js";
import skinStage2Routes from "./routes/skin_stage2.js";
import woundStage1Routes from "./routes/wound_stage1.js";
import woundStage2Routes from "./routes/wound_stage2.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5001;
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.use(cors());
app.use(express.json());
app.use("/backend/output", express.static(path.join(__dirname, "output")));
app.use("/backend/uploads", express.static(path.join(__dirname, "uploads")));

app.use("/api/skin_stage1", skinStage1Routes);
app.use("/api/skin_stage2", skinStage2Routes);
app.use("/api/wound_stage1", woundStage1Routes);
app.use("/api/wound_stage2", woundStage2Routes);

app.get("/", (req, res) => res.send("🧠 Medical AI Backend is Running!"));

app.listen(PORT, () => console.log(`✅ Server running on port ${PORT}`));
