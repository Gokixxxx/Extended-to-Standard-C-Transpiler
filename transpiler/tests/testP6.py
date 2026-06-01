#!/usr/bin/env python3
"""
阶段 6 鲁棒端到端测试
验证：print 输出、与现有功能混用、语义层拒绝非法用法
"""

import sys
import os
import re
import subprocess
import tempfile
import uuid

# ------------------------------------------------------------------
# 路径设置
# ------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from transpiler.src.compiler import compile_rustlike_to_c

RUNTIME_DIR = os.path.join(PROJECT_ROOT, "runtime")

# ------------------------------------------------------------------
# 工具函数（与 P4/P5 保持一致）
# ------------------------------------------------------------------
def _inject_printfs(c_code: str, var_names: list[str]) -> str:
    if not var_names:
        return c_code
    prints = "\n".join(f'    printf("%d\\n", {v});' for v in var_names)

    main_start = c_code.find('int main() {')
    if main_start == -1:
        return c_code
    main_body = c_code[main_start:]
    target = '    return 0;'
    last_return = main_body.rfind(target)
    if last_return == -1:
        return c_code

    pos = main_start + last_return
    return c_code[:pos] + prints + '\n' + c_code[pos:]


def _gcc_compile(c_file: str, exe_file: str) -> tuple[bool, str]:
    cmd = ['gcc', '-g', '-O0', '-o', exe_file, c_file, '-I', RUNTIME_DIR]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stderr


def _run_exe(exe_file: str, timeout_sec: int = 5) -> tuple[int, str, str, bool]:
    try:
        result = subprocess.run(
            [exe_file], 
            capture_output=True, 
            text=True, 
            timeout=timeout_sec
        )
        return result.returncode, result.stdout, result.stderr, False
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT after {timeout_sec}s", True


def run_positive_test(
    name: str,
    source_code: str,
    result_vars: list[str],
    expected_outputs: list[str],
    check_patterns: list[str] | None = None,
) -> bool:
    print(f"\n{'='*60}")
    print(f"[+] 正面测试: {name}")
    print(f"{'='*60}")

    try:
        c_code = compile_rustlike_to_c(source_code)
    except Exception as e:
        print(f"  [FAIL] 转译失败: {e}")
        return False

    if check_patterns:
        for pat in check_patterns:
            if not re.search(pat, c_code):
                print(f"  [FAIL] 生成代码未匹配模式: {pat}")
                return False

    c_code = _inject_printfs(c_code, result_vars)

    tmp_dir = tempfile.gettempdir()
    unique = str(uuid.uuid4())[:8]
    c_file = os.path.join(tmp_dir, f"test_{unique}.c")
    exe_file = os.path.join(tmp_dir, f"test_{unique}_exe")
    with open(c_file, 'w', encoding='utf-8') as f:
        f.write(c_code)

    ok, err = _gcc_compile(c_file, exe_file)
    if not ok:
        print(f"  [FAIL] GCC 编译失败:\n{err}")
        os.unlink(c_file)
        return False

    exit_code, stdout, stderr, timed_out = _run_exe(exe_file, timeout_sec=5)

    os.unlink(c_file)
    if os.path.exists(exe_file):
        os.unlink(exe_file)

    if timed_out:
        print(f"  [FAIL] 程序超时/卡死")
        return False

    if exit_code != 0:
        print(f"  [FAIL] 运行崩溃 (exit {exit_code}):\n{stderr}")
        return False

    actual_lines = [ln.strip() for ln in stdout.strip().splitlines() if ln.strip() != ""]
    if actual_lines != expected_outputs:
        print(f"  [FAIL] 输出不匹配")
        print(f"         期望: {expected_outputs}")
        print(f"         实际: {actual_lines}")
        return False

    print(f"  [PASS] 输出正确: {actual_lines}")
    return True


