import time 
import requests 
import statistics

FUNC_ID = 2  # Replace with your actual function ID
URL_TEMPLATE = "http://localhost:8000/functions/{}/execute"
ROUNDS = 10
RUNTIMES = ["docker", "gvisor"]  # Make sure this matches your implementation

def benchmark_runtime(runtime): 
    timings = [] 
    print(f"\n🔧 Benchmarking runtime: {runtime}")
    
    # Optional: update the function's virtualization_backend before executing
    update_url = f"http://localhost:8000/functions/{FUNC_ID}"
    requests.put(update_url, json={
        "name": "benchmark_func",
        "route": "/benchmark",
        "language": "python",
        "code": "print('Hello from benchmark')",
        "timeout": 3,
        "virtualization_backend": runtime
    })

    for i in range(ROUNDS):
        try:
            start = time.time()
            response = requests.post(URL_TEMPLATE.format(FUNC_ID))
            end = time.time()
            elapsed = round(end - start, 3)

            if response.status_code == 200:
                print(f"✅ Run {i+1}: {elapsed}s")
                timings.append(elapsed)
            else:
                print(f"❌ Run {i+1}: Error {response.status_code} - {response.text}")
                timings.append(None)

        except Exception as e:
            print(f"❌ Run {i+1}: Exception - {str(e)}")
            timings.append(None)

    return [t for t in timings if t is not None]

def summarize_results(runtime, timings): 
    if not timings: 
        print(f"\n❌ No successful runs for {runtime}") 
        return 
    
    print(f"\n📊 Summary for {runtime}")
    print(f"  Runs:        {len(timings)}")
    print(f"  Min time:    {min(timings):.3f}s")
    print(f"  Max time:    {max(timings):.3f}s")
    print(f"  Mean time:   {statistics.mean(timings):.3f}s")
    print(f"  Median time: {statistics.median(timings):.3f}s")

def main():
    for runtime in RUNTIMES:
        timings = benchmark_runtime(runtime)
        summarize_results(runtime, timings)

if __name__ == "__main__":
    main()
