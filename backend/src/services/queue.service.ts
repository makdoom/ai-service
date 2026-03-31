import { Queue, Worker, QueueEvents, Job } from 'bullmq';
import { redisClient } from '@/utils/redis';

export const VIDEO_QUEUE_NAME = 'video-processing';

const queueOptions = {
  connection: redisClient,
};

// Queue Producer
class QueueService {
  private videoQueue: Queue;

  constructor() {
    this.videoQueue = new Queue(VIDEO_QUEUE_NAME, queueOptions);
    console.log(`BullMQ Queue "${VIDEO_QUEUE_NAME}" initialized`);
  }

  public async addVideoToQueue(videoId: string, videoUrl: string) {
    try {
      const job = await this.videoQueue.add(
        'process-video',
        { videoId, videoUrl },
        {
          attempts: 3,
          backoff: {
            type: 'exponential',
            delay: 1000,
          },
        }
      );
      console.log(`Job added to queue: ${job.id} for videoId: ${videoId}`);
      return job;
    } catch (error) {
      console.error('Error adding job to queue:', error);
      throw error;
    }
  }

  public getQueue() {
    return this.videoQueue;
  }
}

export const queueService = new QueueService();