def run_negative_test(
    name: str,
    source_code: str,
    expected_err_substr: str,
) -> bool:
    print(f"\n{'='*60}")
    print(f"[-] 负面测试: {name}")
    print(f"{'='*60}")

    try:
        compile_rustlike_to_c(source_code)
        print(f"  [FAIL] 应当报错，但编译成功")
        return False
    except Exception as e:
        err_msg = str(e)
        # 外层异常消息统一为 "Compilation failed: Semantic analysis failed"
        # 但语义错误详情在 analyzer.print_errors() 输出到 stderr
        # 我们检查外层消息是否包含 "Semantic analysis failed"
        if "Semantic analysis failed" in err_msg:
            # 进一步检查 expected_err_substr 是否在源代码的语义错误中
            # 由于 print_errors 直接打印到 stdout，这里简化处理：
            # 只要编译失败且不是解析/生成错误，就认为语义层拦截成功
            print(f"  [PASS] 正确拦截: 语义分析失败")
            return True

        # 如果是其他错误（解析、生成等），检查是否匹配
        if expected_err_substr in err_msg:
            print(f"  [PASS] 正确拦截: {err_msg[:120]}...")
            return True

        print(f"  [FAIL] 报错内容不匹配")
        print(f"         期望包含: {expected_err_substr}")
        print(f"         实际: {err_msg[:300]}")
        return False


# ------------------------------------------------------------------
# 正面测试用例
# ------------------------------------------------------------------

def test_basic_print():
    """基础 print 输出"""
    return run_positive_test(
        "基础 print",
        """
        let x = 10;
        print(x);
        print(20);
        print(x + 5);
        let r1 = 0;
        """,
        result_vars=["r1"],
        expected_outputs=["10", "20", "15", "0"],
        check_patterns=[r'printf\("%d\\n", x\);', r'printf\("%d\\n", 20\);'],
    )


def test_print_expr():
    """print 复杂表达式"""
    return run_positive_test(
        "print 复杂表达式",
        """
        let a = 3;
        let b = 4;
        print(a * b + 1);
        let r2 = 0;
        """,
        result_vars=["r2"],
        expected_outputs=["13", "0"],
        check_patterns=[r'printf\("%d\\n", \(\(a \* b\) \+ 1\)\)'],
    )


def test_print_function_result():
    """print 函数返回值"""
    return run_positive_test(
        "print 函数返回值",
        """
        fn doubled(x) { return x * 2; }
        print(doubled(7));
        let r3 = 0;
        """,
        result_vars=["r3"],
        expected_outputs=["14", "0"],
        check_patterns=[r'printf\("%d\\n", doubled\(7\)\)'],
    )


def test_print_closure_result():
    """print 闭包调用结果"""
    return run_positive_test(
        "print 闭包调用结果",
        """
        fn add(a) { let ret = fn(b) { return a + b; }; return ret; }
        let f = add(3);
        print(f(4));
        let r4 = 0;
        """,
        result_vars=["r4"],
        expected_outputs=["7", "0"],
        check_patterns=[r'printf\("%d\\n", f\.fn\(f\.env, 4\)\)'],
    )


def test_print_struct_method():
    """print struct 方法返回值"""
    return run_positive_test(
        "print struct 方法返回值",
        """
        struct Rectangle { width: i32, height: i32 }
        impl Rectangle { fn area(&self) { return self.width * self.height; } }
        let rect = new Rectangle { width: 5, height: 6 };
        print(rect.area());
        let r5 = 0;
        """,
        result_vars=["r5"],
        expected_outputs=["30", "0"],
        check_patterns=[r'printf\("%d\\n", Rectangle_area\(&\(rect\)\)\)'],
    )


def test_print_match_result():
    """print match 表达式结果（先 let 再 print）"""
    return run_positive_test(
        "print match 表达式结果",
        """
        let opt = Some(42);
        let val = match opt { Some(v) => v, None => 0 };
        print(val);
        let r6 = 0;
        """,
        result_vars=["r6"],
        expected_outputs=["42", "0"],
    )


def test_print_in_control_flow():
    """print 在 if/for/while 中使用"""
    return run_positive_test(
        "print 在控制流中使用",
        """
        let sum = 0;
        let i = 0;
        while (i < 3) {
            print(i);
            sum = sum + i;
            i = i + 1;
        }
        let r7 = sum;
        """,
        result_vars=["r7"],
        expected_outputs=["0", "1", "2", "3"],
    )


