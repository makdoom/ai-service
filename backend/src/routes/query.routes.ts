import { Router } from "express";
import { queryController } from "@/controllers/query.controller";

const router = Router();

// Endpoint for triggering video processing
router.post("/", queryController.queryVideo);

export const queryRoutes = router;
