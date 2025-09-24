CREATE TABLE IF NOT EXISTS device_readings (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    metric VARCHAR(20) NOT NULL,
    value DECIMAL(10,2) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    ingestion_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    message_id UUID NOT NULL,
    location VARCHAR(100),
    anomaly_detected BOOLEAN DEFAULT FALSE,
    rolling_avg DECIMAL(10,2),
    deviation_pct DECIMAL(10,6),
    processed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_device_readings_device_id ON device_readings(device_id);
CREATE INDEX idx_device_readings_timestamp ON device_readings(timestamp);
CREATE INDEX idx_device_readings_processed_at ON device_readings(processed_at);
CREATE INDEX idx_device_readings_anomaly ON device_readings(anomaly_detected);