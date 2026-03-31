import { Server as SocketServer } from 'socket.io';
import { createAdapter } from '@socket.io/redis-adapter';
import { pubClient, subClient } from '@/utils/redis';
import { Server as HttpServer } from 'http';

class SocketService {
  private io: SocketServer | null = null;

  public init(httpServer: HttpServer) {
    this.io = new SocketServer(httpServer, {
      cors: {
        origin: '*', // Define allowed origins here
        methods: ['GET', 'POST'],
      },
    });

    // Use Redis adapter for horizontal scaling
    this.io.adapter(createAdapter(pubClient, subClient));

    this.setupListeners();
    console.log('Socket.io service initialized with Redis adapter');
  }

  private setupListeners() {
    if (!this.io) return;

    this.io.on('connection', (socket) => {
      console.log(`Client connected: ${socket.id}`);

      socket.on('disconnect', () => {
        console.log(`Client disconnected: ${socket.id}`);
      });

      // Join a video-specific room for real-time updates
      socket.on('join-video', (videoId: string) => {
        socket.join(`video:${videoId}`);
        console.log(`Socket ${socket.id} joined room video:${videoId}`);
      });
    });
  }

  public getIO(): SocketServer {
    if (!this.io) {
      throw new Error('Socket.io not initialized. Please call init() first.');
    }
    return this.io;
  }

  // Helper function to emit events to specific rooms
  public emitToRoom(room: string, event: string, data: any) {
    if (this.io) {
      this.io.to(room).emit(event, data);
    }
  }
}

export const socketService = new SocketService();
