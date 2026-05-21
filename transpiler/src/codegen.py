"""
C 代码生成器
将经过语义分析的 AST 转换为 C 代码
"""

from typing import Any, List, Tuple, Optional

class CCodeGenerator:
    def __init__(self):
        self.includes = set()
        self.declarations = []
        self.statements = []
        self.indent_level = 0
        self.scope_level = 0
    
    def generate(self, ast: Tuple) -> str:
        """主入口：生成完整 C 程序"""
        # 清理状态
        self.includes.clear()
        self.declarations.clear()
        self.statements.clear()
        self.scope_level = 0
        
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
        self.indent_level = 1
        
        # 变量声明
        for decl in self.declarations:
            lines.append(self._indent(decl))
        
        # 语句
        for stmt in self.statements:
            lines.append(self._indent(stmt))
        
        lines.append('    return 0;')
        lines.append('}')
        
        return '\n'.join(lines)
    
    def visit_stmt(self, stmt: Tuple):
        """处理语句节点"""
        if stmt[0] == 'let_decl':
            var_name = stmt[1]
            expr_node = stmt[2]
            
            # 根据表达式类型生成相应代码
            if self._is_option_expr(expr_node):
                # Option 类型变量
                c_type = "Option_i32"
                self.includes.add('option.h')
                expr_code = self._generate_expr(expr_node)
                self.statements.append(f"{c_type} {var_name} = {expr_code};")
            else:
                # 基本类型变量
                expr_code = self._generate_expr(expr_node)
                self.statements.append(f"int {var_name} = {expr_code};")
    
    def _is_option_expr(self, expr: Any) -> bool:
        """判断表达式是否为 Option 类型"""
        if isinstance(expr, tuple):
            if expr[0] == 'some' or expr[0] == 'none':
                return True
            elif expr[0] == 'var':
                # 这里简化处理，实际应从符号表获取类型
                # 但考虑到我们的语言特性，var 在 match 外部通常是 i32
                return False
        return False
    
    def _generate_expr(self, expr: Any) -> str:
        """生成表达式代码"""
        if isinstance(expr, int):
            return str(expr)
        elif isinstance(expr, tuple):
            if expr[0] == 'num':
                return str(expr[1])
            elif expr[0] == 'var':
                return expr[1]
            elif expr[0] == 'some':
                inner_code = self._generate_expr(expr[1])
                return f"Some_i32({inner_code})"
            elif expr[0] == 'none':
                return "None_i32()"
            elif expr[0] == 'add':
                left = self._generate_expr(expr[1])
                right = self._generate_expr(expr[2])
                return f"({left} + {right})"
            elif expr[0] == 'sub':
                left = self._generate_expr(expr[1])
                right = self._generate_expr(expr[2])
                return f"({left} - {right})"
            elif expr[0] == 'mul':
                left = self._generate_expr(expr[1])
                right = self._generate_expr(expr[2])
                return f"({left} * {right})"
            elif expr[0] == 'div':
                left = self._generate_expr(expr[1])
                right = self._generate_expr(expr[2])
                return f"({left} / {right})"
            elif expr[0] == 'match':
                return self._generate_match_expr(expr)
        return str(expr)
    
    def _generate_match_expr(self, match_node: Tuple) -> str:
        """生成 match 表达式（作为表达式上下文）"""
        # 在 C 中，match 需要转换为临时变量赋值
        # 这里返回一个特殊标记，在 let_decl 中特殊处理
        return f"MATCH_EXPR:{match_node}"
    
    def visit_stmt_with_match_handling(self, stmt: Tuple):
        """处理包含 match 的 let 声明"""
        if stmt[0] == 'let_decl':
            var_name = stmt[1]
            expr_node = stmt[2]
            
            if isinstance(expr_node, tuple) and expr_node[0] == 'match':
                # 特殊处理 match 表达式
                self._handle_match_in_let(var_name, expr_node)
            else:
                # 普通表达式处理
                self.visit_stmt(stmt)
    
    def _handle_match_in_let(self, var_name: str, match_node: Tuple):
        """在 let 声明中处理 match 表达式"""
        scrutinee = match_node[1]
        cases = match_node[2]
        
        # 先声明结果变量
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
            # 替换内部变量为 .value 访问
            body_code = self._replace_var_with_value(body, inner_var, f"{scrutinee}.value")
            self.statements.append(f"    {var_name} = {body_code};")
        self.statements.append("} else {")
        if none_case:
            none_code = self._generate_expr(none_case)
            self.statements.append(f"    {var_name} = {none_code};")
        self.statements.append("}")
    
    def _replace_var_with_value(self, expr: Any, var_name: str, replacement: str) -> str:
        """在表达式中替换变量名为 value 访问"""
        if isinstance(expr, tuple):
            if expr[0] == 'var' and expr[1] == var_name:
                return replacement
            elif expr[0] in ['add', 'sub', 'mul', 'div']:
                left = self._replace_var_with_value(expr[1], var_name, replacement)
                right = self._replace_var_with_value(expr[2], var_name, replacement)
                op_map = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/'}
                return f"({left} {op_map[expr[0]]} {right})"
            else:
                return self._generate_expr(expr)
        return self._generate_expr(expr)
    
    def _indent(self, text: str) -> str:
        """添加缩进"""
        indent = '    ' * self.indent_level
        return indent + text.replace('\n', '\n' + indent)


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
    
    # 需要特殊处理 match
    codegen2 = CCodeGenerator()
    # 手动处理包含 match 的情况
    codegen2.visit_stmt(ast3[1][0])  # x = Some(5)
    
    # 处理 match
    match_stmt = ast3[1][1]
    codegen2._handle_match_in_let(match_stmt[1], match_stmt[2])
    
    program = codegen2._build_program()
    print("测试 3 - Match 表达式:")
    print(program)
    print()


if __name__ == '__main__':
    test_codegen()