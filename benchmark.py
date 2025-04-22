import time  
import statistics  
import requests  
import csv  
import pandas as pd  
import seaborn as sns  
import matplotlib.pyplot as plt

# ✅ Set your function ID here
FUNCTION_ID = 2

RUNTIMES = ["runc", "runsc"]
BENCHMARK_ENDPOINT = f"http://localhost:8000/functions/{FUNCTION_ID}/execute"
NUM_RUNS = 10
CSV_FILE = "benchmark_results.csv"

def benchmark_runtime(runtime):
    timings = []
    print(f"\n⚙️  Benchmarking runtime: {runtime}")

    for i in range(NUM_RUNS):
        try:
            payload = {"runtime": runtime}
            start = time.time()
            response = requests.post(BENCHMARK_ENDPOINT, json=payload)
            end = time.time()
            elapsed = end - start
            if response.status_code == 200:
                timings.append(elapsed)
                print(f"✅ Run {i+1}: {elapsed:.3f}s")
            else:
                print(f"❌ Run {i+1} failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Run {i+1} error: {e}")
    return timings

def log_to_csv(runtime, timings):
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        for t in timings:
            writer.writerow([runtime, t])

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

def visualize_results(csv_path):
    df = pd.read_csv(csv_path, names=["Runtime", "Time"])
    sns.set(style="whitegrid")
    plt.figure(figsize=(8, 6))
    sns.barplot(data=df, x="Runtime", y="Time", ci="sd", palette="Set2")
    plt.title("Benchmark: Mean Execution Time by Runtime")
    plt.ylabel("Execution Time (s)")
    plt.xlabel("Runtime Backend")
    plt.tight_layout()
    plt.savefig("benchmark_chart.png")
    plt.show()

def main():
    # Clear CSV before starting fresh benchmark
    open(CSV_FILE, "w").close()

    for runtime in RUNTIMES:
        timings = benchmark_runtime(runtime)
        summarize_results(runtime, timings)
        log_to_csv(runtime, timings)

    visualize_results(CSV_FILE)

if __name__ == "__main__":
    main()
