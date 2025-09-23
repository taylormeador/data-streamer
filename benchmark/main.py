from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field
import aiohttp
import asyncio
import time
import random
import statistics
import logging
from typing import List, Dict, Any, Optional
from asyncio_throttle import Throttler
import json

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Benchmark Service", version="0.1.0")


class BenchmarkConfig(BaseModel):
    target_rps: int = Field(default=100, description="Target requests per second")
    duration_seconds: int = Field(default=60, description="Test duration in seconds")
    warmup_seconds: int = Field(
        default=10, description="Warmup period before measurement"
    )
    producer_url: str = Field(default="http://producer:8000")
    consumer_url: str = Field(default="http://consumer:8001")
    device_count: int = Field(
        default=50, description="Number of unique devices to simulate"
    )


class BenchmarkResults(BaseModel):
    config: BenchmarkConfig
    total_requests: int
    successful_requests: int
    failed_requests: int
    actual_rps: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    latency_avg: float
    error_rate: float
    duration_seconds: float
    timestamp: float


# Global state for running benchmarks
current_benchmark: Optional[Dict[str, Any]] = None
benchmark_results: List[BenchmarkResults] = []


def generate_telemetry_data(device_count: int) -> Dict[str, Any]:
    """Generate realistic IoT telemetry data"""
    device_id = f"device_{random.randint(1, device_count):03d}"

    # Different sensor types have different realistic ranges
    metric_ranges = {
        "temperature": (15.0, 35.0),
        "humidity": (30.0, 90.0),
        "voltage": (3.0, 5.0),
        "status": (0.0, 1.0),
    }

    metric = random.choice(list(metric_ranges.keys()))
    min_val, max_val = metric_ranges[metric]
    value = random.uniform(min_val, max_val)

    # Add some devices with anomalous readings occasionally
    if random.random() < 0.05:  # 5% chance of anomaly
        if metric == "temperature":
            value = random.choice([random.uniform(-10, 10), random.uniform(45, 60)])
        elif metric == "humidity":
            value = random.uniform(95, 100)

    return {
        "device_id": device_id,
        "metric": metric,
        "value": round(value, 2),
        "location": random.choice(
            ["warehouse-a", "warehouse-b", "warehouse-c", "field-1", "field-2"]
        ),
    }


async def send_single_request(
    session: aiohttp.ClientSession, url: str, data: Dict[str, Any]
) -> Dict[str, Any]:
    """Send a single request and measure latency"""
    start_time = time.perf_counter()

    try:
        async with session.post(f"{url}/ingest", json=data) as response:
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000

            return {
                "success": response.status == 200,
                "latency_ms": latency_ms,
                "status_code": response.status,
                "timestamp": start_time,
            }
    except Exception as e:
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        return {
            "success": False,
            "latency_ms": latency_ms,
            "status_code": 0,
            "error": str(e),
            "timestamp": start_time,
        }


