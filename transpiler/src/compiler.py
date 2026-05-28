"""
主编译器入口
"""

from .lexer import RustLikeLexer
from .parser import RustLikeParser
from .semantic import SemanticAnalyzer
from .codegen import CCodeGenerator


class Compiler:
    def __init__(self):
        self.lexer = RustLikeLexer()
        self.parser = RustLikeParser()
        self.analyzer = SemanticAnalyzer()
        self.codegen = CCodeGenerator()
    
    def compile(self, source_code: str) -> str:
        try:
            # lexical analysis
            tokens = self.lexer.tokenize(source_code)
            
            # parse
            ast = self.parser.parse(tokens)
            
            # semantic analysis
            if not self.analyzer.analyze(ast):
                self.analyzer.print_errors()
                raise RuntimeError("Semantic analysis failed")
            
            # generate code
            c_code = self.codegen.generate(
                ast,
                func_signatures=self.analyzer.func_table,
                fn_expr_captures=self.analyzer.fn_expr_captures   # 3.1 新增
            )
            return c_code
            
        except Exception as e:
            raise RuntimeError(f"Compilation failed: {str(e)}")


def test_compiler():
    # 测试用例1
    print("测试 1 - 简单捕获:")
    source1 = """
    let outer = 10;
    let f = fn(x) => outer + x;
    let r = f(5);
    """
    compiler1 = Compiler()
    try:
        c_code1 = compiler1.compile(source1)
        print(c_code1)
    except Exception as e:
        print(f"错误: {e}")
    print()
    
    # 测试用例2
    print("测试 2 - 嵌套闭包 add(3)(4):")
    source2 = """
    let add = fn(a) => fn(b) => a + b;
    let result = add(3)(4);
    """
    compiler2 = Compiler()
    try:
        c_code2 = compiler2.compile(source2)
        print(c_code2)
    except Exception as e:
        print(f"错误: {e}")
    print()
    
    # 测试用例3
    print("测试 3 - 回归 - 无捕获函数仍正常工作:")
    source3 = """
    let x = Some(5);
    let y = match x {
        Some(v) => v + 1,
        None => 0
    };
    """
    compiler3 = Compiler()
    try:
        c_code3 = compiler3.compile(source3)
        print(c_code3)
    except Exception as e:
        print(f"错误: {e}")
    print()

    # 测试用例4
    print("测试 4 - 闭包作为参数传递")
    source4 = """
    fn apply(f, x) {
        return f(x);
    }
    let add5 = fn(y) => 5 + y;
    let result = apply(add5, 10);
    """
    compiler4 = Compiler()
    try:
        c_code4 = compiler4.compile(source4)
        print(c_code4)
    except Exception as e:
        print(f"错误: {e}")
    print()

    # 测试用例5
    print("测试 5 - 多层嵌套捕获")
    source5 = """
    let x = 1;
    let y = 2;
    let f = fn(a) => fn(b) => x + y + a + b;
    let result = f(3)(4);
    """
    compiler5 = Compiler()
    try:
        c_code5 = compiler5.compile(source5)
        print(c_code5)
    except Exception as e:
        print(f"错误: {e}")
    print()

    # 测试用例6
    print("测试 6 - 闭包内使用 match")
    source6 = """
    let opt = Some(10);
    let f = fn(x) => match opt {
        Some(v) => v + x,
        None => x
    };
    let result = f(5);
    """
    compiler6 = Compiler()
    try:
        c_code6 = compiler6.compile(source6)
        print(c_code6)
    except Exception as e:
        print(f"错误: {e}")
    print()

    # 测试 7：let 转移
    print("测试 7 - let 转移:")
    source7 = """
    let a = 10;
    let f = fn(x) => a + x;
    let g = f;
    let r = g(5);
    """
    # 期望：f.env = NULL; free(f.env) 实际为 free(NULL)，安全
    # g(5) 正常调用
    compiler7 = Compiler()
    try:
        c_code7 = compiler7.compile(source7)
        print(c_code7)
    except Exception as e:
        print(f"错误: {e}")
    print()
    
    # 测试 8：return 转移
    print("测试 8 - return 转移:")
    source8 = """
    fn make_adder(x) {
        let f = fn(y) => x + y;
        return f;
    }
    let add5 = make_adder(5);
    let r = add5(3);
    """
    compiler8 = Compiler()
    try:
        c_code8 = compiler8.compile(source8)
        print(c_code8)
    except Exception as e:
        print(f"错误: {e}")
    print()
    
    # 测试 9：assign 转移
    print("测试 9 - assign 转移:")
    source9 = """
    let a = 1;
    let f = fn(x) => a + x;
    let g = fn(x) => a + a + x;
    g = f;
    let r = g(10);
    """
    compiler9= Compiler()
    try:
        c_code9 = compiler9.compile(source9)
        print(c_code9)
    except Exception as e:
        print(f"错误: {e}")
    print()
    
    # 测试 10：use-after-move 应报错
    print("测试 10 - use-after-move 语义报错:")
    sourceX = """
    let a = 1;
    let f = fn(x) => a + x;
    let g = f;
    let h = f;
    """
    # 期望 Semantic 报错：变量 'f' 已被移动，不能再次使用
    compilerX = Compiler()
    try:
        c_codeX = compilerX.compile(sourceX)
        print(c_codeX)
    except Exception as e:
        print(f"错误: {e}")
    print()

    # 测试 11：无捕获函数应允许复制，不触发 move
    print("测试 11 - 无捕获函数可复制:")
    source11 = """
    let doubled = fn(x) => x * 2;
    let g = doubled;
    let h = doubled;
    let r1 = g(5);
    let r2 = h(5);
    """
    compiler11 = Compiler()
    try:
        c_code11 = compiler11.compile(source11)
        print(c_code11)
    except Exception as e:
        print(f"错误: {e}")
    print()


def main():
    """命令行接口"""
    import sys
    
    if len(sys.argv) != 2:
        print("argv is not equal to 2")
        return
    
    source_code = sys.argv[1]
    compiler = Compiler()
    
    try:
        c_code = compiler.compile(source_code)
        print(c_code)
    except Exception as e:
        print(f"Compile Error: {e}", file=sys.stderr)
        sys.exit(1)

def compile_rustlike_to_c(source_code: str) -> str:
    """main.py 接口"""
    compiler = Compiler()
    return compiler.compile(source_code)

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        # 内嵌测试
        test_compiler()
    else:
        # 命令行测试
        main()