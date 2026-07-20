#!/usr/bin/env python3
"""Benchmarking suite for the load balancer.

Run against a live load balancer at LB_URL (except a4, which is a pure
offline simulation). Usage: `python analyze.py [a1|a2|a3|a4|all]`.

  a1 - request distribution across N=3 servers, 10k requests
  a2 - average load per server as N scales from 2 to 6
  a3 - failure detection + self-healing recovery time
  a4 - offline comparison of two different hash function choices
"""
import asyncio
import sys
import time
import math
import random
import subprocess

import aiohttp
import matplotlib.pyplot as plt
import requests

LB_URL         = "http://localhost:5000"
TOTAL_REQUESTS = 10000

# shared helpers 

async def _fetch(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """Fetch JSON data from a URL using an async HTTP client session.

    Args:
        session (aiohttp.ClientSession): The active client session context.
        url (str): The target endpoint URL to GET request.

    Returns:
        Optional[str]: The message string returned by the replica, or None on error.
    """
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json(content_type=None)
            return data.get("message", "")
    except Exception:
        return None

async def _send_async(n: int, path: str = "home") -> List[Optional[str]]:
    """Send n concurrent GET requests asynchronously to the load balancer.

    Args:
        n (int): Number of total requests to dispatch.
        path (str): Endpoint path on the target server.

    Returns:
        List[Optional[str]]: A list containing all responses returned from servers.
    """
    connector = aiohttp.TCPConnector(limit=200)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [_fetch(session, f"{LB_URL}/{path}") for _ in range(n)]
        return await asyncio.gather(*tasks)

def count_by_server(results: List[Optional[str]]) -> Dict[str, int]:
    """Count and aggregate response messages by individual server name.

    Args:
        results (List[Optional[str]]): A list of messages returned by backend replicas.

    Returns:
        Dict[str, int]: A sorted dictionary mapping server names to request counts.
    """
    counts = {}
    for msg in results:
        if msg:
            counts[msg] = counts.get(msg, 0) + 1
    return dict(sorted(counts.items()))

def get_replicas() -> dict:
    """Fetch the current replica count/hostnames from the live load balancer."""
    return requests.get(f"{LB_URL}/rep").json()["message"]

def set_n_servers(target: int) -> None:
    """Scale the live load balancer to exactly `target` servers.

    Args:
        target (int): Target number of active servers.
    """
    info = get_replicas()
    diff = target - info["N"]
    if diff > 0:
        requests.post(f"{LB_URL}/add", json={"n": diff, "hostnames": []})
        time.sleep(3)   # let containers spin up
    elif diff < 0:
        requests.delete(f"{LB_URL}/rm", json={"n": -diff, "hostnames": []})
        time.sleep(1)

def _std(values: List[float]) -> float:
    """Calculate the standard deviation of a sequence of values."""
    if not values:
        return 0.0
    avg = sum(values) / len(values)
    return math.sqrt(sum((v - avg) ** 2 for v in values) / len(values))


#  A-1 

def task_a1() -> None:
    """Benchmark A-1: Test request distribution across N=3 servers with 10k requests.

    Sends 10,000 asynchronous HTTP requests to the load balancer, aggregates
    the distribution of requests handled by each server replica, and saves
    a bar chart visualizing the load distribution.
    """
    print("\n=== A-1: 10,000 async requests on N=3 ===")
    set_n_servers(3)
    replicas = get_replicas()["replicas"]
    print(f"Active servers: {replicas}")

    results = asyncio.run(_send_async(TOTAL_REQUESTS))
    counts  = count_by_server(results)
    success = sum(counts.values())
    print(f"Successful responses: {success}/{TOTAL_REQUESTS}")
    for srv, cnt in counts.items():
        print(f"  {srv}: {cnt} ({cnt / success * 100:.1f} %)")

    labels = list(counts.keys())
    values = list(counts.values())
    ideal  = success / len(labels) if labels else 0

    # Plot request distribution bar chart
    fig, ax = plt.subplots(figsize=(max(8, len(labels) * 1.2), 5))
    bars = ax.bar(range(len(labels)), values, color="steelblue", edgecolor="white")
    ax.axhline(ideal, color="tomato", linestyle="--", linewidth=1.4, label=f"Ideal ({ideal:.0f})")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_title(f"A-1: Request distribution — N=3, {TOTAL_REQUESTS:,} async requests")
    ax.set_xlabel("Server")
    ax.set_ylabel("Requests handled")
    ax.legend()
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 20,
                str(val), ha="center", va="bottom", fontsize=8)
    plt.tight_layout()
    plt.savefig("a1_distribution.png", dpi=150)
    print("Saved → a1_distribution.png")
    plt.show()


# A-2 

def task_a2() -> None:
    """Benchmark A-2: Test scalability by scaling N from 2 to 6 servers.

    Iterates through different active server counts (N = 2 to 6), sends 10,000 concurrent
    requests to the load balancer, records the average load and standard deviation per server,
    and plots an errorbar chart comparing the load metrics with the theoretical ideal limit.
    """
    print("\n=== A-2: Scalability — N from 2 to 6 ===")
    ns        = list(range(2, 7))
    avgs      = []
    stds      = []

    for n in ns:
        set_n_servers(n)
        print(f"N={n}: sending {TOTAL_REQUESTS:,} requests…")
        results = asyncio.run(_send_async(TOTAL_REQUESTS))
        counts  = count_by_server(results)
        vals    = list(counts.values())
        avg     = sum(vals) / len(vals) if vals else 0
        std     = _std(vals)
        avgs.append(avg)
        stds.append(std)
        print(f"  avg={avg:.0f}, std={std:.0f}, per-server={counts}")

    ideal = [TOTAL_REQUESTS / n for n in ns]

    # Plot scalability errorbar comparing measured avg requests with the ideal line
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.errorbar(ns, avgs, yerr=stds, marker='o', capsize=5,
                label="Measured avg ± std", color="steelblue")
    ax.plot(ns, ideal, 'r--', marker='s', label="Ideal (10k / N)", alpha=0.6)
    ax.set_title(f"A-2: Average load per server — {TOTAL_REQUESTS:,} total requests")
    ax.set_xlabel("Number of servers (N)")
    ax.set_ylabel("Avg requests per server")
    ax.set_xticks(ns)
    ax.legend()
    plt.tight_layout()
    plt.savefig("a2_scalability.png", dpi=150)
    print("Saved → a2_scalability.png")
    plt.show()


