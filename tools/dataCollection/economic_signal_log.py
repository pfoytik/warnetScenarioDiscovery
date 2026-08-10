#!/usr/bin/env python3
"""
Economic-Side Signal Log
=========================
Structured, weighted tracker for exchange/custodian/payment-processor
positions on BIP-110 — the manual counterpart to bip110_monitor.py's
pool-side signal_pct, producing an economic_split estimate directly
comparable to the simulation's economic_split parameter.

There is no API for this side of the picture; entries are logged by hand
as you observe announcements, so the value this script adds is structure:
a consistent weight tier and stance per entity, collapsed to each
entity's most recent position, rather than an unweighted headcount.

Weight tiers (rough, 1-5):
  1 = small business / minor service
  2 = mid-size exchange or custodian
  3 = large regional exchange / custodian
  4 = major global exchange / large custodian
  5 = dominant exchange, ETF issuer, or systemically important custodian

Usage:
    python3 economic_signal_log.py add --entity "Coinbase" --type exchange \
        --weight 5 --stance oppose --source "https://x.com/..." --notes "..."

    python3 economic_signal_log.py list
    python3 economic_signal_log.py summary
"""

import argparse
import csv
import os
from datetime import datetime, timezone

LOG_FILE = "economic_signals_log.csv"
FIELDNAMES = ["timestamp", "entity", "entity_type", "weight", "stance", "source", "notes"]

ENTITY_TYPES = ["exchange", "custodian", "payment_processor", "miner_adjacent", "other"]
STANCES = ["support", "oppose", "neutral", "undecided"]


# ── Storage ───────────────────────────────────────────────────────────────────

def append_entry(entity, entity_type, weight, stance, source, notes):
    file_exists = os.path.exists(LOG_FILE)
    row = {
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "entity":      entity,
        "entity_type": entity_type,
        "weight":      weight,
        "stance":      stance,
        "source":      source or "",
        "notes":       notes or "",
    }
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"Logged: {entity} ({entity_type}, weight={weight}) -> {stance}")


def read_all_entries():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, newline="") as f:
        return list(csv.DictReader(f))


def latest_per_entity(entries):
    """
    Collapse to the most recent entry per entity (case-insensitive key) so
    an entity that changed its stance over time isn't double-counted --
    only its current position contributes to the summary.
    """
    latest = {}
    for row in entries:
        key = row["entity"].strip().lower()
        if key not in latest or row["timestamp"] > latest[key]["timestamp"]:
            latest[key] = row
    return list(latest.values())


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_add(args):
    append_entry(args.entity, args.entity_type, args.weight, args.stance,
                 args.source, args.notes)


def cmd_list(args):
    entries = latest_per_entity(read_all_entries())
    if not entries:
        print("No entries logged yet.")
        return
    entries.sort(key=lambda r: (-int(r["weight"]), r["entity"]))
    print(f"\n{'Entity':<25} {'Type':<18} {'Wt':>3}  {'Stance':<10}  Last updated")
    print("-" * 84)
    for r in entries:
        print(f"{r['entity']:<25} {r['entity_type']:<18} {r['weight']:>3}  "
              f"{r['stance']:<10}  {r['timestamp']}")
    print()


def cmd_summary(args):
    entries = latest_per_entity(read_all_entries())
    if not entries:
        print("No entries logged yet.")
        return

    totals = {"support": 0, "oppose": 0, "neutral": 0, "undecided": 0}
    for r in entries:
        w = int(r["weight"])
        stance = r["stance"] if r["stance"] in totals else "undecided"
        totals[stance] += w

    tracked = sum(totals.values())
    silent = totals["neutral"] + totals["undecided"]
    active_denom = totals["support"] + totals["oppose"]

    print(f"\n{'='*64}")
    print("Economic-Side Signal Summary")
    print(f"{'='*64}")
    print(f"  Entities tracked      : {len(entries)}")
    print(f"  Total weight tracked  : {tracked}")
    print(f"  Support weight        : {totals['support']}")
    print(f"  Oppose weight         : {totals['oppose']}")
    print(f"  Neutral/undecided wt  : {silent}")

    if active_denom:
        active_split = totals["support"] / active_denom
        print(f"\n  economic_split (of entities that have taken a position):")
        print(f"    {active_split:.3f}  ({active_split*100:.1f}% support)")
    else:
        print("\n  economic_split (active): undefined -- no support/oppose entries yet")

    if tracked:
        conservative_split = totals["support"] / tracked
        print(f"\n  economic_split (conservative -- silence counts as not-yet-v27,")
        print(f"  since unclaimed custody stays on the incumbent chain by default):")
        print(f"    {conservative_split:.3f}  ({conservative_split*100:.1f}% support)")

    print(f"\n  Paper reference points: cascade floor ~0.45-0.50, override ~0.78-0.82")
    print(f"{'='*64}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Economic-side BIP-110 signal log",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Log a new observation")
    p_add.add_argument("--entity", required=True, help="Exchange/custodian/processor name")
    p_add.add_argument("--type", dest="entity_type", required=True,
                        choices=ENTITY_TYPES, help="Entity category")
    p_add.add_argument("--weight", type=int, required=True, choices=range(1, 6),
                        help="Rough size tier, 1 (small) - 5 (dominant)")
    p_add.add_argument("--stance", required=True, choices=STANCES,
                        help="Current position on BIP-110")
    p_add.add_argument("--source", default="", help="URL or citation for this observation")
    p_add.add_argument("--notes", default="", help="Free-text notes")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="Show current (latest) stance per entity")
    p_list.set_defaults(func=cmd_list)

    p_sum = sub.add_parser("summary", help="Compute weighted economic_split estimate")
    p_sum.set_defaults(func=cmd_summary)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
