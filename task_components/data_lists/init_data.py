import redis
from redis.commands.json.path import Path
import psycopg2
import numpy as np

list_count = 10
step = 10

redis_info = {
    "host": "node-worker-redis-service.default.svc.cluster.local",
    "port": 6379,
    "db": 0
}

postgres = {
    "host": "postgres.default.svc.cluster.local",
    "port": 5432,
    "db": "master_db",
    "user": "master_agent",
    "password": "master_password"
}

################################################################################

def create_random_list(num, start = 1, end = 100):
    arr = np.random.choice(np.arange(start, end + 1), size=num, replace=False)
    return arr

if __name__ == "__main__":
    # Connect to PostgreSQL database
    conn = psycopg2.connect(
        host =     postgres["host"],
        port =     postgres["port"],
        database = postgres["db"],
        user =     postgres["user"],
        password = postgres["password"]
    )

    r = redis.Redis(host=redis_info["host"], port=redis_info["port"], db=redis_info["db"])

    for i in range(1, list_count + 1):
        try:
            list = create_random_list(i * step, 1, i * step)
            count_n = len(list)

            cur = conn.cursor()
            cur.execute(f"INSERT INTO data (name, count_n) VALUES ('data-{count_n}', {count_n}) RETURNING id")
            data_id = cur.fetchone()[0]

            r.json().set(f"data:{data_id}", Path.root_path(), {"list": list.tolist()})

            conn.commit()
        
        except Exception as e:
            conn.rollback()
            print(e)

