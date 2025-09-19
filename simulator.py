import argparse
import asyncio
import random
import time
import uuid

import httpx

METRICS = {
    "temperature": lambda: round(random.uniform(60, 100), 2),
    "voltage": lambda: round(random.uniform(3.0, 4.2), 2),
    "humidity": lambda: round(random.uniform(20, 80), 2),
    "status": lambda: random.choice([0, 1]),  # 0=offline, 1=online
}


async def send_event(client: httpx.AsyncClient, base_url: str, device_id: str):
    metric = random.choice(list(METRICS.keys()))
    value = METRICS[metric]()
    event = {
        "device_id": device_id,
        "metric": metric,
        "value": value,
        "timestamp": time.time(),
    }

    try:
        resp = await client.post(f"{base_url}/ingest", json=event)
        if resp.status_code != 200:
            print(f"[{device_id}] Error {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[{device_id}] Request failed: {e}")


async def run_simulation(base_url: str, num_sensors: int, rate: float):
    """Run simulation with num_sensors, sending `rate` messages per second each."""
    devices = [f"sensor-{i:03d}" for i in range(num_sensors)]
    interval = 1.0 / rate

    async with httpx.AsyncClient(timeout=5.0) as client:
        while True:
            start = time.time()
            tasks = [send_event(client, base_url, d) for d in devices]
            await asyncio.gather(*tasks)

            elapsed = time.time() - start
            sleep_time = max(0, interval - elapsed)
            await asyncio.sleep(sleep_time)


def main():
    parser = argparse.ArgumentParser(description="IoT Data Simulator")
    parser.add_argument(
        "--sensors", type=int, default=5, help="Number of sensors to simulate"
    )
    parser.add_argument(
        "--rate", type=float, default=1.0, help="Events per second per sensor"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8000",
        help="Ingestion API base URL",
    )
    args = parser.parse_args()

    try:
        asyncio.run(run_simulation(args.url, args.sensors, args.rate))
    except KeyboardInterrupt:
        print("Simulation stopped.")


if __name__ == "__main__":
    main()
