-- Argos initial schema and seed data
-- Runs automatically on first postgres startup

CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(100) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,
    role        VARCHAR(50)  NOT NULL DEFAULT 'read-only',
    tenant_id   VARCHAR(100) NOT NULL DEFAULT 'default',
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS devices (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    tenant_id   VARCHAR(100) NOT NULL,
    status      VARCHAR(20)  DEFAULT 'offline',
    ip          VARCHAR(50),
    last_seen   TIMESTAMP
);

CREATE TABLE IF NOT EXISTS executions (
    id          SERIAL PRIMARY KEY,
    job_id      VARCHAR(50)  NOT NULL,
    device_id   INTEGER REFERENCES devices(id),
    tenant_id   VARCHAR(100) NOT NULL,
    task_type   VARCHAR(50)  NOT NULL,
    target      VARCHAR(255),
    status      VARCHAR(20)  DEFAULT 'pending',
    output      TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- Seed: admin user (password: admin)
-- bcrypt hash of "admin" with 12 rounds
INSERT INTO users (username, password, role, tenant_id)
VALUES (
    'admin',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'admin',
    'org-a'
) ON CONFLICT (username) DO NOTHING;

-- Seed: demo devices
INSERT INTO devices (name, tenant_id, status, ip)
VALUES
    ('Device A', 'org-a', 'online',  '192.168.1.100'),
    ('Device B', 'org-b', 'offline', '192.168.2.100'),
    ('Device C', 'org-c', 'online',  '10.0.0.50')
ON CONFLICT DO NOTHING;
