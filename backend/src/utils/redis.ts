import Redis from 'ioredis';
import dotenv from 'dotenv';

dotenv.config();

const redisConfig = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD,
};

export const createRedisClient = () => {
  const client = new Redis(redisConfig);

  client.on('error', (err) => {
    console.error('Redis Client Error:', err);
  });

  client.on('connect', () => {
    console.log('Redis connected successfully');
  });

  return client;
};

// Singleton clients for Pub/Sub and general usage
export const redisClient = createRedisClient();
export const pubClient = createRedisClient();
export const subClient = createRedisClient();
