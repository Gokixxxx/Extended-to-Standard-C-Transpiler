"""
C代码生成器
"""

from typing import Any, List, Tuple

class CCodeGenerator:
    def __init__(self):
        self.includes = set()
        self.func_defs = []          # 函数定义代码（多行字符串列表）
        self.main_stmts = []         # main 函数内的语句
        self.func_return_types = {}  # 函数名 -> C类型字符串

    def generate(self, ast: Tuple) -> str:
        self.includes.clear()
        self.func_defs.clear()
        self.main_stmts.clear()
        self.func_return_types.clear()
        
        if ast[0] == 'program':
            # 第一遍：推断所有函数返回类型
            for top in ast[1]:
                if top[0] == 'func_def':
                    self._infer_func_return_type(top)
            
            # 第二遍：生成代码
            for top in ast[1]:
                if top[0] == 'func_def':
                    self.func_defs.append(self._gen_func_def(top))
                else:
                    self._gen_top_stmt(top)
        
        return self._build_program()

    # ==================== 类型推断 ====================
    def _infer_func_return_type(self, node: Tuple):
        func_name = node[1]
        body = node[3]
        for stmt in body:
            if stmt[0] == 'return':
                self.func_return_types[func_name] = self._infer_expr_type(stmt[1])
                return
        self.func_return_types[func_name] = 'int'

    def _infer_expr_type(self, expr: Any) -> str:
        if not isinstance(expr, tuple):
            return 'int'
        op = expr[0]
        if op in ('some', 'none'):
            return 'Option_i32'
        elif op == 'num':
            return 'int'
        elif op == 'var':
            return 'int'
        elif op == 'call':
            if expr[1][0] == 'var':
                return self.func_return_types.get(expr[1][1], 'int')
            return 'int'
        elif op in ('add', 'sub', 'mul', 'div'):
            return 'int'
        elif op in ('eq', 'neq', 'gt', 'lt', 'gte', 'lte'):
            return 'bool'
        elif op == 'match':
            return 'int'
        return 'int'

    # ==================== 程序组装 ====================
    def _build_program(self) -> str:
        lines = []
        if 'option.h' in self.includes:
            lines.append('#include "option.h"')
            lines.append('')
        
        for func in self.func_defs:
            lines.append(func)
            lines.append('')
        
        lines.append('int main() {')
        for stmt in self.main_stmts:
            for line in stmt.split('\n'):
                lines.append(f"    {line}")
        lines.append('    return 0;')
        lines.append('}')
        
        return '\n'.join(lines)

    # ==================== 函数定义 ====================
    def _gen_func_def(self, node: Tuple) -> str:
        func_name = node[1]
        params = node[2]
        body = node[3]
        ret_type = self.func_return_types.get(func_name, 'int')
        
        param_str = ', '.join(f'int {p}' for p in params) if params else 'void'
        
        lines = [f'{ret_type} {func_name}({param_str}) {{']
        for stmt in body:
            stmt_code = self._gen_stmt(stmt)
            for line in stmt_code.split('\n'):
                lines.append(f'    {line}')
        lines.append('}')
        
        return '\n'.join(lines)

    # ==================== 顶层语句 ====================
    def _gen_top_stmt(self, node: Tuple):
        self.main_stmts.append(self._gen_stmt(node))

    def _gen_stmt(self, node: Tuple) -> str:
        if node[0] == 'let_decl':
            return self._gen_let(node)
        elif node[0] == 'return':
            expr_code = self._generate_expr(node[1])
            return f'return {expr_code};'
        elif node[0] == 'expr_stmt':
            expr_code = self._generate_expr(node[1])
            return f'{expr_code};'
        return ''

    # ==================== let 声明（含 match 处理）====================
    def _gen_let(self, node: Tuple) -> str:
        var_name = node[1]
        expr = node[2]
        
        if self._contains_match(expr):
            return '\n'.join(self._generate_match_code(var_name, expr))
        
        type_str = self._infer_expr_type(expr)
        expr_code = self._generate_expr(expr)
        
        if type_str == 'Option_i32':
            self.includes.add('option.h')
            return f'Option_i32 {var_name} = {expr_code};'
        return f'int {var_name} = {expr_code};'

    def _contains_match(self, expr: Any) -> bool:
        if isinstance(expr, tuple):
            if expr[0] == 'match':
                return True
            for child in expr[1:]:
                if self._contains_match(child):
                    return True
        return False

    def _generate_match_code(self, var_name: str, match_node: Tuple) -> List[str]:
        scrutinee = match_node[1]
        cases = match_node[2]
        
        lines = [f"int {var_name};"]
        
        some_case = None
        none_case = None
        for case in cases:
            if case[0] == 'some_case':
                some_case = (case[1], case[2])
            elif case[0] == 'none_case':
                none_case = case[1]
        
        lines.append(f"if ({scrutinee}.is_some) {{")
        if some_case:
            inner_var, body = some_case
            body_code = self._generate_expr_in_match(body, inner_var, f"{scrutinee}.value")
            lines.append(f"    {var_name} = {body_code};")
        lines.append("} else {")
        if none_case:
            none_code = self._generate_expr(none_case)
            lines.append(f"    {var_name} = {none_code};")
        lines.append("}")
        
        return lines

    def _generate_expr_in_match(self, expr: Any, match_var: str, replacement: str) -> str:
        if isinstance(expr, tuple):
            if expr[0] == 'var':
                return replacement if expr[1] == match_var else expr[1]
            elif expr[0] == 'num':
                return str(expr[1])
            elif expr[0] in ['add', 'sub', 'mul', 'div']:
                left = self._generate_expr_in_match(expr[1], match_var, replacement)
                right = self._generate_expr_in_match(expr[2], match_var, replacement)
                op_map = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/'}
                return f"({left} {op_map[expr[0]]} {right})"
            elif expr[0] == 'call':
                callee = self._generate_expr_in_match(expr[1], match_var, replacement)
                args = [self._generate_expr_in_match(a, match_var, replacement) for a in expr[2]]
                return f"{callee}({', '.join(args)})"
        return str(expr)

    # ==================== 通用表达式生成 ====================
    def _generate_expr(self, expr: Any) -> str:
        if isinstance(expr, tuple):
            if expr[0] == 'num':
                return str(expr[1])
            elif expr[0] == 'var':
                return expr[1]
            elif expr[0] == 'some':
                return f"Some_i32({self._generate_expr(expr[1])})"
            elif expr[0] == 'none':
                return "None_i32()"
            elif expr[0] in ['add', 'sub', 'mul', 'div']:
                left = self._generate_expr(expr[1])
                right = self._generate_expr(expr[2])
                op_map = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/'}
                return f"({left} {op_map[expr[0]]} {right})"
            elif expr[0] in ['eq', 'neq', 'gt', 'lt', 'gte', 'lte']:
                left = self._generate_expr(expr[1])
                right = self._generate_expr(expr[2])
                op_map = {'eq': '==', 'neq': '!=', 'gt': '>', 'lt': '<', 'gte': '>=', 'lte': '<='}
                return f"({left} {op_map[expr[0]]} {right})"
            elif expr[0] == 'call':
                callee = self._generate_expr(expr[1])
                args = [self._generate_expr(a) for a in expr[2]]
                return f"{callee}({', '.join(args)})"
        return str(expr)


# ==================== 测试 ====================
def test_codegen():
    print("=== C 代码生成器测试 ===")
    
    # 测试 1: 基本函数定义和调用
    ast1 = ('program', [
        ('func_def', 'add', ['a', 'b'], [
            ('return', ('add', ('var', 'a'), ('var', 'b')))
        ]),
        ('let_decl', 'x', ('call', ('var', 'add'), [('num', 1), ('num', 2)]))
    ])
    
    codegen = CCodeGenerator()
    print("测试 1 - 函数定义和调用:")
    print(codegen.generate(ast1))
    print()
    
    # 测试 2: Option + match + 函数
    ast2 = ('program', [
        ('func_def', 'find', ['arr', 'target'], [
            ('return', ('some', ('num', 5)))
        ]),
        ('let_decl', 'x', ('call', ('var', 'find'), [('num', 0), ('num', 3)])),
        ('let_decl', 'y', ('match', 'x', [
            ('some_case', 'v', ('add', ('var', 'v'), ('num', 1))),
            ('none_case', ('num', 0))
        ]))
    ])
    
    codegen2 = CCodeGenerator()
    print("测试 2 - Option + match + 函数:")
    print(codegen2.generate(ast2))
    print()


if __name__ == '__main__':
    test_codegen()