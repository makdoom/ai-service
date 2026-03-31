import { Request, Response } from 'express';
import { queueService } from '@/services/queue.service';
import { socketService } from '@/services/socket.service';

class VideoController {
  public async uploadVideo(req: Request, res: Response) {
    try {
      const { videoId, videoUrl } = req.body;

      if (!videoId || !videoUrl) {
        return res.status(400).json({ error: 'videoId and videoUrl are required' });
      }

      console.log(`Uploading video: ${videoId}`);

      // Add to BullMQ queue for processing
      const job = await queueService.addVideoToQueue(videoId, videoUrl);

      // Emit status to socket clients
      socketService.emitToRoom(`video:${videoId}`, 'status', {
        status: 'queued',
        jobId: job.id,
        videoId,
      });

      return res.status(202).json({
        message: 'Video upload processed and queued successfully',
        videoId,
        jobId: job.id,
      });
    } catch (error) {
      console.error('Error uploading video:', error);
      return res.status(500).json({ error: 'Internal Server Error' });
    }
  }

  public async getVideoStatus(req: Request, res: Response) {
    const { videoId } = req.params;
    // In a real app, logic here would check a database
    // For now, returning a mock status
    return res.json({
      videoId,
      status: 'processing', // This should be dynamic
      progress: 45,
    });
  }
}

export const videoController = new VideoController();
