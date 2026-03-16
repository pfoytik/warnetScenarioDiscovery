#!/usr/bin/env python3
"""
Sweep progress monitor.

Usage:
    python tools/monitor_sweeps.py          # print once
    python tools/monitor_sweeps.py --watch  # refresh every 60s
    python tools/monitor_sweeps.py --watch --interval 30
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ── Sweep definitions ────────────────────────────────────────────────────────

SWEEPS = [
    {
        "name": "econ_committed_2016_grid",
        "label": "Sweep 1 — econ_committed_2016_grid (2016-block)",
        "results_dir": "econ_committed_2016_grid/results",
        "total": 45,
        "namespaces": [f"grid2016-c{i}" for i in range(9)],
        "log_prefix": "/tmp/sweep_c",
        "log_suffix": ".log",
        "log_ids": list(range(9)),
    },
    {
        "name": "targeted_sweep7_esp_144",
        "label": "Sweep 2a — targeted_sweep7_esp (144-block)",
        "results_dir": "targeted_sweep7_esp/results_144",
        "total": 9,
        "namespaces": [f"esp-144-{i}" for i in range(9)],
        "log_prefix": "/tmp/sweep_esp144_",
        "log_suffix": ".log",
        "log_ids": list(range(9)),
    },
    {
        "name": "targeted_sweep7_esp_2016",
        "label": "Sweep 2b — targeted_sweep7_esp (2016-block)",
        "results_dir": "targeted_sweep7_esp/results_2016",
        "total": 9,
        "namespaces": [f"esp-2016-{i}" for i in range(9)],
        "log_prefix": "/tmp/sweep_esp2016_",
        "log_suffix": ".log",
        "log_ids": list(range(9)),
    },
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def run(cmd):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception:
        return ""


def count_completed(results_dir: str) -> tuple[int, int]:
    """Returns (completed, failed) counts based on results.json presence."""
    p = Path(results_dir)
    if not p.exists():
        return 0, 0
    completed = sum(1 for d in p.iterdir() if d.is_dir() and (d / "results.json").exists())
    # failed = scenario dirs with log but no results.json (and not currently running)
    failed = 0
    progress_file = p / "sweep_progress.json"
    if progress_file.exists():
        try:
            data = json.loads(progress_file.read_text())
            failed = sum(1 for h in data.get("history", []) if h.get("status") != "OK")
        except Exception:
            pass
    return completed, failed


def get_pod_counts(namespace: str) -> tuple[int, int]:
    out = run(f"kubectl get pods -n {namespace} 2>/dev/null")
    running = out.count("Running")
    pending = out.count("Pending")
    return running, pending


def get_live_processes() -> set[str]:
    """Return set of namespace values from live 3_run_sweep.py processes."""
    out = run("ps aux | grep 3_run_sweep | grep -v grep")
    live = set()
    for line in out.splitlines():
        parts = line.split()
        for i, part in enumerate(parts):
            if part == "--namespace" and i + 1 < len(parts):
                live.add(parts[i + 1])
    return live


def get_memory_gb() -> tuple[float, float]:
    """Returns (used_gb, total_gb)."""
    out = run("free -m | grep Mem")
    parts = out.split()
    if len(parts) >= 3:
        total = int(parts[1]) / 1024
        used = int(parts[2]) / 1024
        return used, total
    return 0, 0


def bar(completed, total, width=30) -> str:
    if total == 0:
        return "[" + "-" * width + "]"
    filled = int(width * completed / total)
    return "[" + "█" * filled + "-" * (width - filled) + "]"


def eta_str(completed, total, elapsed_since_start: float | None) -> str:
    if completed == 0 or elapsed_since_start is None or elapsed_since_start == 0:
        return "ETA: unknown"
    rate = completed / elapsed_since_start
    remaining = (total - completed) / rate
    return f"ETA: ~{timedelta(seconds=int(remaining))}"


def get_sweep_start_time(results_dir: str) -> float | None:
    p = Path(results_dir) / "sweep_progress.json"
    if p.exists():
        try:
            data = json.loads(p.read_text())
            started = data.get("started")
            if started:
                dt = datetime.fromisoformat(started)
                return dt.timestamp()
        except Exception:
            pass
    return None


def get_failures(results_dir: str) -> list[str]:
    """Collect failed scenario IDs from all progress files."""
    failures = []
    p = Path(results_dir)
    if not p.exists():
        return failures
    # There's one shared sweep_progress.json but with parallel writers it may
    # only reflect one namespace — scan per-scenario logs for errors too
    progress_file = p / "sweep_progress.json"
    if progress_file.exists():
        try:
            data = json.loads(progress_file.read_text())
            for h in data.get("history", []):
                if h.get("status") != "OK":
                    failures.append(h["scenario_id"])
        except Exception:
            pass
    return failures


# ── Render ────────────────────────────────────────────────────────────────────

def render(start_times: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mem_used, mem_total = get_memory_gb()
    live_ns = get_live_processes()
    total_pods = int(run("kubectl get pods --all-namespaces 2>/dev/null | grep -c Running") or 0)
    pending_pods = int(run("kubectl get pods --all-namespaces 2>/dev/null | grep -c Pending") or 0)

    lines = []
    lines.append("=" * 70)
    lines.append(f"  SWEEP MONITOR  —  {now}")
    lines.append("=" * 70)
    lines.append(f"  Memory:  {mem_used:.1f} / {mem_total:.1f} GiB used")
    lines.append(f"  Pods:    {total_pods} running, {pending_pods} pending (all namespaces)")
    lines.append(f"  Processes: {len(live_ns)} sweep runners alive")
    lines.append("")

    grand_completed = 0
    grand_total = 0

    for sweep in SWEEPS:
        completed, failed = count_completed(sweep["results_dir"])
        total = sweep["total"]
        grand_completed += completed
        grand_total += total

        elapsed = None
        if sweep["name"] not in start_times:
            t = get_sweep_start_time(sweep["results_dir"])
            if t:
                start_times[sweep["name"]] = t
        if sweep["name"] in start_times:
            elapsed = time.time() - start_times[sweep["name"]]

        pct = f"{100*completed//total}%" if total else "-%"
        eta = eta_str(completed, total, elapsed)
        elapsed_str = str(timedelta(seconds=int(elapsed))) if elapsed else "?"

        lines.append(f"  {sweep['label']}")
        lines.append(f"  {bar(completed, total)}  {completed}/{total} ({pct})  elapsed={elapsed_str}  {eta}")

        if failed:
            failures = get_failures(sweep["results_dir"])
            lines.append(f"  ⚠  {failed} failed: {', '.join(failures)}")

        # Per-namespace pod status (compact)
        ns_parts = []
        dead_ns = []
        for ns in sweep["namespaces"]:
            running, pending = get_pod_counts(ns)
            ns_short = ns.split("-")[-1]  # c0, c1, 0, 1 etc
            ns_parts.append(f"{ns_short}:{running}{'p' if pending else ''}")
            if ns not in live_ns:
                dead_ns.append(ns)
        lines.append(f"  pods/ns: {' '.join(ns_parts)}")
        if dead_ns:
            lines.append(f"  ⚠  DEAD processes: {', '.join(dead_ns)}")
        lines.append("")

    lines.append("-" * 70)
    lines.append(f"  TOTAL: {grand_completed}/{grand_total} scenarios complete across all sweeps")
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Monitor sweep progress")
    parser.add_argument("--watch", action="store_true", help="Continuously refresh")
    parser.add_argument("--interval", type=int, default=60, help="Refresh interval in seconds (default: 60)")
    args = parser.parse_args()

    start_times = {}

    if args.watch:
        try:
            while True:
                os.system("clear")
                print(render(start_times))
                print(f"\n  Refreshing every {args.interval}s — Ctrl+C to exit")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nMonitor stopped.")
    else:
        print(render(start_times))


if __name__ == "__main__":
    main()
