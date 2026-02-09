#!/bin/bash
#
# Save Results from Latest Scenario Run
#
# Automatically fetches logs from the most recent commander pod
# and extracts results to an organized directory.
#
# Usage:
#   ./save_results.sh                    # Save to ./results/
#   ./save_results.sh -o /path/to/dir    # Save to custom directory
#   ./save_results.sh -n my-run-name     # Save with custom name subdirectory
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="./results"
NAMESPACE="warnet"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [-o OUTPUT_DIR] [-n NAMESPACE]"
            echo ""
            echo "Options:"
            echo "  -o, --output-dir   Output directory (default: ./results)"
            echo "  -n, --namespace    Kubernetes namespace (default: warnet)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Find the most recent commander pod
echo "Looking for commander pod in namespace: $NAMESPACE"
COMMANDER_POD=$(kubectl get pods -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp | grep commander | tail -1 | awk '{print $1}')

if [ -z "$COMMANDER_POD" ]; then
    echo "Error: No commander pod found in namespace $NAMESPACE"
    echo ""
    echo "Available pods:"
    kubectl get pods -n "$NAMESPACE"
    exit 1
fi

echo "Found commander pod: $COMMANDER_POD"

# Get pod status
POD_STATUS=$(kubectl get pod "$COMMANDER_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
echo "Pod status: $POD_STATUS"

# Get logs and extract results
echo ""
echo "Fetching logs and extracting results..."
kubectl logs "$COMMANDER_POD" -n "$NAMESPACE" | python3 "$SCRIPT_DIR/extract_results.py" -o "$OUTPUT_DIR"

echo ""
echo "Done!"
