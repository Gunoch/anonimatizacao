#!/usr/bin/env python
# filepath: c:\Users\gusta\OneDrive\Documentos\' Ctrl play\Anonimatizacao\run_tests.py
"""
Wrapper script to easily run anonymization tests with various options.
"""

print("run_tests.py started successfully!") # ADD THIS LINE
import sys # ADD THIS LINE

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
        cmd = ["python", "test_utils.py", "--mode", "batch", "--count", "3", "--output", output_dir]
        
    elif args.type == 'thorough':
        print("Running thorough test (10 PDFs, all complexities)...")
        cmd = ["python", "test_utils.py", "--mode", "batch", "--count", "10", "--output", output_dir]
        
    elif args.type == 'performance':
        print("Running performance test (5 PDFs with high complexity)...")
        # Generate custom high-complexity PDFs for performance testing
        test_pdfs = []
        for i in range(5):
            pages = (i+1) * 5  # 5, 10, 15, 20, 25 pages
            pdf_path = os.path.join(output_dir, f"perf_test_{pages}p.pdf")
            
            # Call test_utils to generate a performance test PDF
            gen_cmd = ["python", "test_utils.py", "--mode", "generate", "--output", output_dir]
            subprocess.run(gen_cmd)
            
            # Now test each generated PDF
            cmd = ["python", "test_utils.py", "--mode", "batch", "--count", "5", "--output", output_dir]
    
    # Run the selected test
    subprocess.run(cmd)
    
    print(f"Tests completed. Results available in: {output_dir}")
    print(f"Test report: {os.path.join(output_dir, 'test_report.pdf')}")

if __name__ == "__main__":
    main()