async def run_load_test(config: BenchmarkConfig) -> BenchmarkResults:
    """Execute the benchmark test"""
    global current_benchmark

    logging.info(
        f"Starting benchmark: {config.target_rps} RPS for {config.duration_seconds}s"
    )

    # Initialize tracking
    current_benchmark = {
        "config": config,
        "status": "running",
        "start_time": time.time(),
        "requests_sent": 0,
        "results": [],
    }

    throttler = Throttler(rate_limit=config.target_rps, period=1.0)

    async with aiohttp.ClientSession() as session:
        # Warmup period
        if config.warmup_seconds > 0:
            logging.info(f"Warmup period: {config.warmup_seconds} seconds")
            warmup_end = time.time() + config.warmup_seconds

            while time.time() < warmup_end:
                async with throttler:
                    data = generate_telemetry_data(config.device_count)
                    await send_single_request(session, config.producer_url, data)

        # Actual benchmark
        logging.info("Starting measurement period")
        test_start = time.time()
        test_end = test_start + config.duration_seconds
        results = []

        while time.time() < test_end:
            async with throttler:
                data = generate_telemetry_data(config.device_count)
                result = await send_single_request(session, config.producer_url, data)
                results.append(result)
                current_benchmark["requests_sent"] = len(results)

        actual_duration = time.time() - test_start
        logging.info(
            f"Benchmark completed. Sent {len(results)} requests in {actual_duration:.2f}s"
        )

        # Calculate statistics
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]

        latencies = [r["latency_ms"] for r in successful_results]

        if latencies:
            latency_p50 = statistics.median(latencies)
            latency_p95 = (
                statistics.quantiles(latencies, n=20)[18]
                if len(latencies) > 20
                else max(latencies)
            )
            latency_p99 = (
                statistics.quantiles(latencies, n=100)[98]
                if len(latencies) > 100
                else max(latencies)
            )
            latency_avg = statistics.mean(latencies)
        else:
            latency_p50 = latency_p95 = latency_p99 = latency_avg = 0.0

        benchmark_result = BenchmarkResults(
            config=config,
            total_requests=len(results),
            successful_requests=len(successful_results),
            failed_requests=len(failed_results),
            actual_rps=len(results) / actual_duration,
            latency_p50=latency_p50,
            latency_p95=latency_p95,
            latency_p99=latency_p99,
            latency_avg=latency_avg,
            error_rate=len(failed_results) / len(results) if results else 0.0,
            duration_seconds=actual_duration,
            timestamp=test_start,
        )

        current_benchmark = None
        benchmark_results.append(benchmark_result)

        return benchmark_result


@app.post("/run-benchmark")
async def start_benchmark(config: BenchmarkConfig, background_tasks: BackgroundTasks):
    """Start a new benchmark test"""
    global current_benchmark

    if current_benchmark is not None:
        return {"error": "Benchmark already running", "status": "busy"}

    # Run benchmark in background
    background_tasks.add_task(run_load_test, config)

    return {
        "message": "Benchmark started",
        "config": config.model_dump(),
        "status": "started",
    }


@app.get("/benchmark-status")
async def get_benchmark_status():
    """Get current benchmark status"""
    if current_benchmark is None:
        return {"status": "idle", "message": "No benchmark running"}

    return {
        "status": "running",
        "config": current_benchmark["config"].model_dump(),
        "requests_sent": current_benchmark["requests_sent"],
        "elapsed_seconds": time.time() - current_benchmark["start_time"],
    }


@app.get("/benchmark-results")
async def get_benchmark_results(limit: int = 10):
    """Get recent benchmark results"""
    results = []
    for result in benchmark_results[-limit:]:
        if hasattr(result, "model_dump"):
            # It's a Pydantic model
            results.append(result.model_dump())
        else:
            # It's already a dict (from suite results)
            results.append(result)

    return {"results": results, "total_results": len(benchmark_results)}


@app.get("/system-check")
async def system_health_check(config: BenchmarkConfig):
    """Check if target systems are healthy before running benchmark"""
    results = {}

    async with aiohttp.ClientSession() as session:
        # Check producer
        try:
            async with session.get(f"{config.producer_url}/health") as response:
                results["producer"] = {
                    "status": "healthy" if response.status == 200 else "unhealthy",
                    "response_time_ms": 0,  # Could add timing here
                }
        except Exception as e:
            results["producer"] = {"status": "unreachable", "error": str(e)}

        # Check consumer
        try:
            async with session.get(f"{config.consumer_url}/health") as response:
                results["consumer"] = {
                    "status": "healthy" if response.status == 200 else "unhealthy",
                    "response_time_ms": 0,
                }
        except Exception as e:
            results["consumer"] = {"status": "unreachable", "error": str(e)}

    all_healthy = all(
        service.get("status") == "healthy" for service in results.values()
    )

    return {
        "overall_status": "healthy" if all_healthy else "unhealthy",
        "services": results,
    }


@app.delete("/benchmark-results")
async def clear_benchmark_results():
    """Clear all stored benchmark results"""
    global benchmark_results
    count = len(benchmark_results)
    benchmark_results.clear()
    return {"message": f"Cleared {count} benchmark results"}


@app.get("/health")
async def health_check():
    """Health check for the benchmark service"""
    return {"status": "healthy"}


