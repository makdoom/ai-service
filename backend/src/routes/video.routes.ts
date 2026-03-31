import { Router } from "express";
import { videoController } from "@/controllers/video.controller";

const router = Router();

// Endpoint for triggering video processing
router.post("/ingest", videoController.uploadVideo);

// Endpoint for checking status of video
router.get("/:videoId/status", videoController.getVideoStatus);

// Webhook endpoint for the AI service to call upon completion
router.post("/webhook", videoController.handleWebhook);

export const videoRoutes = router;
