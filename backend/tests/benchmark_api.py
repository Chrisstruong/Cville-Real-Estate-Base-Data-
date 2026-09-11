import time
import statistics
import requests

URL = "http://127.0.0.1:8000/api/properties?limit=10"
NUM_REQUESTS = 100

response_times = []
successful_requests = 0

for i in range(NUM_REQUESTS):
    start = time.perf_counter()

    try:
        response = requests.get(URL, timeout=10)

        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000

        response_times.append(elapsed_ms)

        if response.status_code == 200:
            successful_requests += 1

        print(
            f"Request {i + 1}: "
            f"{response.status_code} - "
            f"{elapsed_ms:.2f} ms"
        )

    except requests.RequestException as e:
        print(f"Request {i + 1}: FAILED - {e}")

if response_times:
    sorted_times = sorted(response_times)

    average = statistics.mean(response_times)
    median = statistics.median(response_times)
    maximum = max(response_times)

    p95_index = int(0.95 * len(sorted_times)) - 1
    p95 = sorted_times[p95_index]

    success_rate = (
        successful_requests / NUM_REQUESTS
    ) * 100

    print("\n--- API Benchmark Results ---")
    print(f"Total requests: {NUM_REQUESTS}")
    print(f"Successful requests: {successful_requests}")
    print(f"Success rate: {success_rate:.2f}%")
    print(f"Average latency: {average:.2f} ms")
    print(f"Median latency: {median:.2f} ms")
    print(f"P95 latency: {p95:.2f} ms")
    print(f"Maximum latency: {maximum:.2f} ms")