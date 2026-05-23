#!/usr/bin/env python3
"""
阶段 0 端到端测试
验证：基本语法、Option、Vec、match、控制流、索引赋值
"""

import sys
import os
import subprocess
import tempfile

# 确保能导入 transpiler.src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from transpiler.src.compiler import compile_rustlike_to_c


def run_test(name: str, source_code: str, expected_patterns: list = None) -> bool:
    """
    编译源码为 C，用 gcc 编译运行，检查是否成功。
    
    expected_patterns: 可选，检查 stdout 是否包含这些子串
    """
    print(f"\n{'='*50}")
    print(f"测试: {name}")
    print(f"{'='*50}")
    
    try:
        # 1. 编译为 C
        c_code = compile_rustlike_to_c(source_code)
        print("生成的 C 代码:")
        print(c_code[:1500] + "..." if len(c_code) > 1500 else c_code)
        
        # 2. 写入临时 C 文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(c_code)
            c_file = f.name
        
        # 3. gcc 编译
        exe_file = c_file.replace('.c', '')
        runtime_dir = os.path.join(os.path.dirname(__file__), '..', 'runtime')
        
        result = subprocess.run(
            ['gcc', '-o', exe_file, c_file, '-I', runtime_dir],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"GCC 编译失败:\n{result.stderr}")
            os.unlink(c_file)
            return False
        
        # 4. 运行
        result = subprocess.run([exe_file], capture_output=True, text=True)
        
        # 清理
        os.unlink(c_file)
        if os.path.exists(exe_file):
            os.unlink(exe_file)
        
        if result.returncode != 0:
            print(f"运行失败 (exit {result.returncode}):\n{result.stderr}")
            return False
        
        print(f"运行成功，stdout: {repr(result.stdout)}")
        
        # 5. 可选：检查输出模式
        if expected_patterns:
            for pattern in expected_patterns:
                if pattern not in result.stdout:
                    print(f"输出检查失败: 未找到 '{pattern}'")
                    return False
            print("输出模式检查通过")
        
        print("通过")
        return True
        
    except Exception as e:
        print(f"测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== 测试用例 ====================

def test_basic_arithmetic():
    return run_test("基本算术", """
fn mytest() {
    let a = 10;
    let b = 20;
    let c = a + b;
}
""")


def test_if_else():
    return run_test("if/else", """
fn mytest() {
    let x = 5;
    if x > 0 {
        x = x - 1;
    } else {
        x = x + 1;
    }
}
""")


def test_while():
    return run_test("while 循环", """
fn mytest() {
    let i = 0;
    while i < 10 {
        i = i + 1;
    }
}
""")


def test_for_in():
    return run_test("for_in 循环", """
fn mytest() {
    let arr = [1, 2, 3];
    let sum = 0;
    for x in arr {
        sum = sum + x;
    }
}
""")


def test_option_some_none():
    return run_test("Option Some/None", """
fn mytest() {
    let x = Some(5);
    let y = None;
    let a = is_some(x);
    let b = is_none(y);
}
""")


def test_match_basic():
    return run_test("match 基本", """
fn mytest() {
    let x = Some(10);
    let y = match x {
        Some(v) => v + 1,
        None => 0
    };
}
""")


def test_match_complex():
    return run_test("match 复杂表达式", """
fn mytest() {
    let x = Some(5);
    let y = match x {
        Some(v) => v * 2 + 1,
        None => 0
    };
}
""")


def test_vec_all_ops():
    return run_test("Vector 全操作", """
fn mytest() {
    let v = [1, 2, 3];
    v.push(4);
    v[1] = 99;
    let a = v[1];
    let b = v.len();
    let c = v.pop();
    v.remove(0);
}
""")


def test_find_function():
    """文档中的 find 示例"""
    return run_test("find 函数", """
fn find(arr, target) {
    for x in arr {
        if x > target {
            return Some(x);
        }
    }
    return None;
}

fn mytest() {
    let result1 = find([1, 3, 5, 2, 4], 3);
    let result2 = find([1, 2, 3], 5);
}
""")


# ==================== 主入口 ====================

TESTS = [
    test_basic_arithmetic,
    test_if_else,
    test_while,
    test_for_in,
    test_option_some_none,
    test_match_basic,
    test_match_complex,
    test_vec_all_ops,
    test_find_function,
]


def main():
    print("阶段 0 端到端测试开始")
    
    passed = 0
    failed = 0
    
    for test in TESTS:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"结果: {passed} 通过, {failed} 失败")
    print(f"{'='*50}")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())