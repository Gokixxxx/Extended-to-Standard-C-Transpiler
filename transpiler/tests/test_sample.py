#!/usr/bin/env python3
"""
测试用例 - 带文件输出
每个样例输出：输入源码、生成的 C 代码、测试结果
"""

import sys
import os
import re
import subprocess
import tempfile
import uuid

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from transpiler.src.compiler import compile_rustlike_to_c

RUNTIME_DIR = os.path.join(PROJECT_ROOT, "runtime")

# 输出目录
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "test_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 全局计数器
test_counter = 0


# ------------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------------
def _inject_printfs(c_code: str, var_names: list) -> str:
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


def _gcc_compile(c_file: str, exe_file: str):
    cmd = ['gcc', '-g', '-O0', '-o', exe_file, c_file, '-I', RUNTIME_DIR]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stderr


def _run_exe(exe_file: str, timeout_sec: int = 5):
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


def _sanitize_filename(name: str) -> str:
    """将测试名转为合法文件名"""
    return re.sub(r'[^\w\-]', '_', name).strip('_')


def run_test(
    name: str,
    source_code: str,
    result_vars: list = None,
    expected_outputs: list = None,
    check_patterns: list = None,
) -> bool:
    """
    统一测试入口，同时输出到文件。
    """
    global test_counter
    test_counter += 1

    print(f"\n{'='*60}")
    print(f"[TEST {test_counter}] {name}")
    print(f"{'='*60}")

    # 准备输出文件
    safe_name = _sanitize_filename(name)
    out_file = os.path.join(OUTPUT_DIR, f"{test_counter:03d}_{safe_name}.txt")

    lines = []
    lines.append("=" * 70)
    lines.append(f"测试 #{test_counter}: {name}")
    lines.append("=" * 70)
    lines.append("")
    lines.append("-" * 70)
    lines.append("【输入源码】")
    lines.append("-" * 70)
    lines.append(source_code.strip())
    lines.append("")

    c_code = None
    compile_ok = False
    run_ok = False
    output_match = None
    actual_lines = None
    error_msg = None

    # 1. 转译
    try:
        c_code = compile_rustlike_to_c(source_code)
    except Exception as e:
        error_msg = f"转译失败: {e}"
        print(f"  [FAIL] {error_msg}")
        import traceback
        traceback.print_exc()

    if c_code is not None:
        lines.append("-" * 70)
        lines.append("【生成的 C 代码】")
        lines.append("-" * 70)
        lines.append(c_code)
        lines.append("")

        # 2. 模式检查
        if check_patterns:
            pattern_ok = True
            for pat in check_patterns:
                if not re.search(pat, c_code):
                    pattern_ok = False
                    error_msg = f"生成代码未匹配模式: {pat}"
                    break
            if not pattern_ok:
                print(f"  [FAIL] {error_msg}")
            else:
                print(f"  [OK] 代码模式检查通过")

        if result_vars:
            c_code = _inject_printfs(c_code, result_vars)

        # 3. 编译
        tmp_dir = tempfile.gettempdir()
        unique = str(uuid.uuid4())[:8]
        c_file = os.path.join(tmp_dir, f"test_{unique}.c")
        exe_file = os.path.join(tmp_dir, f"test_{unique}_exe")
        with open(c_file, 'w', encoding='utf-8') as f:
            f.write(c_code)

        ok, err = _gcc_compile(c_file, exe_file)
        if not ok:
            error_msg = f"GCC 编译失败:\n{err}"
            print(f"  [FAIL] {error_msg}")
        else:
            compile_ok = True
            print(f"  [OK] GCC 编译通过")

            # 4. 运行
            exit_code, stdout, stderr, timed_out = _run_exe(exe_file, timeout_sec=5)

            os.unlink(c_file)
            if os.path.exists(exe_file):
                os.unlink(exe_file)

            if timed_out:
                error_msg = "程序超时/卡死"
                print(f"  [FAIL] {error_msg}")
            elif exit_code != 0:
                error_msg = f"运行崩溃 (exit {exit_code}):\n{stderr}"
                print(f"  [FAIL] {error_msg}")
            else:
                run_ok = True
                print(f"  [OK] 程序运行成功")

                if result_vars is not None and expected_outputs is not None:
                    actual_lines = [ln.strip() for ln in stdout.strip().splitlines() if ln.strip() != ""]
                    if actual_lines != expected_outputs:
                        error_msg = f"输出不匹配: 期望 {expected_outputs}, 实际 {actual_lines}"
                        print(f"  [FAIL] {error_msg}")
                    else:
                        output_match = True
                        print(f"  [PASS] 输出正确: {actual_lines}")
                else:
                    output_match = True
                    print(f"  [PASS] 编译运行通过 (无输出验证)")
        # 清理
        if os.path.exists(c_file):
            os.unlink(c_file)
        if os.path.exists(exe_file):
            os.unlink(exe_file)

    # 写入结果到文件
    lines.append("-" * 70)
    lines.append("【测试结果】")
    lines.append("-" * 70)
    if error_msg:
        lines.append(f"状态: FAIL")
        lines.append(f"错误: {error_msg}")
    else:
        lines.append(f"状态: PASS")
        lines.append(f"编译: {'通过' if compile_ok else 'N/A'}")
        lines.append(f"运行: {'通过' if run_ok else 'N/A'}")
        if actual_lines is not None:
            lines.append(f"期望输出: {expected_outputs}")
            lines.append(f"实际输出: {actual_lines}")
    lines.append("")
    lines.append("=" * 70)

    with open(out_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"  -> 输出文件: {out_file}")

    return error_msg is None


