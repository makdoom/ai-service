import { Router } from 'express';
import { videoController } from '@/controllers/video.controller';

const router = Router();

// Endpoint for triggering video processing
router.post('/upload', videoController.uploadVideo);

// Endpoint for checking status of video
router.get('/:videoId/status', videoController.getVideoStatus);

export const videoRoutes = router;