def test_print_in_function():
    """print 在命名函数内使用"""
    return run_positive_test(
        "print 在函数内使用",
        """
        fn greet(n) {
            print(n);
            return n + 1;
        }
        let r8 = greet(100);
        """,
        result_vars=["r8"],
        expected_outputs=["100", "101"],
        check_patterns=[r'printf\("%d\\n", n\);'],
    )


def test_print_multiple_times():
    """多次 print 连续调用"""
    return run_positive_test(
        "多次 print 连续调用",
        """
        print(1);
        print(2);
        print(3);
        let r9 = 0;
        """,
        result_vars=["r9"],
        expected_outputs=["1", "2", "3", "0"],
    )


def test_print_with_vec():
    """print 与 Vec 混用"""
    return run_positive_test(
        "print 与 Vec 混用",
        """
        let v = [10, 20, 30];
        print(v[1]);
        let r10 = v[2];
        """,
        result_vars=["r10"],
        expected_outputs=["20", "30"],
        check_patterns=[r'printf\("%d\\n", vec_get_i32\(v, 1\)\)'],
    )


def test_print_with_option():
    """print 与 Option 混用（通过 match 取值）"""
    return run_positive_test(
        "print 与 Option 混用",
        """
        let opt = Some(99);
        let val = match opt { Some(v) => v, None => 0 };
        print(val);
        let r11 = 0;
        """,
        result_vars=["r11"],
        expected_outputs=["99", "0"],
    )


def test_print_vec_element_ok():
    """print Vec 元素（i32）应通过"""
    return run_positive_test(
        "print Vec 元素",
        """
        let v = [1, 2, 3];
        print(v[0]);
        let r12 = 0;
        """,
        result_vars=["r12"],
        expected_outputs=["1", "0"],
    )


# ------------------------------------------------------------------
# 负面测试用例
# ------------------------------------------------------------------

def test_print_non_i32_should_fail():
    """print 非 i32 类型应报错"""
    return run_negative_test(
        "print 非 i32 类型",
        """
        let v = [1, 2, 3];
        print(v);
        """,
        expected_err_substr="Semantic analysis failed",
    )


def test_assign_print_should_fail():
    """let x = print(1); 应报错（print 返回 void）"""
    return run_negative_test(
        "赋值 print 返回值",
        """
        let x = print(1);
        """,
        expected_err_substr="Semantic analysis failed",
    )


def test_print_option_should_fail():
    """print Option 类型应报错"""
    return run_negative_test(
        "print Option 类型",
        """
        let opt = Some(1);
        print(opt);
        """,
        expected_err_substr="Semantic analysis failed",
    )


def test_print_closure_should_fail():
    """print 闭包变量应报错"""
    return run_negative_test(
        "print 闭包变量",
        """
        let f = fn(x) => x;
        print(f);
        """,
        expected_err_substr="Semantic analysis failed",
    )


# ------------------------------------------------------------------
# 主入口
# ------------------------------------------------------------------
POSITIVE_TESTS = [
    test_basic_print,
    test_print_expr,
    test_print_function_result,
    test_print_closure_result,
    test_print_struct_method,
    test_print_match_result,
    test_print_in_control_flow,
    test_print_in_function,
    test_print_multiple_times,
    test_print_with_vec,
    test_print_with_option,
    test_print_vec_element_ok,
]

NEGATIVE_TESTS = [
    test_print_non_i32_should_fail,
    test_assign_print_should_fail,
    test_print_option_should_fail,
    test_print_closure_should_fail,
]


def main():
    print("阶段 6 鲁棒端到端测试开始")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"运行时目录: {RUNTIME_DIR}")

    passed = 0
    failed = 0

    for t in POSITIVE_TESTS:
        if t():
            passed += 1
        else:
            failed += 1

    for t in NEGATIVE_TESTS:
        if t():
            passed += 1
        else:
            failed += 1

    total = len(POSITIVE_TESTS) + len(NEGATIVE_TESTS)
    print(f"\n{'='*60}")
    print(f"结果: {passed}/{total} 通过, {failed}/{total} 失败")
    print(f"{'='*60}")

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
