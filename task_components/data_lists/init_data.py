import os
import redis
from redis.commands.json.path import Path
import psycopg2
import numpy as np

list_count = os.environ.get('LIST_COUNT', 10)
list_count = int(list_count)
step = os.environ.get('LIST_STEP', 10)
step = int(step)

function = os.environ.get('FUNCTION', 'scale')

node_name = os.environ.get('NODE_NAME', 'node')

redis_info = {
    "host": f"{node_name}-worker-redis-service.default.svc.cluster.local",
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

def create_random_list(num, start = 1, end = 10000):
    arr = np.random.choice(np.arange(start, end + 1), size=num, replace=False)
    return arr

def scale(r, conn, list_count, step):
    for i in range(1, list_count + 1):
        try:
            list = create_random_list(i * step, 1, i * step)
            count_n = len(list)

            cur = conn.cursor()
            cur.execute(f"INSERT INTO data (name, count_n) VALUES ('data-{count_n}', {count_n}) RETURNING id")
            data_id = cur.fetchone()[0]

            cur.execute(f"""INSERT INTO node_info (node_id, pod_id, pod_type) 
                            SELECT id, '{data_id}', 'data' FROM node WHERE name = '{node_name}';
                        """)

            r.json().set(f"data:{data_id}", Path.root_path(), {"list": list.tolist()})
            size_mb = r.memory_usage(f"data:{data_id}") / 1024

            cur.execute(f"UPDATE data SET size_mb = {size_mb} WHERE id = {data_id};")

            conn.commit()
        
        except Exception as e:
            conn.rollback()
            print(e)

def same(r, conn, list_count, step):
    for i in range(1, list_count + 1):
        try:
            list = create_random_list(step, 1, step)
            count_n = len(list)

            cur = conn.cursor()
            cur.execute(f"INSERT INTO data (name, count_n) VALUES ('data-{count_n}', {count_n}) RETURNING id")
            data_id = cur.fetchone()[0]

            cur.execute(f"""INSERT INTO node_info (node_id, pod_id, pod_type) 
                            SELECT id, '{data_id}', 'data' FROM node WHERE name = '{node_name}';
                        """)

            r.json().set(f"data:{data_id}", Path.root_path(), {"list": list.tolist()})
            size_mb = r.memory_usage(f"data:{data_id}") / 1024

            cur.execute(f"UPDATE data SET size_mb = {size_mb} WHERE id = {data_id};")

            conn.commit()
            return True
        
        except Exception as e:
            conn.rollback()
            print(e)
            return False
        
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

    if function == "scale":
        scale(r, conn, list_count, step)
    elif function == "same":
        same(r, conn, list_count, step)
    else:
        print(f"Unknown function: {function}")
        exit(1)

    conn.close()

