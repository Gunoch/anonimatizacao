#!/usr/bin/env python
# Wrapper script to easily run anonymization tests with various options.

import os
import sys
import argparse
import subprocess
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Run PDF anonymization tests')
    
    parser.add_argument('--type', choices=['quick', 'thorough', 'performance'], default='quick',
                        help='Type of test to run')
    parser.add_argument('--output', type=str, default='test_results',
                        help='Output directory for test results')
    
    args = parser.parse_args()
    
    # Create timestamp for this test run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output, f"{args.type}_test_{timestamp}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine test parameters based on type
    if args.type == 'quick':
        print("Running quick test (3 PDFs, varied complexity)...")
        count = 3
    elif args.type == 'thorough':
        print("Running thorough test (10 PDFs, all complexities)...")
        count = 10
    else:  # performance
        print("Running performance test (5 PDFs with high complexity)...")
        count = 5

    cmd = [
        "python",
        "test_utils.py",
        "--mode",
        "batch",
        "--count",
        str(count),
        "--output",
        output_dir,
    ]

    # Run the selected test
    subprocess.run(cmd)
    
    print(f"Tests completed. Results available in: {output_dir}")
    print(f"Test report: {os.path.join(output_dir, 'test_report.pdf')}")

if __name__ == "__main__":
    main()
