# Analytics API Documentation

Base URL: `http://localhost:8003`

## Overview

The Analytics API provides RESTful access to IoT device data, including historical readings, real-time snapshots, device statistics, and anomaly detection results.

## Implementation Status
- [x] `/system/health` - Health check
- [x] `/system/stats` - System statistics
- [x] `/devices` - List all devices
- [ ] `/devices/{id}` - Get device details
- [ ] `/devices/{id}/readings` - Get device readings
- [ ] `/devices/{id}/anomalies` - Get device anomalies
- [ ] `/readings` - Get recent readings
- [ ] `/readings/latest` - Get latest readings
- [ ] `/anomalies` - Get recent anomalies

---

## Device Resources

### List All Devices
```
GET /devices
```

Returns aggregate statistics for all devices in the system.

**Query Parameters:**
- `active` (boolean, optional) - Filter for devices active in last 5 minutes
- `limit` (integer, optional) - Maximum number of devices to return (default: 50)

**Response:**
```json
{
  "devices": [
    {
      "device_id": "device_001",
      "message_count": 1543,
      "avg_value": 24.5,
      "last_seen": "2025-09-25T14:30:00Z",
      "anomaly_count": 12
    }
  ]
}
```

---

### Get Device Details
```
GET /devices/{id}
```

Returns detailed statistics for a specific device.

**Path Parameters:**
- `id` (string, required) - Device identifier

**Response:**
```json
{
  "device_id": "device_001",
  "message_count": 1543,
  "avg_value": 24.5,
  "last_seen": "2025-09-25T14:30:00Z",
  "anomaly_count": 12
}
```

---

### Get Device Readings
```
GET /devices/{id}/readings
```

Returns historical readings for a specific device.

**Path Parameters:**
- `id` (string, required) - Device identifier

**Query Parameters:**
- `metric` (string, optional) - Filter by metric type (temperature, humidity, voltage, status)
- `start` (timestamp, optional) - Start time for time range query
- `end` (timestamp, optional) - End time for time range query
- `limit` (integer, optional) - Maximum number of readings (default: 100)

**Response:**
```json
{
  "readings": [
    {
      "id": 12345,
      "device_id": "device_001",
      "metric": "temperature",
      "value": 25.3,
      "timestamp": "2025-09-25T14:30:00Z",
      "location": "warehouse-a",
      "anomaly_detected": false,
      "rolling_avg": 24.8,
      "deviation_pct": 0.02,
      "processed_at": "2025-09-25T14:30:01Z"
    }
  ]
}
```

---

### Get Device Anomalies
```
GET /devices/{id}/anomalies
```

Returns anomaly events for a specific device.

**Path Parameters:**
- `id` (string, required) - Device identifier

**Response:**
```json
{
  "anomalies": [
    {
      "id": 456,
      "device_id": "device_001",
      "metric": "temperature",
      "value": 45.2,
      "timestamp": "2025-09-25T14:15:00Z",
      "location": "warehouse-a",
      "anomaly_detected": true,
      "rolling_avg": 24.8,
      "deviation_pct": 0.82,
      "processed_at": "2025-09-25T14:15:01Z"
    }
  ]
}
```

---

## Reading Resources

### Get Recent Readings
```
GET /readings
```

Returns recent readings across all devices (activity feed).

**Query Parameters:**
- `device_id` (string, optional) - Filter by specific device
- `metric` (string, optional) - Filter by metric type
- `limit` (integer, optional) - Maximum number of readings (default: 50)

**Response:**
```json
{
  "readings": [
    {
      "id": 12345,
      "device_id": "device_001",
      "metric": "temperature",
      "value": 25.3,
      "timestamp": "2025-09-25T14:30:00Z",
      "location": "warehouse-a",
      "anomaly_detected": false,
      "rolling_avg": 24.8,
      "deviation_pct": 0.02,
      "processed_at": "2025-09-25T14:30:01Z"
    }
  ]
}
```

---

### Get Latest Readings
```
GET /readings/latest
```

Returns the most recent reading for each device (real-time system snapshot).

**Response:**
```json
{
  "readings": [
    {
      "device_id": "device_001",
      "metric": "temperature",
      "value": 25.3,
      "timestamp": "2025-09-25T14:30:00Z",
      "location": "warehouse-a"
    },
    {
      "device_id": "device_002",
      "metric": "humidity",
      "value": 65.8,
      "timestamp": "2025-09-25T14:29:58Z",
      "location": "warehouse-b"
    }
  ]
}
```

---

## Anomaly Resources

### Get Recent Anomalies
```
GET /anomalies
```

Returns recent anomaly events across all devices.

**Query Parameters:**
- `device_id` (string, optional) - Filter by specific device
- `severity` (string, optional) - Filter by severity (high, medium, low)
- `limit` (integer, optional) - Maximum number of anomalies (default: 50)

**Response:**
```json
{
  "anomalies": [
    {
      "id": 456,
      "device_id": "device_001",
      "metric": "temperature",
      "value": 45.2,
      "timestamp": "2025-09-25T14:15:00Z",
      "location": "warehouse-a",
      "anomaly_detected": true,
      "rolling_avg": 24.8,
      "deviation_pct": 0.82,
      "processed_at": "2025-09-25T14:15:01Z"
    }
  ]
}
```

---

## System Resources

### Health Check
```
GET /system/health
```

Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "analytics-api"
}
```

---

### System Statistics
```
GET /system/stats
```

Returns system-wide statistics and metrics.

**Response:**
```json
{
  "total_readings": 156234,
  "unique_devices": 50,
  "total_anomalies": 342,
  "latest_reading": "2025-09-25T14:30:00Z"
}
```

---

## Error Responses

All endpoints return standard HTTP status codes and error messages in JSON format:

```json
{
  "error": "Device not found",
  "status": 404
}
```

**Common Status Codes:**
- `200 OK` - Request successful
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Responses may be cached for performance optimization
- Query parameter validation is enforced on all endpoints