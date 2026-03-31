import http from 'http';
import app from '@/app';
import { socketService } from '@/services/socket.service';
import dotenv from 'dotenv';

dotenv.config();

const port = process.env.PORT || 5000;
const server = http.createServer(app);

// Initialize Socket.io with the HTTP server
socketService.init(server);

server.listen(port, () => {
  console.log(`[server]: Server is running at http://localhost:${port}`);
  console.log(`[server]: Socket.io service initialized`);
  console.log(`[server]: BullMQ service initialized`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    process.exit(0);
  });
});
