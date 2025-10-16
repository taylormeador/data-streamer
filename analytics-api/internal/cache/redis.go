package cache

import (
	"context"
	"encoding/json"
	"time"

	"github.com/redis/go-redis/v9"
	"github.com/taylormeador/data-streamer/analytics-api/internal/data"
	"github.com/taylormeador/data-streamer/analytics-api/internal/metrics"
)

type Cache struct {
	client *redis.Client
}

func NewCache(redisURL string) (*Cache, error) {
	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, err
	}

	client := redis.NewClient(opt)

	// Test connection
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		return nil, err
	}

	return &Cache{client: client}, nil
}

func (c *Cache) Close() error {
	return c.client.Close()
}

// GetReadings caches device readings with read-through pattern
func (c *Cache) GetReadings(ctx context.Context, key string, ttl time.Duration, fetchFn func() ([]*data.DeviceReading, error)) ([]*data.DeviceReading, error) {
	// Try cache first
	cached, err := c.client.Get(ctx, key).Result()
	if err == nil {
		var readings []*data.DeviceReading
		if err := json.Unmarshal([]byte(cached), &readings); err == nil {
			metrics.CacheHits.Inc()
			return readings, nil
		}
	}

	// Cache miss - fetch from DB
	metrics.CacheMisses.Inc()
	readings, err := fetchFn()
	if err != nil {
		return nil, err
	}

	// Store in cache for next time
	jsonData, err := json.Marshal(readings)
	if err == nil {
		c.client.Set(ctx, key, jsonData, ttl)
	}

	return readings, nil
}

// GetDevices caches device statistics with read-through pattern
func (c *Cache) GetDevices(ctx context.Context, key string, ttl time.Duration, fetchFn func() ([]*data.Device, error)) ([]*data.Device, error) {
	// Try cache first
	cached, err := c.client.Get(ctx, key).Result()
	if err == nil {
		var devices []*data.Device
		if err := json.Unmarshal([]byte(cached), &devices); err == nil {
			return devices, nil
		}
	}

	// Cache miss - fetch from DB
	devices, err := fetchFn()
	if err != nil {
		return nil, err
	}

	// Store in cache for next time
	jsonData, err := json.Marshal(devices)
	if err == nil {
		c.client.Set(ctx, key, jsonData, ttl)
	}

	return devices, nil
}

// Invalidate removes a key from cache
func (c *Cache) Invalidate(ctx context.Context, key string) error {
	return c.client.Del(ctx, key).Err()
}
