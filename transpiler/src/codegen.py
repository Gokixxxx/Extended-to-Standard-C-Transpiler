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
        self.in_function = False
        self.func_signatures = {}
        self.fn_expr_counter = 0          # 匿名函数编号计数器
        self.fn_expr_defs = []            # 提升后的全局函数定义代码
        self.fn_expr_types = {}           # fn_expr AST节点 → C函数指针类型字符串
        self.fn_expr_captures = {}

    def generate(self, ast: Tuple, func_signatures: dict = None, fn_expr_captures: dict = None) -> str:
        self.includes.clear()
        self.func_defs.clear()
        self.main_stmts.clear()
        self.func_return_types.clear()
        self.vec_vars.clear()
        self.temp_counter = 0
        self.func_signatures = func_signatures or {}
        self.fn_expr_counter = 0
        self.fn_expr_defs = []
        self.fn_expr_types = {}
        self.fn_expr_captures = fn_expr_captures or {}
        
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
    
    def _c_type_from_str(self, type_str: str) -> str:
        """将语义类型字符串转为 C 类型名"""
        if type_str == 'i32':
            return 'int'
        elif type_str == 'bool':
            return 'int'
        elif type_str == 'Vec<i32>':
            return 'Vec_i32'
        elif type_str.startswith('Option<'):
            return 'Option_i32'
        return 'int'

    def _new_temp(self) -> str:
        self.temp_counter += 1
        return f"__t{self.temp_counter}"
    
    def _new_fn_name(self) -> str:
        self.fn_expr_counter += 1
        return f"__fn_{self.fn_expr_counter}"

    def _gen_fn_expr_type(self, param_count: int, ret_c_type: str) -> str:
        """生成 C 函数指针类型，如 int (*)(int)"""
        params = ', '.join(['int'] * param_count) if param_count > 0 else 'void'
        return f"{ret_c_type} (*)({params})"
    
    def _gen_fn_expr_def(self, node: Tuple, fn_name: str) -> str:
        """将 fn_expr 提升为全局 static 函数"""
        params = node[1]
        body = node[2]
        
        # 推断返回类型
        ret_type = 'int'  # 默认
        for stmt in body:
            if stmt[0] == 'return':
                ret_type = self._infer_expr_type(stmt[1])
                break
        
        # 生成参数列表
        param_parts = [f'int {p}' for p in params]
        param_str = ', '.join(param_parts) if param_parts else 'void'
        
        # 生成函数体
        lines = [f'static {ret_type} {fn_name}({param_str}) {{']
        
        # 收集函数内 Vector，返回前 free
        func_vec_vars = []
        for stmt in body:
            if stmt[0] == 'let_decl' and self._infer_expr_type(stmt[2]) == 'Vec_i32':
                func_vec_vars.append(stmt[1])
        
        for stmt in body:
            stmt_code = self._gen_stmt(stmt)
            for line in stmt_code.split('\n'):
                lines.append(f'    {line}')
        
        for var in func_vec_vars:
            lines.append(f'    free({var}.data);')
        
        lines.append('}')
        
        return '\n'.join(lines)

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
        """
        推断表达式对应的 C 类型名。
        
        抽象类型 -> C 类型 映射：
            i32         -> int
            bool        -> int  (C 无 bool，用 0/1)
            Vec<i32>    -> Vec_i32
            Option<i32> -> Option_i32
            fn(...)->R  -> 函数指针
        """
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
            return 'int'
        elif op == 'match':
            return 'int'
        return 'int'

    # ==================== 程序组装 ====================
    def _build_program(self) -> str:
        lines = []
        lines.append('#include "option.h"')
        lines.append('#include "vec.h"')
        lines.append('#include "closure.h"')
        lines.append('')
        
        for func in self.func_defs:
            lines.append(func)
            lines.append('')
        
        for fn_def in self.fn_expr_defs:
            lines.append(fn_def)
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
        
        func_sig = self.func_signatures.get(func_name, {})
        sig_params = func_sig.get('params', [])

        if any(i < len(sig_params) and sig_params[i] == 'Vec<i32>' for i in range(len(params))):
            self.includes.add('vec.h')
        
        param_parts = []
        for i, p in enumerate(params):
            if i < len(sig_params) and sig_params[i] == 'Vec<i32>':
                param_parts.append(f'Vec_i32 {p}')
            else:
                param_parts.append(f'int {p}')
        
        param_str = ', '.join(param_parts) if param_parts else 'void'
        
        # 收集本函数内声明的 Vector，返回前 free
        func_vec_vars = []
        
        self.in_function = True           # 进入函数
        lines = [f'{ret_type} {func_name}({param_str}) {{']
        for stmt in body:
            if stmt[0] == 'let_decl' and self._infer_expr_type(stmt[2]) == 'Vec_i32':
                func_vec_vars.append(stmt[1])
            
            stmt_code = self._gen_stmt(stmt)
            for line in stmt_code.split('\n'):
                lines.append(f'    {line}')
        
        for var in func_vec_vars:
            lines.append(f'    free({var}.data);')
        
        lines.append('}')
        self.in_function = False          # 退出函数
        
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
        
        if isinstance(expr, tuple) and expr[0] == 'fn_expr':
            params = expr[1]
            body = expr[2]
            ret_c_type = 'int'
            for stmt in body:
                if stmt[0] == 'return':
                    ret_c_type = self._infer_expr_type(stmt[1])
                    break
            expr_code = self._generate_expr(expr)
            param_str = ', '.join(['int'] * len(params)) if params else 'void'
            # 正确语法：ret_type (*var_name)(params) = func_name;
            return f'{ret_c_type} (*{var_name})({param_str}) = {expr_code};'

        if self._contains_match(expr):
            return '\n'.join(self._generate_match_code(var_name, expr))
        
        type_str = self._infer_expr_type(expr)
        c_type = 'Vec_i32' if type_str == 'Vec_i32' else ('Option_i32' if type_str == 'Option_i32' else 'int')

        # 检查是否为函数类型
        if isinstance(type_str, str) and type_str.startswith('fn('):
            arrow_idx = type_str.find(')->')
            if arrow_idx != -1:
                params_str = type_str[3:arrow_idx]
                param_count = len([p for p in params_str.split(',') if p.strip()])
                ret_type_str = type_str[arrow_idx + 3:]
                ret_c_type = self._c_type_from_str(ret_type_str)
                
                expr_code = self._generate_expr(expr)
                param_str = ', '.join(['int'] * param_count) if param_count > 0 else 'void'
                return f'{ret_c_type} (*{var_name})({param_str}) = {expr_code};'
        
        if type_str == 'Vec_i32':
            self.includes.add('vec.h')
            if not self.in_function:
                self.vec_vars.add(var_name)
            if expr[0] == 'vec_literal':
                lines = [f'Vec_i32 {var_name} = vec_new_i32();']
                for elem in expr[1]:
                    elem_code = self._generate_expr(elem)
                    lines.append(f'vec_push_i32(&{var_name}, {elem_code});')
                return '\n'.join(lines)
        
        expr_code = self._generate_expr(expr)
        
        # 处理包含前置语句的表达式（如 call 中的 vec_literal 参数）
        if '\n' in expr_code:
            parts = expr_code.split('\n')
            pre_stmts = parts[:-1]
            actual_expr = parts[-1]
            lines = pre_stmts + [f'{c_type} {var_name} = {actual_expr};']
            return '\n'.join(lines)
        
        return f'{c_type} {var_name} = {expr_code};'

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
            # 使用替换表：match 变量名 -> scrutinee.value
            body_code = self._generate_expr(body, subs={inner_var: f"{scrutinee}.value"})
            lines.append(f"    {var_name} = {body_code};")
        lines.append("} else {")
        if none_case:
            none_code = self._generate_expr(none_case)
            lines.append(f"    {var_name} = {none_code};")
        lines.append("}")
        
        return lines

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
    def _generate_expr(self, expr: Any, subs: dict = None) -> str:
        if subs is None:
            subs = {}
        
        if isinstance(expr, tuple):
            if expr[0] == 'num':
                return str(expr[1])
            elif expr[0] == 'var':
                name = expr[1]
                if name in subs:
                    return subs[name]
                return name
            elif expr[0] == 'some':
                return f"Some_i32({self._generate_expr(expr[1], subs)})"
            elif expr[0] == 'none':
                return "None_i32()"
            elif expr[0] == 'fn_expr':
                # 匿名函数表达式：提升为全局函数，返回函数指针
                fn_name = self._new_fn_name()
                fn_def = self._gen_fn_expr_def(expr, fn_name)
                self.fn_expr_defs.append(fn_def)
                
                params = expr[1]
                ret_c_type = 'int'
                for stmt in expr[2]:
                    if stmt[0] == 'return':
                        ret_c_type = self._infer_expr_type(stmt[1])
                        break
                
                # 返回函数指针值（即函数名本身，在 C 中自动 decay 为指针）
                return fn_name
            elif expr[0] == 'vec_literal':
                return "vec_new_i32()"
            elif expr[0] == 'index':
                obj = self._generate_expr(expr[1], subs)
                idx = self._generate_expr(expr[2], subs)
                return f"vec_get_i32({obj}, {idx})"
            elif expr[0] == 'method_call':
                obj = self._generate_expr(expr[1], subs)
                method = expr[2]
                args = [self._generate_expr(a, subs) for a in expr[3]]
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
                left = self._generate_expr(expr[1], subs)
                right = self._generate_expr(expr[2], subs)
                op_map = {'add': '+', 'sub': '-', 'mul': '*', 'div': '/'}
                return f"({left} {op_map[expr[0]]} {right})"
            elif expr[0] in ['eq', 'neq', 'gt', 'lt', 'gte', 'lte']:
                left = self._generate_expr(expr[1], subs)
                right = self._generate_expr(expr[2], subs)
                op_map = {'eq': '==', 'neq': '!=', 'gt': '>', 'lt': '<', 'gte': '>=', 'lte': '<='}
                return f"({left} {op_map[expr[0]]} {right})"
            elif expr[0] == 'call':
                callee = self._generate_expr(expr[1], subs)
                arg_codes = []
                pre_stmts = []
                for a in expr[2]:
                    if a[0] == 'vec_literal':
                        tmp = self._new_temp()
                        self.includes.add('vec.h')
                        pre_stmts.append(f'Vec_i32 {tmp} = vec_new_i32();')
                        for elem in a[1]:
                            elem_code = self._generate_expr(elem, subs)
                            pre_stmts.append(f'vec_push_i32(&{tmp}, {elem_code});')
                        arg_codes.append(tmp)
                    else:
                        arg_codes.append(self._generate_expr(a, subs))
                
                call_code = f"{callee}({', '.join(arg_codes)})"
                
                if pre_stmts:
                    return '\n'.join(pre_stmts + [call_code])
                return call_code
            elif expr[0] == 'assign':
                lhs = expr[1]
                rhs = self._generate_expr(expr[2], subs)
                if lhs[0] == 'var':
                    return f"{lhs[1]} = {rhs}"
                elif lhs[0] == 'index':
                    obj = self._generate_expr(lhs[1], subs)
                    idx = self._generate_expr(lhs[2], subs)
                    return f"vec_set_i32(&{obj}, {idx}, {rhs})"
            elif expr[0] == 'is_some':
                return f"is_some({self._generate_expr(expr[1], subs)})"
            elif expr[0] == 'is_none':
                return f"is_none({self._generate_expr(expr[1], subs)})"
        return str(expr)


# ==================== 测试 ====================
def test_codegen():
    print("=== C 代码生成器测试 ===")
    
    ast4 = ('program', [
        ('let_decl', 'double', ('fn_expr', ['x'], [
            ('return', ('mul', ('var', 'x'), ('num', 2)))
        ])),
        ('let_decl', 'result', ('call', ('var', 'double'), [('num', 10)]))
    ])
    
    codegen4 = CCodeGenerator()
    print("测试 4 - 函数作为值:")
    print(codegen4.generate(ast4))
    print()


if __name__ == '__main__':
    test_codegen()