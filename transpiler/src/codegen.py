"""
C 代码生成器
将经过语义分析的 AST 转换为 C 代码
"""

from typing import Any, List, Tuple, Optional

class CCodeGenerator:
    def __init__(self):
        self.includes = set()
        self.statements = []
        self.indent_level = 0
    
    def generate(self, ast: Tuple) -> str:
        """主入口：生成完整 C 程序"""
        # 清理状态
        self.includes.clear()
        self.statements.clear()
        
        # 处理 AST
        if ast[0] == 'program':
            for stmt in ast[1]:
                self.visit_stmt(stmt)
        
        # 生成完整程序
        return self._build_program()
    
    def _build_program(self) -> str:
        """构建完整的 C 程序"""
        lines = []
        
        # includes
        if 'option.h' in self.includes:
            lines.append('#include "option.h"')
            lines.append('')
        
        lines.append('int main() {')
        
        # 语句
        for stmt in self.statements:
            lines.append(f"    {stmt}")
        
        lines.append('    return 0;')
        lines.append('}')
        
        return '\n'.join(lines)
    
    def visit_stmt(self, stmt: Tuple):
        """处理语句节点"""
        if stmt[0] == 'let_decl':
            var_name = stmt[1]
            expr_node = stmt[2]
            
            # 检查表达式是否包含 match
            if self._contains_match(expr_node):
                # 特殊处理包含 match 的 let 声明
                self._handle_let_with_match(var_name, expr_node)
            else:
                # 普通表达式处理
                expr_code = self._generate_simple_expr(expr_node)
                if self._is_option_expr(expr_node):
                    self.includes.add('option.h')
                    self.statements.append(f"Option_i32 {var_name} = {expr_code};")
                else:
                    self.statements.append(f"int {var_name} = {expr_code};")
    
    def _contains_match(self, expr: Any) -> bool:
        """检查表达式是否包含 match 节点"""
        if isinstance(expr, tuple):
            if expr[0] == 'match':
                return True
            elif expr[0] in ['add', 'sub', 'mul', 'div']:
                return (self._contains_match(expr[1]) or 
                       self._contains_match(expr[2]))
        return False
    
    def _handle_let_with_match(self, var_name: str, expr: Any):
        """处理包含 match 的 let 声明"""
        if isinstance(expr, tuple) and expr[0] == 'match':
            # 直接处理 match 表达式
            self._generate_match_assignment(var_name, expr)
        elif isinstance(expr, tuple) and expr[0] in ['add', 'sub', 'mul', 'div']:
            # 处理包含 match 的二元操作
            if self._contains_match(expr[1]):
                temp_var1 = f"__temp1_{len(self.statements)}"
                self._handle_let_with_match(temp_var1, expr[1])
                right_code = self._generate_simple_expr(expr[2])
                op_map = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/'}
                result_type = "int"  # match 表达式结果总是 int
                self.statements.append(f"{result_type} {var_name} = {temp_var1} {op_map[expr[0]]} {right_code};")
            elif self._contains_match(expr[2]):
                temp_var2 = f"__temp2_{len(self.statements)}"
                left_code = self._generate_simple_expr(expr[1])
                self._handle_let_with_match(temp_var2, expr[2])
                op_map = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/'}
                result_type = "int"
                self.statements.append(f"{result_type} {var_name} = {left_code} {op_map[expr[0]]} {temp_var2};")
        else:
            # 回退到简单表达式
            expr_code = self._generate_simple_expr(expr)
            self.statements.append(f"int {var_name} = {expr_code};")
    
    def _generate_match_assignment(self, var_name: str, match_node: Tuple):
        """生成 match 表达式的赋值语句"""
        scrutinee = match_node[1]
        cases = match_node[2]
        
        # 先声明结果变量（match 结果总是 int 类型）
        self.statements.append(f"int {var_name};")
        
        # 找到 Some 和 None 分支
        some_case = None
        none_case = None
        
        for case in cases:
            if case[0] == 'some_case':
                inner_var = case[1]
                body_expr = case[2]
                some_case = (inner_var, body_expr)
            elif case[0] == 'none_case':
                none_case = case[1]
        
        # 生成 if-else 结构
        self.statements.append(f"if ({scrutinee}.is_some) {{")
        if some_case:
            inner_var, body = some_case
            # 生成 Some 分支的代码
            body_code = self._generate_expr_in_match(body, inner_var, f"{scrutinee}.value")
            self.statements.append(f"    {var_name} = {body_code};")
        self.statements.append("} else {")
        if none_case:
            none_code = self._generate_simple_expr(none_case)
            self.statements.append(f"    {var_name} = {none_code};")
        self.statements.append("}")
    
    def _generate_expr_in_match(self, expr: Any, match_var: str, replacement: str) -> str:
        """在 match 表达式的上下文中生成表达式代码"""
        if isinstance(expr, tuple):
            if expr[0] == 'var':
                if expr[1] == match_var:
                    return replacement
                else:
                    return expr[1]
            elif expr[0] == 'num':
                return str(expr[1])
            elif expr[0] in ['add', 'sub', 'mul', 'div']:
                left = self._generate_expr_in_match(expr[1], match_var, replacement)
                right = self._generate_expr_in_match(expr[2], match_var, replacement)
                op_map = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/'}
                return f"({left} {op_map[expr[0]]} {right})"
        elif isinstance(expr, int):
            return str(expr)
        return str(expr)
    
    def _generate_simple_expr(self, expr: Any) -> str:
        """生成不包含 match 的简单表达式"""
        if isinstance(expr, int):
            return str(expr)
        elif isinstance(expr, tuple):
            if expr[0] == 'num':
                return str(expr[1])
            elif expr[0] == 'var':
                return expr[1]
            elif expr[0] == 'some':
                inner_code = self._generate_simple_expr(expr[1])
                return f"Some_i32({inner_code})"
            elif expr[0] == 'none':
                return "None_i32()"
            elif expr[0] in ['add', 'sub', 'mul', 'div']:
                left = self._generate_simple_expr(expr[1])
                right = self._generate_simple_expr(expr[2])
                op_map = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/'}
                return f"({left} {op_map[expr[0]]} {right})"
        return str(expr)
    
    def _is_option_expr(self, expr: Any) -> bool:
        """判断表达式是否为 Option 类型"""
        if isinstance(expr, tuple):
            if expr[0] == 'some' or expr[0] == 'none':
                return True
        return False


