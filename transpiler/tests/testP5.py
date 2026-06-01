#!/usr/bin/env python3
"""
阶段 5 鲁棒端到端测试
验证：Struct 定义、Impl 方法、字段访问、方法调用、与 Vec/Option/闭包混用
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
# 工具函数（与 P4 保持一致）
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
    """编译 C 文件"""
    cmd = ['gcc', '-g', '-O0', '-o', exe_file, c_file, '-I', RUNTIME_DIR]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stderr


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
    """正面测试：编译 → 注入 printf → 运行 → 验证 stdout 数值"""
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
    """负面测试：期望在语义分析阶段报错"""
    print(f"\n{'='*60}")
    print(f"[-] 负面测试: {name}")
    print(f"{'='*60}")

    try:
        compile_rustlike_to_c(source_code)
        print(f"  [FAIL] 应当报错，但编译成功")
        return False
    except Exception as e:
        err_msg = str(e)
        if expected_err_substr in err_msg:
            print(f"  [PASS] 正确拦截: {err_msg[:120]}...")
            return True
        cause = getattr(e, '__cause__', None)
        if cause:
            cause_msg = str(cause)
            if expected_err_substr in cause_msg:
                print(f"  [PASS] 正确拦截: {cause_msg[:120]}...")
                return True
        for arg in getattr(e, 'args', []):
            if isinstance(arg, str) and expected_err_substr in arg:
                print(f"  [PASS] 正确拦截: {arg[:120]}...")
                return True
        
        print(f"  [FAIL] 报错内容不匹配")
        print(f"         期望包含: {expected_err_substr}")
        print(f"         实际: {err_msg[:300]}")
        return False


# ------------------------------------------------------------------
# 正面测试用例
# ------------------------------------------------------------------

def test_basic_struct_impl():
    """基础 struct + impl + 方法调用"""
    return run_positive_test(
        "基础 struct 与 impl",
        """
        struct Rectangle {
            width: i32,
            height: i32
        }

        impl Rectangle {
            fn area(&self) {
                return self.width * self.height;
            }
        }

        let rect = new Rectangle { width: 30, height: 50 };
        let r1 = rect.area();
        """,
        result_vars=["r1"],
        expected_outputs=["1500"],
        check_patterns=[r"typedef struct\s*\{[^}]*int width;[^}]*int height;\s*\}\s*Rectangle;"],
    )


def test_multi_field_access():
    """直接字段访问（值类型和指针类型）"""
    return run_positive_test(
        "字段直接访问",
        """
        struct Point {
            x: i32,
            y: i32
        }

        let p = new Point { x: 10, y: 20 };
        let r2 = p.x + p.y;
        """,
        result_vars=["r2"],
        expected_outputs=["30"],
    )


def test_method_with_extra_params():
    """方法带额外参数（&self + 其他参数）"""
    return run_positive_test(
        "方法带额外参数",
        """
        struct Rectangle {
            width: i32,
            height: i32
        }

        impl Rectangle {
            fn scale(&self, factor) {
                return self.width * self.height * factor;
            }
        }

        let rect = new Rectangle { width: 3, height: 4 };
        let r3 = rect.scale(5);
        """,
        result_vars=["r3"],
        expected_outputs=["60"],
    )


def test_multiple_methods():
    """同一 struct 多个方法"""
    return run_positive_test(
        "同一 struct 多方法",
        """
        struct Counter {
            value: i32
        }

        impl Counter {
            fn get(&self) {
                return self.value;
            }

            fn add(&self, delta) {
                return self.value + delta;
            }
        }

        let c = new Counter { value: 100 };
        let r4 = c.get();
        let r5 = c.add(7);
        """,
        result_vars=["r4", "r5"],
        expected_outputs=["100", "107"],
    )


def test_struct_as_value():
    """struct 按值传递（赋值给新变量）"""
    return run_positive_test(
        "struct 按值传递",
        """
        struct Point {
            x: i32,
            y: i32
        }

        let p1 = new Point { x: 5, y: 6 };
        let p2 = p1;
        let r6 = p2.x + p2.y;
        """,
        result_vars=["r6"],
        expected_outputs=["11"],
    )


def test_struct_in_vec():
    """Vec 存储 struct 方法结果（或 struct 实例）"""
    return run_positive_test(
        "Vec 与 struct 混用",
        """
        struct Rect {
            w: i32,
            h: i32
        }

        impl Rect {
            fn area(&self) {
                return self.w * self.h;
            }
        }

        let v = [1, 2, 3];
        let rect = new Rect { w: 2, h: 3 };
        let r7 = rect.area() + v[1];
        """,
        result_vars=["r7"],
        expected_outputs=["8"],
    )


def test_struct_with_option():
    """Struct 与 Option 组合"""
    return run_positive_test(
        "struct 与 Option 混用",
        """
        struct Box {
            width: i32,
            height: i32
        }

        impl Box {
            fn max_side(&self) {
                if (self.width > self.height) {
                    return Some(self.width);
                } else {
                    return Some(self.height);
                }
            }
        }

        let b = new Box { width: 8, height: 5 };
        let opt = b.max_side();
        let r8 = match opt {
            Some(v) => v,
            None => 0
        };
        """,
        result_vars=["r8"],
        expected_outputs=["8"],
    )


def test_struct_with_closure():
    """Struct 方法内使用闭包（或闭包捕获 struct 字段）"""
    return run_positive_test(
        "struct 与闭包混用",
        """
        struct Config {
            base: i32
        }

        impl Config {
            fn make_adder(&self) {
                return fn(x) => self.base + x;
            }
        }

        let cfg = new Config { base: 100 };
        let adder = cfg.make_adder();
        let r9 = adder(7);
        """,
        result_vars=["r9"],
        expected_outputs=["107"],
        check_patterns=[r"Config_make_adder"],
    )


def test_chained_method_calls():
    """链式/嵌套方法调用（方法返回 i32 直接参与运算）"""
    return run_positive_test(
        "方法结果参与运算",
        """
        struct Num {
            val: i32
        }

        impl Num {
            fn double(&self) {
                return self.val * 2;
            }

            fn triple(&self) {
                return self.val * 3;
            }
        }

        let n = new Num { val: 5 };
        let r10 = n.double() + n.triple();
        """,
        result_vars=["r10"],
        expected_outputs=["25"],
    )


def test_self_field_arithmetic():
    """方法内 self 字段参与复杂运算"""
    return run_positive_test(
        "self 字段复杂运算",
        """
        struct Math {
            a: i32,
            b: i32
        }

        impl Math {
            fn compute(&self) {
                return self.a * self.a + self.b * self.b;
            }
        }

        let m = new Math { a: 3, b: 4 };
        let r11 = m.compute();
        """,
        result_vars=["r11"],
        expected_outputs=["25"],
    )


def test_struct_passed_to_function():
    """struct 实例传给普通函数使用（通过方法调用间接验证）"""
    return run_positive_test(
        "struct 与普通函数协作",
        """
        struct Item {
            price: i32,
            qty: i32
        }

        impl Item {
            fn total(&self) {
                return self.price * self.qty;
            }
        }

        fn calc(item) {
            return item.total();
        }

        let i = new Item { price: 7, qty: 6 };
        let r12 = calc(i);
        """,
        result_vars=["r12"],
        expected_outputs=["42"],
    )


def test_nested_struct_usage():
    """struct 在 if/for 控制流中使用"""
    return run_positive_test(
        "struct 在控制流中使用",
        """
        struct Score {
            val: i32
        }

        impl Score {
            fn is_pass(&self) {
                if (self.val >= 60) {
                    return 1;
                } else {
                    return 0;
                }
            }
        }

        let s1 = new Score { val: 80 };
        let s2 = new Score { val: 50 };
        let r13 = s1.is_pass();
        let r14 = s2.is_pass();
        """,
        result_vars=["r13", "r14"],
        expected_outputs=["1", "0"],
    )


# ------------------------------------------------------------------
# 负面测试用例
# ------------------------------------------------------------------

def test_undefined_struct():
    """使用未定义的 struct 类型"""
    return run_negative_test(
        "未定义 struct 类型",
        """
        let p = new Point { x: 1, y: 2 };
        """,
        expected_err_substr="未定义的 struct 类型",
    )


def test_missing_field():
    """初始化缺少字段"""
    return run_negative_test(
        "初始化缺少字段",
        """
        struct Point {
            x: i32,
            y: i32
        }

        let p = new Point { x: 1 };
        """,
        expected_err_substr="缺少字段",
    )


def test_extra_field():
    """初始化包含 struct 不存在的字段"""
    return run_negative_test(
        "初始化多余字段",
        """
        struct Point {
            x: i32,
            y: i32
        }

        let p = new Point { x: 1, y: 2, z: 3 };
        """,
        expected_err_substr="没有字段",
    )


def test_duplicate_field():
    """初始化字段重复"""
    return run_negative_test(
        "初始化字段重复",
        """
        struct Point {
            x: i32,
            y: i32
        }

        let p = new Point { x: 1, x: 2, y: 3 };
        """,
        expected_err_substr="重复",
    )


def test_field_type_mismatch():
    """字段类型不匹配"""
    return run_negative_test(
        "字段类型不匹配",
        """
        struct Point {
            x: i32,
            y: i32
        }

        let p = new Point { x: 1, y: [1, 2] };
        """,
        expected_err_substr="期望 i32",
    )


def test_undefined_field_access():
    """访问不存在的字段"""
    return run_negative_test(
        "访问不存在字段",
        """
        struct Point {
            x: i32,
            y: i32
        }

        let p = new Point { x: 1, y: 2 };
        let r = p.z;
        """,
        expected_err_substr="没有字段",
    )


def test_impl_undefined_struct():
    """impl 未定义的 struct"""
    return run_negative_test(
        "impl 未定义 struct",
        """
        impl Circle {
            fn area(&self) {
                return 0;
            }
        }
        """,
        expected_err_substr="impl 目标 struct",
    )


def test_duplicate_method():
    """同一 impl 块内方法重复定义"""
    return run_negative_test(
        "方法重复定义",
        """
        struct S {
            v: i32
        }

        impl S {
            fn get(&self) {
                return self.v;
            }

            fn get(&self) {
                return self.v;
            }
        }
        """,
        expected_err_substr="重复定义",
    )


def test_method_arg_mismatch():
    """方法调用参数数量不匹配"""
    return run_negative_test(
        "方法参数数量不匹配",
        """
        struct Rect {
            w: i32,
            h: i32
        }

        impl Rect {
            fn scale(&self, factor) {
                return self.w * factor;
            }
        }

        let r = new Rect { w: 2, h: 3 };
        let x = r.scale();
        """,
        expected_err_substr="期望",
    )


def test_field_access_on_non_struct():
    """对非 struct 类型进行字段访问"""
    return run_negative_test(
        "非 struct 字段访问",
        """
        let v = [1, 2, 3];
        let x = v.data;
        """,
        expected_err_substr="字段访问要求 struct 类型",
    )


# ------------------------------------------------------------------
# 主入口
# ------------------------------------------------------------------
POSITIVE_TESTS = [
    test_basic_struct_impl,
    test_multi_field_access,
    test_method_with_extra_params,
    test_multiple_methods,
    test_struct_as_value,
    test_struct_in_vec,
    test_struct_with_option,
    test_struct_with_closure,
    test_chained_method_calls,
    test_self_field_arithmetic,
    test_struct_passed_to_function,
    test_nested_struct_usage,
]

NEGATIVE_TESTS = [
    test_undefined_struct,
    test_missing_field,
    test_extra_field,
    test_duplicate_field,
    test_field_type_mismatch,
    test_undefined_field_access,
    test_impl_undefined_struct,
    test_duplicate_method,
    test_method_arg_mismatch,
    test_field_access_on_non_struct,
]


def main():
    print("阶段 5 鲁棒端到端测试开始")
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