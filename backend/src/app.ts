import express, { Request, Response, NextFunction } from "express";
import cors from "cors";
import { videoRoutes } from "@/routes/video.routes";

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Express 5: Ensure req.body is initialized to an object
app.use((req: Request, res: Response, next: NextFunction) => {
  if (!req.body) {
    req.body = {};
  }
  next();
});

// Routes
app.use("/api/v1/video", videoRoutes);

// Basic health check
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok", timestamp: new Date().toISOString() });
});

// Error handling middleware
app.use((err: any, req: Request, res: Response, next: NextFunction) => {
  console.error(err.stack);
  res.status(500).json({
    error: "Internal Server Error",
    message: process.env.NODE_ENV === "development" ? err.message : undefined,
  });
});

export default app;