def test_codegen():
    """内嵌测试函数"""
    print("=== C 代码生成器测试 ===")
    
    # 测试用例 1: 基本变量声明
    ast1 = ('program', [
        ('let_decl', 'x', ('num', 42))
    ])
    
    codegen = CCodeGenerator()
    c_code1 = codegen.generate(ast1)
    print("测试 1 - 基本整数:")
    print(c_code1)
    print()
    
    # 测试用例 2: Option 变量
    ast2 = ('program', [
        ('let_decl', 'opt', ('some', ('num', 5)))
    ])
    
    c_code2 = codegen.generate(ast2)
    print("测试 2 - Option 变量:")
    print(c_code2)
    print()
    
    # 测试用例 3: Match 表达式
    ast3 = ('program', [
        ('let_decl', 'x', ('some', ('num', 5))),
        ('let_decl', 'y', ('match', 'x', [
            ('some_case', 'v', ('add', ('var', 'v'), ('num', 1))),
            ('none_case', ('num', 0))
        ]))
    ])
    
    c_code3 = codegen.generate(ast3)
    print("测试 3 - Match 表达式:")
    print(c_code3)
    print()
    
    # 测试用例 4: 复杂表达式中的 match
    ast4 = ('program', [
        ('let_decl', 'a', ('num', 10)),
        ('let_decl', 'b', ('some', ('num', 20))),
        ('let_decl', 'result', ('match', 'b', [
            ('some_case', 'val', ('add', ('var', 'a'), ('mul', ('var', 'val'), ('num', 2)))),
            ('none_case', ('var', 'a'))
        ]))
    ])
    
    c_code4 = codegen.generate(ast4)
    print("测试 4 - 复杂表达式中的 match:")
    print(c_code4)
    print()


if __name__ == '__main__':
    test_codegen()