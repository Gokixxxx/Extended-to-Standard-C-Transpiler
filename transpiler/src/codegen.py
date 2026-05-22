"""
C代码生成器
"""

from typing import Any, List, Tuple

class CCodeGenerator:
    def __init__(self):
        self.includes = set()
        self.func_defs = []
        self.main_stmts = []
        self.func_return_types = {}
        self.vec_vars = set()
        self.temp_counter = 0

    def generate(self, ast: Tuple) -> str:
        self.includes.clear()
        self.func_defs.clear()
        self.main_stmts.clear()
        self.func_return_types.clear()
        self.vec_vars.clear()
        self.temp_counter = 0
        
        if ast[0] == 'program':
            for top in ast[1]:
                if top[0] == 'func_def':
                    self._infer_func_return_type(top)
            
            for top in ast[1]:
                if top[0] == 'func_def':
                    self.func_defs.append(self._gen_func_def(top))
                else:
                    self._gen_top_stmt(top)
        
        return self._build_program()

    def _new_temp(self) -> str:
        self.temp_counter += 1
        return f"__t{self.temp_counter}"

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
        elif op == 'vec_literal':
            return 'Vec_i32'
        elif op == 'call':
            if expr[1][0] == 'var':
                return self.func_return_types.get(expr[1][1], 'int')
            return 'int'
        elif op == 'method_call':
            if expr[2] in ('len', 'pop'):
                return 'int'
            return 'void'
        elif op == 'index':
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
        if 'vec.h' in self.includes:
            lines.append('#include "vec.h"')
            lines.append('')
        
        for func in self.func_defs:
            lines.append(func)
            lines.append('')
        
        lines.append('int main() {')
        for stmt in self.main_stmts:
            for line in stmt.split('\n'):
                lines.append(f"    {line}")
        
        for var in self.vec_vars:
            lines.append(f"    free({var}.data);")
        
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
        elif node[0] == 'if':
            return self._gen_if(node)
        elif node[0] == 'for_in':
            return self._gen_for_in(node)
        elif node[0] == 'while':
            return self._gen_while(node)
        return ''

    # ==================== let 声明 ====================
    def _gen_let(self, node: Tuple) -> str:
        var_name = node[1]
        expr = node[2]
        
        if self._contains_match(expr):
            return '\n'.join(self._generate_match_code(var_name, expr))
        
        type_str = self._infer_expr_type(expr)
        
        if type_str == 'Vec_i32':
            self.includes.add('vec.h')
            self.vec_vars.add(var_name)
            if expr[0] == 'vec_literal':
                lines = [f'Vec_i32 {var_name} = vec_new_i32();']
                for elem in expr[1]:
                    elem_code = self._generate_expr(elem)
                    lines.append(f'vec_push_i32(&{var_name}, {elem_code});')
                return '\n'.join(lines)
            else:
                expr_code = self._generate_expr(expr)
                return f'Vec_i32 {var_name} = {expr_code};'
        elif type_str == 'Option_i32':
            self.includes.add('option.h')
            expr_code = self._generate_expr(expr)
            return f'Option_i32 {var_name} = {expr_code};'
        else:
            expr_code = self._generate_expr(expr)
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

    # ==================== if ====================
    def _gen_if(self, node: Tuple) -> str:
        cond = self._generate_expr(node[1])
        then_stmts = node[2]
        else_stmts = node[3]
        
        lines = [f"if ({cond}) {{"]
        for stmt in then_stmts:
            for line in self._gen_stmt(stmt).split('\n'):
                lines.append(f"    {line}")
        lines.append("}")
        
        if else_stmts:
            lines.append("else {")
            for stmt in else_stmts:
                for line in self._gen_stmt(stmt).split('\n'):
                    lines.append(f"    {line}")
            lines.append("}")
        
        return '\n'.join(lines)

    # ==================== for_in ====================
    def _gen_for_in(self, node: Tuple) -> str:
        var_name = node[1]
        iterable = self._generate_expr(node[2])
        body = node[3]
        
        idx = self._new_temp()
        
        lines = [
            f"{{",
            f"    int {idx} = 0;",
            f"    for (; {idx} < vec_len_i32({iterable}); {idx}++) {{",
            f"        int {var_name} = vec_get_i32({iterable}, {idx});"
        ]
        
        for stmt in body:
            for line in self._gen_stmt(stmt).split('\n'):
                lines.append(f"        {line}")
        
        lines.append("    }")
        lines.append("}")
        
        return '\n'.join(lines)

    # ==================== while ====================
    def _gen_while(self, node: Tuple) -> str:
        cond = self._generate_expr(node[1])
        body = node[2]
        
        lines = [f"while ({cond}) {{"]
        for stmt in body:
            for line in self._gen_stmt(stmt).split('\n'):
                lines.append(f"    {line}")
        lines.append("}")
        
        return '\n'.join(lines)

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
            elif expr[0] == 'vec_literal':
                return "vec_new_i32()"
            elif expr[0] == 'index':
                obj = self._generate_expr(expr[1])
                idx = self._generate_expr(expr[2])
                return f"vec_get_i32({obj}, {idx})"
            elif expr[0] == 'method_call':
                obj = self._generate_expr(expr[1])
                method = expr[2]
                args = [self._generate_expr(a) for a in expr[3]]
                if method == 'push':
                    return f"vec_push_i32(&{obj}, {', '.join(args)})"
                elif method == 'len':
                    return f"vec_len_i32({obj})"
                elif method == 'pop':
                    return f"vec_pop_i32(&{obj})"
                elif method == 'remove':
                    return f"vec_remove_i32(&{obj}, {', '.join(args)})"
                return f"{method}({obj}, {', '.join(args)})"
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
            elif expr[0] == 'assign':
                var = expr[1]
                val = self._generate_expr(expr[2])
                return f"{var} = {val}"
        return str(expr)


# ==================== 测试 ====================
def test_codegen():
    print("=== C 代码生成器测试 ===")
    
    # 测试 1: if/else
    ast1 = ('program', [
        ('let_decl', 'x', ('num', 5)),
        ('if', ('gt', ('var', 'x'), ('num', 0)), [
            ('expr_stmt', ('assign', 'x', ('sub', ('var', 'x'), ('num', 1))))
        ], [
            ('expr_stmt', ('assign', 'x', ('add', ('var', 'x'), ('num', 1))))
        ])
    ])
    
    codegen = CCodeGenerator()
    print("测试 1 - if/else:")
    print(codegen.generate(ast1))
    print()
    
    # 测试 2: for_in
    ast2 = ('program', [
        ('let_decl', 'arr', ('vec_literal', [('num', 1), ('num', 2), ('num', 3)])),
        ('for_in', 'x', ('var', 'arr'), [
            ('expr_stmt', ('call', ('var', 'print'), [('var', 'x')]))
        ])
    ])
    
    codegen2 = CCodeGenerator()
    print("测试 2 - for_in:")
    print(codegen2.generate(ast2))
    print()
    
    # 测试 3: while
    ast3 = ('program', [
        ('let_decl', 'i', ('num', 0)),
        ('while', ('lt', ('var', 'i'), ('num', 10)), [
            ('expr_stmt', ('assign', 'i', ('add', ('var', 'i'), ('num', 1))))
        ])
    ])
    
    codegen3 = CCodeGenerator()
    print("测试 3 - while:")
    print(codegen3.generate(ast3))
    print()


if __name__ == '__main__':
    test_codegen()