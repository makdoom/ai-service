import { Worker, Job } from "bullmq";
import { VIDEO_QUEUE_NAME, videoQueueOptions } from "@/services/queue.service";
import { socketService } from "@/services/socket.service";

export const initVideoWorker = () => {
  const worker = new Worker(
    VIDEO_QUEUE_NAME,
    async (job: Job) => {
      const { videoId, videoUrl } = job.data;
      const aiServiceUrl =
        process.env.AI_SERVICE_URL || "http://localhost:8000";

      console.log(`[worker]: Processing video ${videoId} from job ${job.id}`);

      // 1. Emit "processing" status
      socketService.emitToRoom(`video:${videoId}`, "status", {
        status: "processing",
        videoId,
        jobId: job.id,
      });

      try {
        // 2. Call Python FastAPI service with webhook
        const response = await fetch(`${aiServiceUrl}/api/v1/ingest-video`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Auth-Token": process.env.AUTH_TOKEN,
          },
          body: JSON.stringify({
            video_id: videoId,
            video_url: videoUrl,
            webhook_url: `${process.env.BACKEND_URL}/api/v1/video/webhook`,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            `AI Service returned ${response.status}: ${JSON.stringify(errorData)}`,
          );
        }

        const result = await response.json();
        console.log(
          `[worker]: Acknowledgement from AI Service for video ${videoId}:`,
        );

        // We don't emit "completed" yet. The AI Service will call our webhook instead.
        return result;
      } catch (error: any) {
        console.error(`[worker]: Error processing video ${videoId}:`, error);

        // 4. Emit "failed" status
        socketService.emitToRoom(`video:${videoId}`, "status", {
          status: "failed",
          videoId,
          jobId: job.id,
          error: error.message,
        });

        throw error;
      }
    },
    videoQueueOptions,
  );

  worker.on("completed", (job) => {
    console.log(`[worker]: Job ${job.id} completed`);
  });

  worker.on("failed", (job, err) => {
    console.error(`[worker]: Job ${job?.id} failed:`, err);
  });

  console.log(`[worker]: Video processing worker initialized`);

  return worker;
};
