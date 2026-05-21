"""
语义分析器
"""

# transpiler/src/semantic.py
from typing import Dict, List, Optional, Tuple, Any, Set
from .parser import RustLikeParser

class SemanticAnalyzer:
    def __init__(self):
        # 符号表：栈式结构，每个作用域一个字典
        self.symbol_table: List[Dict[str, str]] = [{}]  # [{var: type}]
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def reset(self):
        self.symbol_table = [{}]
        self.errors = []
        self.warnings = []
    
    # ============ 作用域管理 ============
    def enter_scope(self):
        """进入新作用域（如 match 分支）"""
        self.symbol_table.append({})
    
    def exit_scope(self):
        """退出当前作用域"""
        if len(self.symbol_table) > 1:
            self.symbol_table.pop()
    
    def declare(self, name: str, type_info: str, is_shadowing_allowed: bool = False):
        """声明变量"""
        if name in self.symbol_table[-1]:
            if not is_shadowing_allowed:
                self.errors.append(f"错误: 变量 '{name}' 在当前作用域中已声明")
            return False
        self.symbol_table[-1][name] = type_info
        return True
    
    def lookup(self, name: str) -> Optional[str]:
        """查找变量（从内向外查找）"""
        for scope in reversed(self.symbol_table):
            if name in scope:
                return scope[name]
        return None
    
    # ============ 主分析入口 ============
    def analyze(self, ast: Tuple) -> bool:
        """分析整个程序，返回 True 表示无错误"""
        self.errors.clear()
        self.visit(ast)
        return len(self.errors) == 0
    
    def visit(self, node: Any):
        """分发到具体节点处理"""
        if node is None:
            return
        
        if isinstance(node, tuple):
            node_type = node[0]
            
            if node_type == 'program':
                for stmt in node[1]:
                    self.visit(stmt)
            
            elif node_type == 'let_decl':
                self.visit_let_decl(node)
            
            elif node_type == 'match':
                self.visit_match(node)
            
            elif node_type in ['add', 'sub', 'mul', 'div', 'eq', 'neq']:
                self.visit_binary_op(node)
            
            elif node_type in ['is_some', 'is_none']:
                self.visit_type_test(node)
            
            else:
                # 递归访问子节点
                for child in node[1:]:
                    self.visit(child)
        
        elif isinstance(node, list):
            for item in node:
                self.visit(item)
    
    # ============ 具体节点处理 ============
    def visit_let_decl(self, node: Tuple):
        """处理 let 声明：let x = expr;"""
        var_name = node[1]
        expr_node = node[2]
        
        # 分析表达式类型
        expr_type = self.visit_expr(expr_node)
        
        # 声明变量
        self.declare(var_name, expr_type)
    
    def visit_match(self, node: Tuple):
        """处理 match 表达式"""
        scrutinee_name = node[1]  # match x { ... }
        cases = node[2]
        
        # 查找被匹配的变量
        scrutinee_type = self.lookup(scrutinee_name)
        if scrutinee_type is None:
            self.errors.append(f"错误: 未声明的变量 '{scrutinee_name}'")
            return
        
        # 检查是否为 Option 类型
        if not scrutinee_type.startswith('Option<'):
            self.errors.append(
                f"错误: match 表达式必须作用于 Option 类型，但 '{scrutinee_name}' 是 {scrutinee_type}"
            )
            return
        
        # 检查分支是否穷尽
        has_some = any(c[0] == 'some_case' for c in cases)
        has_none = any(c[0] == 'none_case' for c in cases)
        
        if not (has_some and has_none):
            self.errors.append("错误: match 表达式必须同时包含 Some 和 None 分支")
        
        # 分析每个分支
        for case in cases:
            self.visit_case(case, scrutinee_type)
    
    def visit_case(self, case: Tuple, scrutinee_type: str):
        """处理 match 分支"""
        case_type = case[0]
        
        if case_type == 'some_case':
            # Some(v) => expr
            var_name = case[1]
            expr_node = case[2]
            
            # 提取 Option 内部类型
            inner_type = scrutinee_type[7:-1] if scrutinee_type.startswith('Option<') else 'unknown'
            
            # 在新作用域中声明 v
            self.enter_scope()
            self.declare(var_name, inner_type)
            self.visit_expr(expr_node)
            self.exit_scope()
        
        elif case_type == 'none_case':
            # None => expr
            expr_node = case[1]
            self.visit_expr(expr_node)
    
    def visit_expr(self, node: Any) -> str:
        """分析表达式并返回类型"""
        if isinstance(node, tuple):
            node_type = node[0]
            
            if node_type == 'var':
                # 变量
                name = node[1]
                t = self.lookup(name)
                if t is None:
                    self.errors.append(f"错误: 使用未声明的变量 '{name}'")
                    return 'unknown'
                return t
            
            elif node_type == 'num':
                # 数字字面量
                return 'i32'
            
            elif node_type == 'some':
                # Some(expr)
                inner_type = self.visit_expr(node[1])
                return f'Option<{inner_type}>'
            
            elif node_type == 'none':
                # None
                return 'Option<unknown>'
            
            elif node_type in ['add', 'sub', 'mul', 'div']:
                # 二元运算
                left_type = self.visit_expr(node[1])
                right_type = self.visit_expr(node[2])
                
                if left_type != 'i32' or right_type != 'i32':
                    self.errors.append(
                        f"错误: 不能对 {left_type} 和 {right_type} 执行算术运算"
                    )
                return 'i32'
            
            elif node_type in ['eq', 'neq']:
                # 比较运算
                left_type = self.visit_expr(node[1])
                right_type = self.visit_expr(node[2])
                
                if left_type != right_type:
                    self.warnings.append(
                        f"警告: 比较不同类型的值 {left_type} 和 {right_type}"
                    )
                return 'bool'
            
            elif node_type == 'is_some' or node_type == 'is_none':
                # is_some / is_none
                expr_type = self.visit_expr(node[1])
                if not expr_type.startswith('Option<'):
                    self.errors.append(
                        f"错误: {node_type} 只能用于 Option 类型，但得到 {expr_type}"
                    )
                return 'bool'
            
            elif node_type == 'match':
                # match 表达式
                self.visit_match(node)
                # 返回分支表达式的类型（简化：假设所有分支类型一致）
                return 'i32'  # TODO: 实际应检查所有分支类型是否一致
        
        return 'unknown'
    
    def visit_binary_op(self, node: Tuple):
        """处理二元运算"""
        op = node[0]
        left = node[1]
        right = node[2]
        
        left_type = self.visit_expr(left)
        right_type = self.visit_expr(right)
        
        # 类型检查已在 visit_expr 中完成
    
    def visit_type_test(self, node: Tuple):
        """处理类型测试（is_some / is_none）"""
        expr = node[1]
        expr_type = self.visit_expr(expr)
        
        if not expr_type.startswith('Option<'):
            op_name = 'is_some' if node[0] == 'is_some' else 'is_none'
            self.errors.append(
                f"错误: {op_name} 只能用于 Option 类型，但得到 {expr_type}"
            )
    
    # ============ 错误报告 ============
    def print_errors(self):
        """打印所有错误和警告"""
        if self.errors:
            print("\n语义错误:")
            for i, err in enumerate(self.errors, 1):
                print(f"  {i}. {err}")
        
        if self.warnings:
            print("\n警告:")
            for i, warn in enumerate(self.warnings, 1):
                print(f"  {i}. {warn}")
        
        if not self.errors and not self.warnings:
            print("\n语义检查通过！")

