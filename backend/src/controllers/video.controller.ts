import { Request, Response } from "express";
import { queueService } from "@/services/queue.service";
import { socketService } from "@/services/socket.service";

class VideoController {
  public uploadVideo = async (req: Request, res: Response) => {
    try {
      const { videoId, videoUrl } = req.body || {};

      if (!videoId || !videoUrl) {
        return res.status(400).json({
          error: "Bad Request",
          message: "videoId and videoUrl are required in the request body",
        });
      }

      console.log(`Uploading video: ${videoId}`);

      // Add to BullMQ queue for processing
      const job = await queueService.addVideoToQueue(videoId, videoUrl);

      // Emit status to socket clients
      socketService.emitToUser(`video:${videoId}`, "status", {
        status: "queued",
        jobId: job.id,
        videoId,
      });

      return res.status(202).json({
        message: "Video upload processed and queued successfully",
        videoId,
        jobId: job.id,
      });
    } catch (error: any) {
      console.error("Error uploading video:", error);
      return res.status(500).json({
        error: "Internal Server Error",
        message: error.message,
      });
    }
  };

  public getVideoStatus = async (req: Request, res: Response) => {
    const { videoId } = req.params;
    // In a real app, logic here would check a database
    // For now, returning a mock status
    return res.json({
      videoId,
      status: "processing", // This should be dynamic
      progress: 45,
    });
  };

  public handleWebhook = async (req: Request, res: Response) => {
    try {
      console.log(req.body);
      const { video_id, status, result, error } = req.body || {};

      console.log(
        `[webhook]: Received webhook for video ${video_id}: ${status}`,
      );

      if (!video_id) {
        return res.status(400).json({ error: "Missing video_id" });
      }

      // Map snake_case to camelCase for the socket notification
      const socketStatus = status === "completed" ? "completed" : "failed";

      socketService.emitToRoom(`video:${video_id}`, "status", {
        status: socketStatus,
        videoId: video_id,
        result: result || null,
        error: error || (status === "failed" ? "Processing failed" : null),
      });

      return res
        .status(200)
        .json({ message: "Webhook processed successfully" });
    } catch (error: any) {
      console.error("[webhook]: Error handling webhook:", error);
      return res.status(500).json({ error: "Internal Server Error" });
    }
  };
}

export const videoController = new VideoController();