# ==================================================================
# 阶段 0：基础语法、Option、Vec、match、控制流、索引赋值
# ==================================================================

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


# ==================================================================
# 阶段 4：函数返回函数、闭包捕获、闭包参数、多层调用链
# ==================================================================

def test_curried_add():
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
        "无参数闭包",
        """
        let get42 = fn() => 42;
        let r16 = get42();
        """,
        result_vars=["r16"],
        expected_outputs=["42"],
    )


def test_vec_with_closure():
    return run_test(
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


def test_let_move():
    return run_test(
        "let 转移：闭包变量复制后原变量置空",
        """
        let a = 10;
        let f = fn(x) => a + x;
        let g = f;
        let r1 = g(5);
        """,
        result_vars=["r1"],
        expected_outputs=["15"],
    )


def test_assign_move():
    return run_test(
        "assign 转移：闭包变量赋值后原变量置空",
        """
        let b = 1;
        let f1 = fn(x) => b + x;
        let f2 = fn(x) => b * 2 + x;
        f2 = f1;
        let r2 = f2(10);
        """,
        result_vars=["r2"],
        expected_outputs=["11"],
    )


def test_return_move():
    return run_test(
        "return 转移：命名函数返回闭包",
        """
        fn make_adder(x) {
            let adder = fn(y) => x + y;
            return adder;
        }
        let add5 = make_adder(5);
        let r3 = add5(3);
        """,
        result_vars=["r3"],
        expected_outputs=["8"],
    )


def test_uncaptured_fn_copyable():
    return run_test(
        "无捕获函数可复制：多次赋值不触发 move",
        """
        let doubled = fn(x) => x * 2;
        let d1 = doubled;
        let d2 = doubled;
        let r4 = d1(3);
        let r5 = d2(4);
        """,
        result_vars=["r4", "r5"],
        expected_outputs=["6", "8"],
    )


def test_closure_as_param_move():
    return run_test(
        "闭包作为参数传递（自动包装）",
        """
        fn apply_twice(f, x) {
            return f(f(x));
        }
        let add3 = fn(x) => x + 3;
        let r6 = apply_twice(add3, 5);
        """,
        result_vars=["r6"],
        expected_outputs=["11"],
    )


# ==================================================================
# 阶段 5：Struct 定义、Impl 方法、字段访问、方法调用
# ==================================================================

def test_basic_struct_impl():
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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


def test_chained_method_calls():
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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


# ==================================================================
# 阶段 6：print 输出支持
# ==================================================================

def test_basic_print():
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
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
    return run_test(
        "print Vec 元素",
        """
        let v = [1, 2, 3];
        print(v[0]);
        let r12 = 0;
        """,
        result_vars=["r12"],
        expected_outputs=["1", "0"],
    )


# ==================================================================
# 测试套件入口
# ==================================================================

ALL_TESTS = [
    # 阶段 0
    test_basic_arithmetic,
    test_if_else,
    test_while,
    test_for_in,
    test_option_some_none,
    test_match_basic,
    test_match_complex,
    test_vec_all_ops,
    test_find_function,
    # 阶段 4
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
    test_let_move,
    test_assign_move,
    test_return_move,
    test_uncaptured_fn_copyable,
    test_closure_as_param_move,
    # 阶段 5
    test_basic_struct_impl,
    test_multi_field_access,
    test_method_with_extra_params,
    test_multiple_methods,
    test_struct_as_value,
    test_struct_in_vec,
    test_struct_with_option,
    test_chained_method_calls,
    test_self_field_arithmetic,
    test_struct_passed_to_function,
    test_nested_struct_usage,
    # 阶段 6
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


def main():
    print("=" * 60)
    print("Test Sample")
    print(f"Count: {len(ALL_TESTS)}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)

    passed = 0
    failed = 0

    for test in ALL_TESTS:
        if test():
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Result: {passed}/{len(ALL_TESTS)} passed, {failed}/{len(ALL_TESTS)} failed.")
    print(f"输出文件保存在: {OUTPUT_DIR}")
    print(f"{'='*60}")

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
