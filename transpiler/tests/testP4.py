
#!/usr/bin/env python3
"""
阶段 4 端到端测试
验证：函数返回函数（嵌套闭包）、命名函数返回闭包、闭包作为参数、多层调用链
"""

import sys
import os
import subprocess
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from transpiler.src.compiler import compile_rustlike_to_c


def run_test(name: str, source_code: str, expected_patterns: list = None) -> bool:
    """编译源码为 C，用 gcc 编译运行，检查是否成功。"""
    print(f"\\n{'='*50}")
    print(f"测试: {name}")
    print(f"{'='*50}")
    
    try:
        c_code = compile_rustlike_to_c(source_code)
        print("生成的 C 代码:")
        print(c_code[:2000] + "..." if len(c_code) > 2000 else c_code)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(c_code)
            c_file = f.name
        
        exe_file = c_file.replace('.c', '')
        runtime_dir = os.path.join(os.path.dirname(__file__), '..', 'runtime')
        
        result = subprocess.run(
            ['gcc', '-o', exe_file, c_file, '-I', runtime_dir],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"GCC 编译失败:\\n{result.stderr}")
            os.unlink(c_file)
            return False
        
        result = subprocess.run([exe_file], capture_output=True, text=True)
        
        os.unlink(c_file)
        if os.path.exists(exe_file):
            os.unlink(exe_file)
        
        if result.returncode != 0:
            print(f"运行失败 (exit {result.returncode}):\\n{result.stderr}")
            return False
        
        print(f"运行成功，stdout: {repr(result.stdout)}")
        
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


# ==================== P4 测试用例 ====================

def test_add_curried():
    """基础柯里化：let add = fn(a) => fn(b) => a + b; add(3)(4) == 7"""
    return run_test("柯里化 add(3)(4)", """
fn mymain() {
    let add = fn(a) => fn(b) => a + b;
    let result = add(3)(4);
}
""", expected_patterns=["7"])


def test_closure_capture_toplevel():
    """闭包捕获顶层变量：f(3)(4) == 10 (x=1, y=2)"""
    return run_test("闭包捕获顶层变量", """
fn mymain() {
    let x = 1;
    let y = 2;
    let f = fn(a) => fn(b) => x + y + a + b;
    let result = f(3)(4);
}
""", expected_patterns=["10"])


def test_triple_nested():
    """三层嵌套闭包：triple(1)(2)(3) == 6"""
    return run_test("三层嵌套闭包", """
fn mymain() {
    let triple = fn(a) => fn(b) => fn(c) => a + b + c;
    let result = triple(1)(2)(3);
}
""", expected_patterns=["6"])


def test_named_func_returns_closure():
    """命名函数返回闭包：make_adder(10)(5) == 15"""
    return run_test("命名函数返回闭包", """
fn make_adder(base) {
    return fn(x) => base + x;
}

fn mymain() {
    let add10 = make_adder(10);
    let result = add10(5);
}
""", expected_patterns=["15"])


def test_closure_as_param():
    """闭包作为参数传递：apply_twice(double, 3) == 12"""
    return run_test("闭包作为参数", """
fn apply_twice(f, x) {
    return f(f(x));
}

fn mymain() {
    let doubled = fn(n) => n * 2;
    let result = apply_twice(doubled, 3);
}
""", expected_patterns=["12"])


def test_named_func_returns_closure_multiple():
    """多个命名函数返回闭包"""
    return run_test("多个命名函数返回闭包", """
fn make_multiplier(factor) {
    return fn(x) => x * factor;
}

fn make_offset_adder(base, delta) {
    return fn(x) => base + delta + x;
}

fn mymain() {
    let triple_fn = make_multiplier(3);
    let result1 = triple_fn(7);
    
    let add_150 = make_offset_adder(100, 50);
    let result2 = add_150(7);
}
""", expected_patterns=["21 157"])


def test_closure_capture_param():
    """闭包捕获参数：外层 fn 的参数进入内层闭包 Env"""
    return run_test("闭包捕获参数", """
fn make_adder(base) {
    return fn(x) => base + x;
}

fn mymain() {
    let add5 = make_adder(5);
    let add100 = make_adder(100);
    let result1 = add5(3);
    let result2 = add100(3);
}
""", expected_patterns=["8 103"])


def test_mixed_closure_and_plain():
    """混合场景：闭包与普通函数共存"""
    return run_test("混合场景", """
fn plain_add(a, b) {
    return a + b;
}

fn make_adder(base) {
    return fn(x) => base + x;
}

fn apply_twice(f, x) {
    return f(f(x));
}

fn mymain() {
    let a = plain_add(2, 3);
    let add10 = make_adder(10);
    let b = add10(5);
    let doubled = fn(n) => n * 2;
    let c = apply_twice(doubled, 4);
}
""", expected_patterns=["5 15 16"])


def test_closure_in_closure_with_match():
    """闭包内使用 match（回归测试）"""
    return run_test("闭包内使用 match", """
fn mymain() {
    let opt = Some(10);
    let f = fn(x) => match opt {
        Some(v) => v + x,
        None => x
    };
    let result = f(5);
}
""", expected_patterns=["15"])


# ==================== 主入口 ====================

TESTS = [
    test_add_curried,
    test_closure_capture_toplevel,
    test_triple_nested,
    test_named_func_returns_closure,
    test_closure_as_param,
    test_named_func_returns_closure_multiple,
    test_closure_capture_param,
    test_mixed_closure_and_plain,
    test_closure_in_closure_with_match,
]


def main():
    print("阶段 4 端到端测试开始")
    
    passed = 0
    failed = 0
    
    for test in TESTS:
        if test():
            passed += 1
        else:
            failed += 1
    
    print(f"\\n{'='*50}")
    print(f"结果: {passed} 通过, {failed} 失败")
    print(f"{'='*50}")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())