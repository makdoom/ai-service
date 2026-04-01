import { Request, Response } from "express";

class QueryController {
  public queryVideo = async (req: Request, res: Response) => {
    try {
      const { videoId, query } = req.body || {};

      if (!videoId || !query) {
        return res.status(400).json({
          error: "Bad Request",
          message: "videoId and query are required in the request body",
        });
      }

      const aiServiceUrl =
        process.env.AI_SERVICE_URL || "http://localhost:8000";

      console.log(`Querying video: ${videoId}`);

      const response = await fetch(`${aiServiceUrl}/api/v1/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Auth-Token": process.env.AUTH_TOKEN,
        },
        body: JSON.stringify({
          video_id: videoId,
          query: query.trim(),
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

      // // Emit status to socket clients
      // socketService.emitToUser(`video:${videoId}`, "status", {
      //   status: "queued",
      //   jobId: job.id,
      //   videoId,
      // });

      return res.status(202).json({ succcess: 200, result });
    } catch (error: any) {
      console.error("Error uploading video:", error);
      return res.status(500).json({
        error: "Internal Server Error",
        message: error.message,
      });
    }
  };
}

export const queryController = new QueryController();
