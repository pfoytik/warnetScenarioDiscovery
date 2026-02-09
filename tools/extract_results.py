#!/usr/bin/env python3
"""
Extract Scenario Results from Commander Logs

Extracts base64-encoded results from warnet commander logs and saves them
to an organized directory structure.

Usage:
    # From commander logs directly
    warnet logs | python extract_results.py

    # From a saved log file
    python extract_results.py < commander.log

    # Specify output directory
    python extract_results.py --output-dir ./my_results < commander.log

    # Extract from a specific log file
    python extract_results.py --log-file commander.log

The script will:
1. Find RESULTS_EXPORT_START/END markers in logs
2. Extract and decode the base64 results data
3. Save to: <output_dir>/<results_id>/results.json
4. Also save individual oracle outputs for convenience
"""

import argparse
import base64
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from text."""
    # ANSI escape codes: \x1b[...m or \033[...m
    # The ... can contain numbers, semicolons, and other chars
    ansi_pattern = r'\x1b\[[0-9;]*m|\033\[[0-9;]*m'
    return re.sub(ansi_pattern, '', text)


def extract_data_line(line: str) -> str:
    """
    Extract the RESULTS_DATA payload from a log line.

    Handles various log formats:
    - "RESULTS_DATA:abc123..."
    - "PartitionMinerWithPools - RESULTS_DATA:abc123..."
    - "2024-01-01 12:00:00 INFO - PartitionMinerWithPools - RESULTS_DATA:abc123..."

    Also cleans up any non-base64 characters that might be added by logging systems.
    """
    # First, strip ANSI escape codes from the entire line
    line = strip_ansi_codes(line)

    # Find RESULTS_DATA: and extract everything after it
    marker = 'RESULTS_DATA:'
    idx = line.find(marker)
    if idx == -1:
        return ''

    raw_data = line[idx + len(marker):]

    # Clean: keep ONLY valid base64 characters (A-Z, a-z, 0-9, +, /, =)
    # This removes any remaining whitespace, control chars, etc.
    cleaned = re.sub(r'[^A-Za-z0-9+/=]', '', raw_data)

    return cleaned


def extract_id_line(line: str) -> str:
    """Extract the RESULTS_ID payload from a log line."""
    # First strip ANSI codes
    line = strip_ansi_codes(line)

    marker = 'RESULTS_ID:'
    idx = line.find(marker)
    if idx == -1:
        return ''
    # Get everything after marker, strip whitespace and any control chars
    raw = line[idx + len(marker):]
    # Remove any non-printable characters
    cleaned = ''.join(c for c in raw if c.isprintable())
    return cleaned.strip()


def fix_base64_padding(b64_string: str) -> str:
    """
    Fix base64 padding issues.

    Base64 strings must have a length that is a multiple of 4.
    Add '=' padding characters as needed.

    Also handles the case where = signs appear in the middle
    (which can happen if chunks were truncated and concatenated).
    """
    # First, strip any trailing = signs, then re-add correct padding
    stripped = b64_string.rstrip('=')

    # Add padding if needed
    padding_needed = (4 - len(stripped) % 4) % 4
    return stripped + '=' * padding_needed


def extract_results_from_logs(log_content: str, verbose: bool = False) -> dict:
    """
    Extract results from log content.

    Args:
        log_content: Full log text
        verbose: Print debug info

    Returns:
        Dict with results_id and decoded results data
    """
    lines = log_content.split('\n')

    results_id = None
    data_chunks = []
    in_export_block = False

    for i, line in enumerate(lines):
        # Strip ANSI codes and whitespace
        line = strip_ansi_codes(line.strip())

        if 'RESULTS_EXPORT_START' in line:
            in_export_block = True
            data_chunks = []
            if verbose:
                print(f"[DEBUG] Found RESULTS_EXPORT_START at line {i+1}")
            continue

        if 'RESULTS_EXPORT_END' in line:
            in_export_block = False
            if verbose:
                print(f"[DEBUG] Found RESULTS_EXPORT_END at line {i+1}")
                print(f"[DEBUG] Collected {len(data_chunks)} data chunks")
            continue

        if in_export_block:
            if 'RESULTS_ID:' in line:
                results_id = extract_id_line(line)
                if verbose:
                    print(f"[DEBUG] Found RESULTS_ID: {results_id}")
            elif 'RESULTS_DATA:' in line:
                chunk = extract_data_line(line)
                if chunk:
                    data_chunks.append(chunk)
                    if verbose and len(data_chunks) <= 3:
                        print(f"[DEBUG] Chunk {len(data_chunks)}: {chunk[:50]}...")

    if not data_chunks:
        raise ValueError("No RESULTS_DATA found in logs. Make sure the scenario completed successfully.")

    # Combine all chunks (already cleaned per-chunk)
    combined_b64 = ''.join(data_chunks)

    if verbose:
        print(f"[DEBUG] Combined base64 length: {len(combined_b64)}")
        print(f"[DEBUG] Length mod 4: {len(combined_b64) % 4}")

        # Check chunk lengths - they should all be 1000 except the last
        chunk_lengths = [len(c) for c in data_chunks]
        unusual_chunks = [(i, l) for i, l in enumerate(chunk_lengths[:-1]) if l != 1000]
        if unusual_chunks:
            print(f"[DEBUG] Chunks not exactly 1000: {len(unusual_chunks)} chunks")
            print(f"[DEBUG] Sample unusual lengths: {unusual_chunks[:5]}")
        else:
            print(f"[DEBUG] All {len(data_chunks)-1} full chunks are exactly 1000 chars")
        print(f"[DEBUG] Last chunk length: {chunk_lengths[-1]}")

        # Check for = signs in the middle (indicates truncation issues)
        equals_positions = [i for i, c in enumerate(combined_b64[:-4]) if c == '=']
        if equals_positions:
            print(f"[DEBUG] WARNING: Found {len(equals_positions)} '=' signs before the last 4 chars")
            print(f"[DEBUG] Positions: {equals_positions[:10]}")

        # Show first/last of combined
        print(f"[DEBUG] First 100 chars: {combined_b64[:100]}")
        print(f"[DEBUG] Last 100 chars: {combined_b64[-100:]}")

    # Fix padding issues (strip trailing =, then add correct padding)
    original_len = len(combined_b64)
    combined_b64 = fix_base64_padding(combined_b64)

    if verbose:
        print(f"[DEBUG] After padding fix, length: {len(combined_b64)} (was {original_len})")

    try:
        decoded = base64.b64decode(combined_b64).decode('utf-8')
        results = json.loads(decoded)
    except base64.binascii.Error as e:
        # More detailed error for base64 issues
        # Try to find where it fails by decoding in chunks
        if verbose:
            print(f"[DEBUG] Trying to locate error position...")
            test_size = 10000
            for i in range(0, len(combined_b64), test_size):
                chunk = combined_b64[:i+test_size]
                # Add padding for partial decode
                padded = chunk + '=' * ((4 - len(chunk) % 4) % 4)
                try:
                    base64.b64decode(padded)
                except:
                    print(f"[DEBUG] Error occurs around position {i} to {i+test_size}")
                    print(f"[DEBUG] Content at error region: ...{combined_b64[max(0,i-50):i+100]}...")
                    break
        raise ValueError(f"Base64 decode failed: {e}. Combined length: {len(combined_b64)}, mod 4: {len(combined_b64) % 4}")
    except json.JSONDecodeError as e:
        # Show where JSON parsing failed
        raise ValueError(f"JSON decode failed at position {e.pos}: {e.msg}. First 200 chars: {decoded[:200]}")
    except Exception as e:
        raise ValueError(f"Failed to decode results: {e}")

    return {
        'results_id': results_id or 'unknown',
        'data': results
    }


def save_results(results: dict, output_dir: Path) -> Path:
    """
    Save results to organized directory structure.

    Args:
        results: Dict with results_id and data
        output_dir: Base output directory

    Returns:
        Path to the results directory
    """
    results_id = results['results_id']
    data = results['data']

    # Create results directory
    results_dir = output_dir / results_id
    results_dir.mkdir(parents=True, exist_ok=True)

    # Save consolidated results
    consolidated_path = results_dir / 'results.json'
    with open(consolidated_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved: {consolidated_path}")

    # Save individual oracle outputs for convenience
    oracle_mappings = {
        'pools': 'partition_pools.json',
        'economic': 'partition_economic.json',
        'prices': 'partition_prices.json',
        'fees': 'partition_fees.json',
        'difficulty': 'partition_difficulty.json',
        'reorg': 'partition_reorg.json',
    }

    for key, filename in oracle_mappings.items():
        if key in data:
            oracle_path = results_dir / filename
            with open(oracle_path, 'w') as f:
                json.dump(data[key], f, indent=2)
            print(f"Saved: {oracle_path}")

    # Save metadata separately for quick reference
    if 'metadata' in data:
        meta_path = results_dir / 'metadata.json'
        with open(meta_path, 'w') as f:
            json.dump(data['metadata'], f, indent=2)
        print(f"Saved: {meta_path}")

    # Save summary separately
    if 'summary' in data:
        summary_path = results_dir / 'summary.json'
        with open(summary_path, 'w') as f:
            json.dump(data['summary'], f, indent=2)
        print(f"Saved: {summary_path}")

    # Save time series as CSV for easy charting
    if 'time_series' in data:
        ts = data['time_series']
        csv_path = results_dir / 'time_series.csv'
        with open(csv_path, 'w') as f:
            # Write header
            headers = list(ts.keys())
            f.write(','.join(headers) + '\n')
            # Write rows
            num_rows = len(ts.get('timestamps', []))
            for i in range(num_rows):
                row = [str(ts[h][i]) if i < len(ts[h]) else '' for h in headers]
                f.write(','.join(row) + '\n')
        print(f"Saved: {csv_path}")

        # Also save as JSON for programmatic access
        ts_json_path = results_dir / 'time_series.json'
        with open(ts_json_path, 'w') as f:
            json.dump(ts, f, indent=2)
        print(f"Saved: {ts_json_path}")

    # Save pool decision history as CSV for charting opportunity costs
    if 'pools' in data and 'decision_history' in data['pools']:
        decisions = data['pools']['decision_history']
        if decisions:
            decisions_csv_path = results_dir / 'pool_decisions.csv'
            with open(decisions_csv_path, 'w') as f:
                # Write header based on first decision
                headers = list(decisions[0].keys())
                f.write(','.join(headers) + '\n')
                # Write rows
                for d in decisions:
                    row = [str(d.get(h, '')) for h in headers]
                    f.write(','.join(row) + '\n')
            print(f"Saved: {decisions_csv_path}")

    # Create a human-readable summary
    summary_txt_path = results_dir / 'summary.txt'
    with open(summary_txt_path, 'w') as f:
        f.write(f"Results ID: {results_id}\n")
        f.write(f"{'='*50}\n\n")

        if 'metadata' in data:
            meta = data['metadata']
            f.write("CONFIGURATION\n")
            f.write(f"  Timestamp: {meta.get('timestamp', 'N/A')}\n")
            f.write(f"  Duration: {meta.get('duration_seconds', 0)/60:.1f} minutes\n")
            f.write(f"  Pool Scenario: {meta.get('pool_scenario', 'N/A')}\n")
            f.write(f"  Economic Scenario: {meta.get('economic_scenario', 'N/A')}\n")
            f.write(f"  Difficulty Enabled: {meta.get('difficulty_enabled', False)}\n")
            f.write(f"  Reorg Metrics Enabled: {meta.get('reorg_metrics_enabled', False)}\n")
            f.write("\n")

        if 'summary' in data:
            s = data['summary']
            f.write("FINAL STATE\n")
            f.write(f"  Blocks Mined: v27={s['blocks_mined'].get('v27', 0)}, v26={s['blocks_mined'].get('v26', 0)}\n")
            f.write(f"  Total Blocks: {s.get('total_blocks', 0)}\n")
            f.write(f"  Final Hashrate: v27={s['final_hashrate'].get('v27', 0):.1f}%, v26={s['final_hashrate'].get('v26', 0):.1f}%\n")
            f.write(f"  Final Economic: v27={s['final_economic'].get('v27', 0):.1f}%, v26={s['final_economic'].get('v26', 0):.1f}%\n")
            f.write(f"  Final Prices: v27=${s['final_prices'].get('v27', 0):,.0f}, v26=${s['final_prices'].get('v26', 0):,.0f}\n")
            f.write("\n")

        if 'difficulty' in data and 'winning_fork' in data['difficulty']:
            d = data['difficulty']
            f.write("DIFFICULTY/CHAINWORK\n")
            f.write(f"  Winning Fork: {d.get('winning_fork', 'N/A')}\n")
            for fork_id, state in d.get('forks', {}).items():
                f.write(f"  {fork_id}: difficulty={state.get('current_difficulty', 0):.6f}, chainwork={state.get('cumulative_chainwork', 0):.4f}\n")
            f.write("\n")

        if 'reorg' in data:
            r = data['reorg']
            ns = r.get('network_summary', {})
            f.write("REORG METRICS\n")
            f.write(f"  Total Reorg Events: {ns.get('total_reorg_events', 0)}\n")
            f.write(f"  Total Reorg Mass: {ns.get('total_reorg_mass', 0)} blocks\n")
            f.write(f"  Total Blocks Orphaned: {ns.get('total_blocks_orphaned', 0)}\n")
            if ns.get('total_blocks_mined', 0) > 0:
                orphan_rate = ns.get('total_blocks_orphaned', 0) / ns['total_blocks_mined'] * 100
                f.write(f"  Network Orphan Rate: {orphan_rate:.2f}%\n")
            f.write("\n")

            if 'reunion_analysis' in r:
                ra = r['reunion_analysis']
                f.write("REUNION ANALYSIS (hypothetical merge)\n")
                f.write(f"  Winning Fork: {ra.get('winning_fork', 'N/A')}\n")
                f.write(f"  Losing Fork Depth: {ra.get('losing_fork_depth', 0)} blocks\n")
                f.write(f"  Nodes on Losing Fork: {ra.get('num_nodes_on_losing_fork', 0)}\n")
                f.write(f"  Additional Orphans: {ra.get('additional_orphans', 0)}\n")

    print(f"Saved: {summary_txt_path}")

    return results_dir


def main():
    parser = argparse.ArgumentParser(
        description='Extract scenario results from commander logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--output-dir', '-o', type=str, default='./results',
                        help='Output directory for results (default: ./results)')
    parser.add_argument('--log-file', '-f', type=str, default=None,
                        help='Log file to read (default: stdin)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print debug information during extraction')

    args = parser.parse_args()

    # Read log content
    if args.log_file:
        with open(args.log_file, 'r') as f:
            log_content = f.read()
    else:
        if sys.stdin.isatty():
            print("Reading from stdin... (pipe logs or use --log-file)")
            print("Example: warnet logs | python extract_results.py")
            print("Or: python extract_results.py --log-file commander.log")
            sys.exit(1)
        log_content = sys.stdin.read()

    # Extract results
    try:
        results = extract_results_from_logs(log_content, verbose=args.verbose)
        print(f"\nFound results: {results['results_id']}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Save results
    output_dir = Path(args.output_dir)
    results_dir = save_results(results, output_dir)

    print(f"\n{'='*50}")
    print(f"Results saved to: {results_dir}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
