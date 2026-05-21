"""
主编译器入口
集成词法分析、语法分析、语义分析和代码生成
"""

from .lexer import RustLikeLexer
from .parser import RustLikeParser
from .semantic import SemanticAnalyzer
from .codegen import CCodeGenerator


class Compiler:
    def __init__(self):
        """初始化编译器各组件"""
        self.lexer = RustLikeLexer()
        self.parser = RustLikeParser()
        self.analyzer = SemanticAnalyzer()
        self.codegen = CCodeGenerator()
    
    def compile(self, source_code: str) -> str:
        """
        端到端编译：Rust-like 源码 → C 代码
        
        Args:
            source_code: 输入的 Rust-like 源代码字符串
            
        Returns:
            生成的 C 代码字符串
            
        Raises:
            RuntimeError: 编译过程中出现错误
        """
        try:
            # 阶段1: 词法分析
            tokens = self.lexer.tokenize(source_code)
            
            # 阶段2: 语法分析
            ast = self.parser.parse(tokens)
            
            # 阶段3: 语义分析
            if not self.analyzer.analyze(ast):
                self.analyzer.print_errors()
                raise RuntimeError("Semantic analysis failed")
            
            # 阶段4: 代码生成
            c_code = self.codegen.generate(ast)
            return c_code
            
        except Exception as e:
            # 重新抛出带上下文的错误信息
            raise RuntimeError(f"Compilation failed: {str(e)}")


def test_compiler():
    """内嵌端到端编译器测试"""
    print("=== 端到端编译器测试 ===")
    
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
        print(f"编译错误: {e}", file=sys.stderr)
        sys.exit(1)

def compile_rustlike_to_c(source_code: str) -> str:
    """
    将 Rust-like 源码编译为 C 代码的便捷函数
    
    Args:
        source_code: 输入的 Rust-like 源代码字符串
        
    Returns:
        生成的 C 代码字符串
    """
    compiler = Compiler()
    return compiler.compile(source_code)

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        # 运行内嵌测试
        test_compiler()
    else:
        # 命令行模式
        main()