# ============ 使用示例 ============
if __name__ == '__main__':
    from .lexer import RustLikeLexer
    
    # 测试代码
    test_cases = [
        # 有效代码
        ("有效代码", """
            let x = Some(5);
            let y = match x { Some(v) => v + 1, None => 0 };
        """),
        
        # 错误：match 缺少 None 分支
        ("缺少 None 分支", """
            let x = Some(5);
            let y = match x { Some(v) => v + 1 };
        """),
        
        # 错误：使用未声明变量
        ("未声明变量", """
            let y = z + 1;
        """),
        
        # 错误：对 Option 执行算术运算
        ("Option 算术错误", """
            let x = Some(5);
            let y = x + 1;
        """),
    ]
    
    lexer = RustLikeLexer()
    parser = RustLikeParser()
    analyzer = SemanticAnalyzer()
    
    for name, code in test_cases:
        print(f"\n{'='*50}")
        print(f"测试: {name}")
        print(f"{'='*50}")
        print("代码:")
        print(code)
        
        try:
            tokens = lexer.tokenize(code)
            ast = parser.parse(tokens)
            print("\nAST:")
            import pprint
            pprint.pprint(ast)

            analyzer.reset()
            
            success = analyzer.analyze(ast)
            analyzer.print_errors()
            
            if success:
                print("通过")
            else:
                print("失败")
        
        except Exception as e:
            print(f"解析错误: {e}")