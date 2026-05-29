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
                fn_expr_captures=self.analyzer.fn_expr_captures,
                struct_table=self.analyzer.struct_table,
                impl_table=self.analyzer.impl_table
            )
            return c_code
            
        except Exception as e:
            raise RuntimeError(f"Compilation failed: {str(e)}")


def test_compiler():
    source12 = """
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
    let a = rect.area();
    """
    compiler12 = Compiler()
    try:
        c_code12 = compiler12.compile(source12)
        print(c_code12)
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