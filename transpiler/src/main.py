#!/usr/bin/env python3
"""
编译器主程序
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from compiler import compile_rustlike_to_c
except ImportError:
    from transpiler.src.compiler import compile_rustlike_to_c

def main():
    input_file = "input.txt"
    output_file = "output.txt"
    
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            source_code = f.read().strip()
        
        c_code = compile_rustlike_to_c(source_code)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(c_code)
        
        print("-" * 50)
        
    except Exception as e:
        print(f"Compile Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()