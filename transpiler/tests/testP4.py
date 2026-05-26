#!/usr/bin/env python3
"""
阶段 4 鲁棒端到端测试
验证：函数返回函数、闭包捕获、闭包参数、多层调用链、内存安全
"""

import sys
import os
import re
import subprocess
import tempfile

# ------------------------------------------------------------------
# 路径设置
# ------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from transpiler.src.compiler import compile_rustlike_to_c

RUNTIME_DIR = os.path.join(PROJECT_ROOT, "runtime")

# ------------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------------
def _inject_printfs(c_code: str, var_names: list[str]) -> str:
    """在 main() 的 return 0; 之前插入 printf，打印指定变量"""
    if not var_names:
        return c_code
    prints = "\n".join(f'    printf("%d\\n", {v});' for v in var_names)
    new_code = re.sub(
        r'(\s+return 0;)',
        lambda m: f"\n{prints}{m.group(1)}",
        c_code,
        count=1
    )
    return new_code


def _gcc_compile(c_file: str, exe_file: str, use_asan: bool = True) -> tuple[bool, str, bool]:
    """编译 C 文件，优先尝试 ASan，失败则降级"""
    base_cmd = ['gcc', '-g', '-O0', '-fno-omit-frame-pointer', '-o', exe_file, c_file, '-I', RUNTIME_DIR]
    if use_asan:
        result = subprocess.run(base_cmd + ['-fsanitize=address'], capture_output=True, text=True)
        if result.returncode == 0:
            return True, "", True
    result = subprocess.run(base_cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stderr, False


def _run_exe(exe_file: str, timeout_sec: int = 5) -> tuple[int, str, str, bool]:
    """运行可执行文件，带超时保护"""
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
    """
    正面测试：编译 → 注入 printf → 运行 → 验证 stdout 数值 + 内存安全
    """
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

    # 使用 UUID 避免临时文件冲突
    import uuid
    tmp_dir = tempfile.gettempdir()
    unique = str(uuid.uuid4())[:8]
    c_file = os.path.join(tmp_dir, f"test_{unique}.c")
    exe_file = os.path.join(tmp_dir, f"test_{unique}_exe")
    with open(c_file, 'w', encoding='utf-8') as f:
        f.write(c_code)

    ok, err, used_asan = _gcc_compile(c_file, exe_file, use_asan=True)
    if not ok:
        print(f"  [FAIL] GCC 编译失败:\n{err}")
        os.unlink(c_file)
        return False

    exit_code, stdout, stderr, timed_out = _run_exe(exe_file, timeout_sec=5)

    os.unlink(c_file)
    if os.path.exists(exe_file):
        os.unlink(exe_file)

    if timed_out:
        print(f"  [FAIL] 程序超时/卡死 (ASan={used_asan})")
        return False

    if "ERROR: AddressSanitizer" in stderr:
        print(f"  [FAIL] AddressSanitizer 检测到内存错误:\n{stderr}")
        return False

    if "ERROR:" in stderr and "Sanitizer" in stderr:
        print(f"  [FAIL] Sanitizer 报错:\n{stderr}")
        return False

    if exit_code != 0:
        print(f"  [FAIL] 运行崩溃 (exit {exit_code}, ASan={used_asan}):\n{stderr}")
        return False

    actual_lines = [ln.strip() for ln in stdout.strip().splitlines() if ln.strip() != ""]
    if actual_lines != expected_outputs:
        print(f"  [FAIL] 输出不匹配")
        print(f"         期望: {expected_outputs}")
        print(f"         实际: {actual_lines}")
        return False

    print(f"  [PASS] 输出正确: {actual_lines} | ASan={used_asan}")
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
        # 检查外层异常消息
        if expected_err_substr in err_msg:
            print(f"  [PASS] 正确拦截: {err_msg[:120]}...")
            return True
        # 检查原始异常（__cause__）
        cause = getattr(e, '__cause__', None)
        if cause:
            cause_msg = str(cause)
            if expected_err_substr in cause_msg:
                print(f"  [PASS] 正确拦截: {cause_msg[:120]}...")
                return True
        # 检查异常参数（args）
        for arg in getattr(e, 'args', []):
            if isinstance(arg, str) and expected_err_substr in arg:
                print(f"  [PASS] 正确拦截: {arg[:120]}...")
                return True
        
        print(f"  [FAIL] 报错内容不匹配")
        print(f"         期望包含: {expected_err_substr}")
        print(f"         实际: {err_msg[:300]}")
        return False


# ------------------------------------------------------------------
# 正面测试用例（仅 i32 捕获，符合阶段 3 约束）
# ------------------------------------------------------------------
def test_curried_add():
    return run_positive_test(
        "柯里化 add(3)(4)",
        """
        let add = fn(a) => fn(b) => a + b;
        let r1 = add(3)(4);
        """,
        result_vars=["r1"],
        expected_outputs=["7"],
        check_patterns=[r"Closure_i32_i32"],
    )


def test_capture_toplevel():
    return run_positive_test(
        "闭包捕获顶层变量",
        """
        let x1 = 1;
        let y1 = 2;
        let f1 = fn(a) => fn(b) => x1 + y1 + a + b;
        let r2 = f1(3)(4);
        """,
        result_vars=["r2"],
        expected_outputs=["10"],
    )


def test_triple_nested():
    return run_positive_test(
        "三层嵌套闭包 triple(1)(2)(3)",
        """
        let triple = fn(a) => fn(b) => fn(c) => a + b + c;
        let r3 = triple(1)(2)(3);
        """,
        result_vars=["r3"],
        expected_outputs=["6"],
        check_patterns=[r"Closure_Closure_i32_i32__i32"],
    )


def test_named_func_returns_closure():
    return run_positive_test(
        "命名函数返回闭包 make_adder(10)(5)",
        """
        fn make_adder1(base) {
            return fn(x) => base + x;
        }
        let add10 = make_adder1(10);
        let r4 = add10(5);
        """,
        result_vars=["r4"],
        expected_outputs=["15"],
    )


def test_closure_as_param():
    return run_positive_test(
        "闭包作为参数 apply_twice(doubled, 3)",
        """
        fn apply_twice(f, x) {
            return f(f(x));
        }
        let doubled = fn(n) => n * 2;
        let r5 = apply_twice(doubled, 3);
        """,
        result_vars=["r5"],
        expected_outputs=["12"],
    )


def test_multiple_named_closures():
    return run_positive_test(
        "多个命名函数返回闭包",
        """
        fn make_multiplier(factor) {
            return fn(x) => x * factor;
        }
        fn make_offset_adder(base, delta) {
            return fn(x) => base + delta + x;
        }
        let triple_fn = make_multiplier(3);
        let r6 = triple_fn(7);
        let add_150 = make_offset_adder(100, 50);
        let r7 = add_150(7);
        """,
        result_vars=["r6", "r7"],
        expected_outputs=["21", "157"],
    )


def test_closure_capture_param():
    return run_positive_test(
        "闭包捕获参数（外层参数进入内层 Env）",
        """
        fn make_adder2(base) {
            return fn(x) => base + x;
        }
        let add5 = make_adder2(5);
        let add100 = make_adder2(100);
        let r8 = add5(3);
        let r9 = add100(3);
        """,
        result_vars=["r8", "r9"],
        expected_outputs=["8", "103"],
    )


def test_mixed_closure_and_plain():
    return run_positive_test(
        "混合场景：普通函数 + 闭包 + 高阶",
        """
        fn plain_add(a, b) {
            return a + b;
        }
        fn make_adder3(base) {
            return fn(x) => base + x;
        }
        fn apply_twice2(f, x) {
            return f(f(x));
        }
        let a1 = plain_add(2, 3);
        let add10b = make_adder3(10);
        let b1 = add10b(5);
        let doubled2 = fn(n) => n * 2;
        let c1 = apply_twice2(doubled2, 4);
        """,
        result_vars=["a1", "b1", "c1"],
        expected_outputs=["5", "15", "16"],
    )


def test_for_closure():
    return run_positive_test(
        "for 循环内闭包",
        """
        let arr1 = [1, 2, 3];
        let sum1 = 0;
        for j in arr1 {
            let f2 = fn() => j;
            let r10 = f2();
            sum1 = sum1 + r10;
        }
        let r11 = sum1;
        """,
        result_vars=["r11"],
        expected_outputs=["6"],
    )


def test_while_closure():
    return run_positive_test(
        "while 循环内闭包",
        """
        let i1 = 0;
        let wsum = 0;
        while (i1 < 3) {
            let f3 = fn() => i1;
            let r12 = f3();
            wsum = wsum + r12;
            i1 = i1 + 1;
        }
        let r13 = wsum;
        """,
        result_vars=["r13"],
        expected_outputs=["3"],
    )


def test_if_else_closure():
    return run_positive_test(
        "if-else 分支内闭包",
        """
        let x2 = 10;
        let r14 = 0;
        if (x2 > 5) {
            let f4 = fn(a) => x2 + a;
            r14 = f4(1);
        } else {
            let g1 = fn(b) => x2 * b;
            r14 = g1(2);
        }
        """,
        result_vars=["r14"],
        expected_outputs=["11"],
    )


def test_nested_if_closure():
    return run_positive_test(
        "嵌套 if 内闭包",
        """
        let flag = 1;
        let r15 = 0;
        if (flag > 0) {
            if (flag > 0) {
                let f5 = fn() => flag;
                r15 = f5();
            }
        }
        """,
        result_vars=["r15"],
        expected_outputs=["1"],
    )


def test_no_arg_closure():
    return run_positive_test(
        "无参数闭包",
        """
        let get42 = fn() => 42;
        let r16 = get42();
        """,
        result_vars=["r16"],
        expected_outputs=["42"],
    )


def test_vec_with_closure():
    return run_positive_test(
        "Vec 与闭包组合（仅迭代，不捕获 Vec）",
        """
        let arr2 = [1, 2, 3];
        let sum2 = 0;
        for j in arr2 {
            let f7 = fn() => j;
            sum2 = sum2 + f7();
        }
        let r18 = sum2;
        """,
        result_vars=["r18"],
        expected_outputs=["6"],
    )


# ------------------------------------------------------------------
# 负面测试用例
# ------------------------------------------------------------------
def test_capture_vec_should_fail():
    return run_negative_test(
        "捕获 Vec<i32> 应报错",
        """
        let arr = [1, 2, 3];
        let f = fn() => arr;
        let r = f();
        """,
        expected_err_substr="闭包暂只支持捕获 i32",
    )


def test_undefined_var_in_closure():
    return run_negative_test(
        "闭包内使用未声明变量应报错",
        """
        let f = fn(x) => y + x;
        let r = f(1);
        """,
        expected_err_substr="未声明",
    )


def test_type_mismatch_hof():
    return run_negative_test(
        "高阶函数参数类型不匹配应报错",
        """
        fn apply_twice(f, x) {
            return f(f(x));
        }
        let result = apply_twice(10, 3);
        """,
        expected_err_substr="callee 不是函数类型",
    )


def test_closure_return_type_mismatch():
    return run_negative_test(
        "命名函数返回类型不一致应报错",
        """
        fn foo() {
            return 1;
        }
        fn bar() {
            return fn(x) => x;
        }
        """,
        expected_err_substr="unknown",
    )


# ------------------------------------------------------------------
# 主入口
# ------------------------------------------------------------------
POSITIVE_TESTS = [
    test_curried_add,
    test_capture_toplevel,
    test_triple_nested,
    test_named_func_returns_closure,
    test_closure_as_param,
    test_multiple_named_closures,
    test_closure_capture_param,
    test_mixed_closure_and_plain,
    test_for_closure,
    test_while_closure,
    test_if_else_closure,
    test_nested_if_closure,
    test_no_arg_closure,
    test_vec_with_closure,
]

NEGATIVE_TESTS = [
    test_capture_vec_should_fail,
    test_undefined_var_in_closure,
    test_type_mismatch_hof,
    test_closure_return_type_mismatch,
]


def main():
    print("阶段 4 鲁棒端到端测试开始")
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