# Standard benchmark profiles for consistent testing
@app.post("/baseline-suite")
async def run_baseline_suite(background_tasks: BackgroundTasks):
    """Run the complete baseline benchmark suite"""
    if current_benchmark is not None:
        return {"error": "Benchmark already running", "status": "busy"}

    suite_results = []

    # 1. Light Load Test - establish minimum viable performance
    light_config = BenchmarkConfig(
        target_rps=25, duration_seconds=60, warmup_seconds=10, device_count=10
    )

    # 2. Standard Load Test - target "production" load
    standard_config = BenchmarkConfig(
        target_rps=100, duration_seconds=120, warmup_seconds=15, device_count=25
    )

    # 3. High Load Test - find breaking point
    high_config = BenchmarkConfig(
        target_rps=250, duration_seconds=60, warmup_seconds=15, device_count=50
    )

    configs = [
        ("light_load", light_config),
        ("standard_load", standard_config),
        ("high_load", high_config),
    ]

    async def run_suite():
        suite_start = time.time()
        logging.info("Starting baseline benchmark suite")

        for test_name, config in configs:
            logging.info(f"Running {test_name} test...")
            result = await run_load_test(config)
            result_dict = result.model_dump()
            result_dict["test_name"] = test_name
            suite_results.append(result_dict)

            # Wait between tests to let system settle
            await asyncio.sleep(30)

        suite_duration = time.time() - suite_start
        logging.info(f"Baseline suite completed in {suite_duration:.1f} seconds")

        # Store suite results with special marker
        benchmark_results.append(
            {
                "suite_name": "baseline",
                "timestamp": suite_start,
                "duration_seconds": suite_duration,
                "tests": suite_results,
            }
        )

    background_tasks.add_task(run_suite)

    return {
        "message": "Baseline benchmark suite started",
        "tests": ["light_load", "standard_load", "high_load"],
        "estimated_duration_minutes": 8,
    }


@app.post("/quick-test")
async def quick_benchmark():
    """Run a quick 30-second test at 50 RPS"""
    config = BenchmarkConfig(
        target_rps=50, duration_seconds=30, warmup_seconds=5, device_count=10
    )

    result = await run_load_test(config)
    return result.model_dump()


@app.post("/throughput-ceiling")
async def find_throughput_ceiling(
    background_tasks: BackgroundTasks,
    start_rps: int = 50,
    step_rps: int = 50,
    max_error_rate: float = 0.05,
):
    """Find maximum throughput before system breaks"""
    if current_benchmark is not None:
        return {"error": "Benchmark already running", "status": "busy"}

    async def find_ceiling():
        current_rps = start_rps
        ceiling_results = []

        logging.info(f"Finding throughput ceiling starting at {start_rps} RPS")

        while current_rps <= 1000:  # Safety limit
            config = BenchmarkConfig(
                target_rps=current_rps,
                duration_seconds=45,
                warmup_seconds=10,
                device_count=25,
            )

            logging.info(f"Testing {current_rps} RPS...")
            result = await run_load_test(config)
            result_dict = result.model_dump()
            result_dict["test_rps"] = current_rps
            ceiling_results.append(result_dict)

            # Check if we hit the breaking point
            if result.error_rate > max_error_rate:
                logging.info(
                    f"Hit ceiling at {current_rps} RPS (error rate: {result.error_rate:.1%})"
                )
                break

            if result.actual_rps < current_rps * 0.8:  # Can't keep up
                logging.info(
                    f"Hit ceiling at {current_rps} RPS (actual: {result.actual_rps:.1f} RPS)"
                )
                break

            current_rps += step_rps
            await asyncio.sleep(15)  # Brief recovery

        # Store ceiling test results
        benchmark_results.append(
            {
                "test_name": "throughput_ceiling",
                "timestamp": time.time(),
                "ceiling_rps": current_rps - step_rps,
                "tests": ceiling_results,
            }
        )

        logging.info(f"Throughput ceiling test completed")

    background_tasks.add_task(find_ceiling)

    return {
        "message": "Throughput ceiling test started",
        "parameters": {
            "start_rps": start_rps,
            "step_rps": step_rps,
            "max_error_rate": max_error_rate,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
