CREATE USER IF NOT EXISTS master_agent WITH PASSWORD 'master_password';
CREATE DATABASE IF NOT EXISTS master_db;
GRANT ALL PRIVILEGES ON DATABASE master_db TO master_agent;

GRANT USAGE ON SCHEMA public TO master_agent;
GRANT pg_write_all_data TO master_agent;

--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS node (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cpu_speed INTEGER, -- MHz 10^6 Hz
    memory INTEGER,
    disk_size INTEGER
);

CREATE TABLE IF NOT EXISTS code (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    image VARCHAR(255),
    tag VARCHAR(255),
    complexity VARCHAR(255), -- O(n) | O(n^2) | O(n*log(n))
    size_mb NUMERIC(10,1) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    count_n INTEGER, -- len(list)
    size_mb NUMERIC(10,1) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS task (
    id SERIAL PRIMARY KEY,
    code_id INTEGER NOT NULL,
    data_id INTEGER NOT NULL,
    time_listed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_scheduled TIMESTAMP,
    time_started TIMESTAMP,
    time_completed TIMESTAMP,
    node_id INTEGER,
    execution_prediction_ms NUMERIC(10,2),
    completion_prediction_ms NUMERIC(10,2)
);

CREATE TABLE IF NOT EXISTS compatible (
    code_id INTEGER NOT NULL,
    data_id INTEGER NOT NULL,
    PRIMARY KEY (code_id, data_id)
);

CREATE TYPE IF NOT EXISTS pod_type AS ENUM ('code', 'data');

CREATE TABLE IF NOT EXISTS node_info (
    id SERIAL PRIMARY KEY,
    time_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    node_id INTEGER NOT NULL,
    pod_id INTEGER NOT NULL,
    pod_type  pod_type NOT NULL
);

CREATE TABLE IF NOT EXISTS node_latency (
    id SERIAL PRIMARY KEY,
    node_from INTEGER NOT NULL,
    node_to INTEGER NOT NULL,
    latency_ms INTEGER NOT NULL DEFAULT 0
);

INSERT INTO code (name, image, tag, complexity, size_mb) VALUES
('merge-sort', 'code-job-merge-sort', 'latest', 'O(n*log(n))', 53),
('selection-sort', 'code-job-selection-sort', 'latest', 'O(n^2)', 53),
('insertion-sort', 'code-job-insertion-sort', 'latest', 'O(n^2)', 53),
('bubble-sort', 'code-job-bubble-sort', 'latest', 'O(n^2)', 53)