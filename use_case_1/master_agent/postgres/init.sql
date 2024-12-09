CREATE USER master_agent WITH PASSWORD 'master_password';
CREATE DATABASE master_db;
GRANT ALL PRIVILEGES ON DATABASE master_db TO master_agent;

CREATE TABLE node (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cpu_speed INTEGER, -- MHz 10^6 Hz
    memory INTEGER,
    disk_size INTEGER
);

CREATE TABLE code (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    image VARCHAR(255),
    tag VARCHAR(255),
    complexity VARCHAR(255), -- O(n) | O(n^2) | O(nlogn)
    size_mb NUMERIC(10,1) DEFAULT 0
);

CREATE TABLE data (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    count_n INTEGER, -- len(list)
    size_mb NUMERIC(10,1) DEFAULT 0
);

CREATE TABLE task (
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

CREATE TABLE compatible (
    code_id INTEGER NOT NULL,
    data_id INTEGER NOT NULL,
    PRIMARY KEY (code_id, data_id)
);

CREATE TYPE pod_type AS ENUM ('code', 'data');

CREATE TABLE node_info (
    id SERIAL PRIMARY KEY,
    time_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    time_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    node_id INTEGER NOT NULL,
    pod_id INTEGER NOT NULL,
    pod_type  pod_type NOT NULL
);

CREATE TABLE node_latency (
    id SERIAL PRIMARY KEY,
    node_from INTEGER NOT NULL,
    node_to INTEGER NOT NULL,
    latency_ms INTEGER NOT NULL DEFAULT 0
);