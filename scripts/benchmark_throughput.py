import asyncio
import time
import uuid
import httpx


async def run_benchmark(base_url="http://localhost:8000", total_requests=100, concurrency=10):
    """Measures API accept rate (uploads accepted/sec) and p95 latency under concurrent load."""
    print(f"\n=======================================================")
    print(f"  AuditFlow AI — High Throughput Ingestion Benchmark  ")
    print(f"=======================================================")
    print(f"Target: {base_url} | Requests: {total_requests} | Concurrency: {concurrency}")

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # 1. Register test tenant
        uid = uuid.uuid4().hex[:8]
        reg_res = await client.post(
            "/auth/register",
            json={
                "tenant_name": f"Benchmark Org {uid}",
                "email": f"bench_{uid}@test.com",
                "password": "BenchmarkPass123!",
            },
        )
        if reg_res.status_code != 201:
            print("Failed to register tenant for benchmark:", reg_res.text)
            return

        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Tenant registered & authenticated successfully.")

        latencies = []
        status_counts = {}
        sem = asyncio.Semaphore(concurrency)

        async def worker(index):
            inv_num = f"INV-BENCH-{uid}-{index}"
            csv_data = f"invoice_number,vendor_name,date,total_amount,vendor_gstin\n{inv_num},Benchmark Vendor,2026-11-07,15000.00,27AAACT2727Q1ZB\n"
            files = {"file": (f"{inv_num}.csv", csv_data.encode("utf-8"), "text/csv")}
            data = {"document_type": "invoice"}
            req_headers = dict(headers)
            req_headers["Idempotency-Key"] = f"idemp_bench_{index}_{uid}"

            async with sem:
                t0 = time.perf_counter()
                try:
                    res = await client.post("/documents", files=files, data=data, headers=req_headers)
                    duration_ms = (time.perf_counter() - t0) * 1000
                    latencies.append(duration_ms)
                    code = res.status_code
                    status_counts[code] = status_counts.get(code, 0) + 1
                except Exception as exc:
                    status_counts["error"] = status_counts.get("error", 0) + 1

        overall_start = time.perf_counter()
        tasks = [worker(i) for i in range(total_requests)]
        await asyncio.gather(*tasks)
        total_time_sec = time.perf_counter() - overall_start

        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
        p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
        rps = round(total_requests / total_time_sec, 2)

        print("\n--- Benchmark Results ---")
        print(f"Total Time:         {total_time_sec:.2f}s")
        print(f"API Accept Rate:    {rps} uploads/second")
        print(f"P50 Latency:        {p50:.2f} ms")
        print(f"P95 Latency:        {p95:.2f} ms")
        print(f"P99 Latency:        {p99:.2f} ms")
        print(f"HTTP Status Codes:  {status_counts}")
        print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
