#!/usr/bin/env python3
"""
编译器主程序
"""

import sys
import os

# 确保可以导入 src 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from compiler import compile_rustlike_to_c
except ImportError:
    # 如果直接运行而不是作为模块运行
    from transpiler.src.compiler import compile_rustlike_to_c

def main():
    # 设置默认文件名
    input_file = "input.txt"
    output_file = "output.txt"
    
    # 处理命令行参数
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在")
        sys.exit(1)
    
    try:
        # 读取源码
        with open(input_file, 'r', encoding='utf-8') as f:
            source_code = f.read().strip()
        
        if not source_code:
            print(f"警告: {input_file} 为空")
            return
        
        print(f"正在编译: {input_file}")
        print(f"输出文件: {output_file}")
        
        # 编译
        c_code = compile_rustlike_to_c(source_code)
        
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(c_code)
        
        print("编译成功！")
        
        print("-" * 50)
        
    except Exception as e:
        print(f"编译失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()