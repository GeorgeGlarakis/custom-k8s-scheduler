import redis
import os

# Initialize environmental variables
data_host = os.environ.get('DATA_HOST')
namespace = os.environ.get('NAMESPACE')

def connect_to_redis():
    try:
        # Connect to Redis instance
        r = redis.StrictRedis(host=f'{data_host}.{namespace}.svc.cluster.local', port=6379)

        r.incr('mykey', 1)
        value = r.get('mykey')
        print(f'Retrieved value from Redis: {value.decode("utf-8")}')

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    connect_to_redis()