# A-3

def task_a3() -> None:
    """Benchmark A-3: Test failure detection and self-healing recovery time.

    Starts with N=3 servers, kills one container directly via the Docker CLI,
    and polls the load balancer replica list every second to verify that
    the background heartbeat monitor successfully detects the dead server
    and launches a replacement within the 20-second timeout period.
    """
    print("\n A-3: Failure and recovery ===")
    set_n_servers(3)
    before = get_replicas()
    print(f"Before failure : N={before['N']}, replicas={before['replicas']}")

    victim = before["replicas"][0]
    print(f"Killing container: {victim}")
    # Forcefully stop and remove the server container to simulate a sudden crash
    subprocess.run(["docker", "stop", victim], capture_output=True)
    subprocess.run(["docker", "rm",   victim], capture_output=True)
    print("Container killed — waiting for heartbeat recovery (max 20 s)…")

    # Poll status every 1 second to measure recovery elapsed time
    for elapsed in range(1, 21):
        time.sleep(1)
        after = get_replicas()
        if victim not in after["replicas"] and after["N"] >= before["N"]:
            print(f"  Recovered after {elapsed} s: N={after['N']}, replicas={after['replicas']}")
            return
    print(f"  State after 20 s: {get_replicas()}")


# A-4 offline simulation 
def _simulate(H, Phi, n_servers=3, n_requests=10000,
              num_slots=512, num_virtual=9):
    """Simulate request distribution without any Docker dependency."""
    ring = [None] * num_slots

    def probe(slot):
        for _ in range(num_slots):
            if ring[slot % num_slots] is None:
                return slot % num_slots
            slot += 1
        return None

    for sid in range(1, n_servers + 1):
        for j in range(num_virtual):
            s = probe(Phi(sid, j) % num_slots)
            if s is not None:
                ring[s] = sid

    counts = {i: 0 for i in range(1, n_servers + 1)}
    for _ in range(n_requests):
        rid  = random.randint(100000, 999999)
        slot = H(rid) % num_slots
        for k in range(num_slots):
            srv = ring[(slot + k) % num_slots]
            if srv is not None:
                counts[srv] += 1
                break

    return counts

def task_a4():
    print("\n A-4: Hash function comparison (offline simulation) \n")

    configs = [
        ("Original\nH(i)=i²+2i+17\nΦ=i²+j²+2j+25",
         lambda i: i**2 + 2*i + 17,
         lambda i, j: i**2 + j**2 + 2*j + 25),
        ("Modified\nH(i)=i²+3i+11\nΦ=i²+j²+3j+17",
         lambda i: i**2 + 3*i + 11,
         lambda i, j: i**2 + j**2 + 3*j + 17),
    ]

    # sub-figure 1: N=3 bar comparison 
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"A-4: Distribution comparison : N=3, {TOTAL_REQUESTS:,} requests (simulated)")

    for ax, (title, H, Phi) in zip(axes, configs):
        counts = _simulate(H, Phi)
        total  = sum(counts.values())
        labels = [f"Server {k}" for k in counts]
        values = [counts[k] for k in counts]
        ideal  = total / len(values)
        ax.bar(labels, values, color="mediumseagreen", edgecolor="white")
        ax.axhline(ideal, color="tomato", linestyle="--", linewidth=1.2, label=f"Ideal ({ideal:.0f})")
        ax.set_title(title, fontsize=9)
        ax.set_ylabel("Simulated requests")
        ax.legend(fontsize=8)
        for k, v in counts.items():
            print(f"  [{title[:8].strip()}] Server {k}: {v} ({v/total*100:.1f} %)")

    plt.tight_layout()
    plt.savefig("a4_bar_comparison.png", dpi=150)
    print("Saved → a4_bar_comparison.png")
    plt.show()

    #  sub-figure 2: scalability line comparison (N=2..6) 
    fig, ax = plt.subplots(figsize=(8, 5))
    ns = list(range(2, 7))
    for title, H, Phi in configs:
        avgs = []
        for n in ns:
            counts = _simulate(H, Phi, n_servers=n)
            vals   = list(counts.values())
            avgs.append(sum(vals) / len(vals) if vals else 0)
        ax.plot(ns, avgs, marker='o', label=title.split('\n')[0])

    ideal_line = [TOTAL_REQUESTS / n for n in ns]
    ax.plot(ns, ideal_line, 'k--', alpha=0.4, label="Ideal")
    ax.set_title(f"A-4: Avg load per server vs N  hash function comparison")
    ax.set_xlabel("N")
    ax.set_ylabel("Avg requests per server")
    ax.set_xticks(ns)
    ax.legend()
    plt.tight_layout()
    plt.savefig("a4_scalability_comparison.png", dpi=150)
    print("Saved → a4_scalability_comparison.png")
    plt.show()

# entry point

if __name__ == "__main__":
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    if cmd in ("a1", "all"): task_a1()
    if cmd in ("a2", "all"): task_a2()
    if cmd in ("a3", "all"): task_a3()
    if cmd in ("a4", "all"): task_a4()
