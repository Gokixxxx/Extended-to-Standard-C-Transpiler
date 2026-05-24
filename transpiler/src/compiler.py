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
    # 测试用例1: 基本整数操作
    print("测试 1 - 基本整数:")
    source1 = "let x = 42;"
    compiler1 = Compiler()
    try:
        c_code1 = compiler1.compile(source1)
        print(c_code1)
    except Exception as e:
        print(f"错误: {e}")
    print()
    
    # 测试用例2: Option 类型
    print("测试 2 - Option 类型:")
    source2 = "let opt = Some(5);"
    compiler2 = Compiler()
    try:
        c_code2 = compiler2.compile(source2)
        print(c_code2)
    except Exception as e:
        print(f"错误: {e}")
    print()
    
    # 测试用例3: Match 表达式（完整端到端）
    print("测试 3 - Match 表达式（端到端）:")
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
    
    # 测试用例4: 复杂表达式
    print("测试 4 - 复杂表达式:")
    source4 = """
    let a = 10;
    let b = Some(20);
    let result = match b {
        Some(val) => a + val * 2,
        None => a
    };
    """
    compiler4 = Compiler()
    try:
        c_code4 = compiler4.compile(source4)
        print(c_code4)
    except Exception as e:
        print(f"错误: {e}")
    print()

    # 测试用例5: 函数作为值
    print("测试 5 - 函数作为值:")
    source5 = """
    let double = fn(x) { return x * 2; };
    let result = double(10);
    """
    compiler5 = Compiler()
    try:
        c_code5 = compiler5.compile(source5)
        print(c_code5)
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