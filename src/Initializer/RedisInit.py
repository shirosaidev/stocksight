import redis
from config import redis_host, redis_port

rds = redis.Redis(host=str(redis_host), port=redis_port, db=0)