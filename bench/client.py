
import time
import statistics
from llm_prompt_shield.integrations.langchain import PromptGuardCallbackHandler

def prompt_shield_latency_test(prompt, runs=50):
    shield_callback = PromptGuardCallbackHandler(block_on_detection=True)
    latencies = []
    for _ in range(runs):
        start = time.perf_counter()
        shield_callback.on_llm_start({}, [prompt])
        end = time.perf_counter()
        latencies.append(end - start)
    median_latency = statistics.median(latencies)
    print(f"Median latency (Prompt Shield only): {median_latency:.6f} seconds")

if __name__ == "__main__":
    small_payload = "a" * 50
    large_payload = "b" * 500

    print("Benchmarking Prompt Shield callback (small payload)...")
    prompt_shield_latency_test(small_payload)
    print("Benchmarking Prompt Shield callback (large payload)...")
    prompt_shield_latency_test(large_payload)
