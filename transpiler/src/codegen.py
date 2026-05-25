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
        self.env_struct_defs = []         # Env 结构体定义代码
        self.closure_vars = set()         # 绑定闭包的变量名
        self.closure_return_funcs = set()   # 返回闭包的命名函数
        self.closure_env_vars = set()     # 需要 free 的闭包变量（顶层）
        self.func_returns_closure = set()
        self.temp_closures = []   # 需要 free 的临时闭包变量名
        self.current_func_params = set()  # 当前命名函数的参数名（避免与顶层闭包变量冲突）
        self.closure_struct_defs = {}   # 动态生成的闭包结构体定义

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

        self.env_struct_defs = []
        self.closure_vars = set()
        self.closure_return_funcs = set()
        self.closure_env_vars = set()
        self.func_returns_closure = set()
        self.temp_closures = []
        self.current_func_params = set()
        self.fn_expr_is_closure = {
            node_id: bool(caps) 
            for node_id, caps in self.fn_expr_captures.items()
        }
        self._pre_scan(ast)
        
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
    
    # ==================== 3.3/3.4 闭包辅助方法 ====================
    def _pre_scan(self, node):
        """预扫描 AST，标记闭包变量和返回闭包的函数"""
        if not isinstance(node, tuple):
            return
        op = node[0]
        if op == 'program':
            for top in node[1]:
                self._pre_scan(top)
        elif op == 'func_def':
            func_name = node[1]
            func_info = self.func_signatures.get(func_name, {})
            ret_type = func_info.get('return_type', 'int')
            if isinstance(ret_type, str) and ret_type.startswith('fn('):
                self.func_returns_closure.add(func_name)
            body = node[3]
            for stmt in body:
                if stmt[0] == 'return':
                    if self._is_closure_expr(stmt[1]):
                        self.closure_return_funcs.add(func_name)
                    break
            # 递归扫描 body
            for stmt in body:
                self._pre_scan(stmt)
        elif op == 'let_decl':
            var_name = node[1]
            expr = node[2]
            if self._is_closure_expr(expr):
                self.closure_vars.add(var_name)
            # 新增：检查函数变量是否返回闭包
            expr_type = self._infer_expr_type(expr)
            if isinstance(expr_type, str) and expr_type.startswith('fn('):
                parsed = self._parse_fn_type(expr_type)
                if parsed:
                    _, ret_type = parsed
                    if isinstance(ret_type, str) and ret_type.startswith('fn('):
                        self.func_returns_closure.add(var_name)
            self._pre_scan(expr)
        elif op == 'expr_stmt':
            self._pre_scan(node[1])
        elif op == 'if':
            self._pre_scan(node[1])
            for s in node[2]: self._pre_scan(s)
            for s in node[3]: self._pre_scan(s)
        elif op == 'for_in':
            self._pre_scan(node[2])
            for s in node[3]: self._pre_scan(s)
        elif op == 'while':
            self._pre_scan(node[1])
            for s in node[2]: self._pre_scan(s)
        elif op == 'return':
            self._pre_scan(node[1])

    def _is_closure_expr(self, expr):
        """判断表达式是否为有捕获的 fn_expr"""
        return (isinstance(expr, tuple) and expr[0] == 'fn_expr' 
                and self.fn_expr_is_closure.get(id(expr), False))

    def _closure_type(self, param_count: int) -> str:
        """根据参数数量返回闭包结构体类型名"""
        return 'Closure_i32' + '_i32' * param_count
    
    def _closure_type_for(self, param_count: int, ret_c_type: str) -> str:
        """根据参数数量和返回类型生成闭包结构体类型名，按需动态生成结构体定义"""
        if ret_c_type == 'int':
            return 'Closure_i32' + '_i32' * param_count
        
        type_name = f'Closure_{ret_c_type}_' + '_i32' * param_count
        if type_name not in self.closure_struct_defs:
            fn_params = 'void *env'
            if param_count > 0:
                fn_params += ', ' + ', '.join(['int'] * param_count)
            def_code = f'''typedef struct {{
                void *env;
                {ret_c_type} (*fn)({fn_params});
            }} {type_name};'''
            self.closure_struct_defs[type_name] = def_code
        return type_name

    def _parse_fn_type(self, type_str: str):
        """解析 'fn(i32,i32)->i32' 为 (['i32','i32'], 'i32')"""
        if not type_str or not type_str.startswith('fn('):
            return None
        arrow_idx = type_str.find(')->')
        if arrow_idx == -1:
            return None
        params = [p.strip() for p in type_str[3:arrow_idx].split(',') if p.strip()]
        ret = type_str[arrow_idx + 3:]
        return (params, ret)

    def _expr_returns_closure(self, expr) -> bool:
        if not isinstance(expr, tuple):
            return False
        op = expr[0]
        if op == 'fn_expr':
            return self._is_closure_expr(expr)
        elif op == 'var':
            name = expr[1]
            if name in self.closure_vars:
                return True
            if name in self.func_returns_closure:
                return True
            func_info = self.func_signatures.get(name, {})
            ret_type = func_info.get('return_type', 'int')
            if isinstance(ret_type, str) and ret_type.startswith('fn('):
                return True
            return False
        elif op == 'call':
            return self._expr_returns_closure(expr[1])
        return False
    
    def _is_closure_callee(self, expr) -> bool:
        """判断 callee 本身是否是闭包变量（需要用 .fn(.env, ...) 调用）"""
        if not isinstance(expr, tuple):
            return False
        op = expr[0]
        if op == 'var':
            name = expr[1]
            # 如果是当前命名函数的参数，优先认为是普通参数（非闭包）
            if name in getattr(self, 'current_func_params', set()):
                return False
            return name in self.closure_vars
        elif op == 'fn_expr':
            return self._is_closure_expr(expr)
        elif op == 'call':
            # 如 add(3) 返回闭包，则 add(3)(4) 的外层 callee 是闭包
            return self._expr_returns_closure(expr)
        return False

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
        """将 fn_expr 提升为全局 static 函数（支持闭包 env）"""
        params = node[1]
        body = node[2]
        captures = self.fn_expr_captures.get(id(node), [])
        
        # 推断返回类型
        ret_type = 'int'
        for stmt in body:
            if stmt[0] == 'return':
                ret_type = self._infer_expr_type(stmt[1])
                if isinstance(ret_type, str) and ret_type.startswith('fn('):
                    parsed = self._parse_fn_type(ret_type)
                    if parsed:
                        ret_params, _ = parsed
                        ret_type = self._closure_type(len(ret_params))
                break
        
        has_captures = bool(captures)
        fn_counter = int(fn_name.split('_')[-1])
        
        if not has_captures:
            # 无捕获：保持原有 ABI
            param_parts = [f'int {p}' for p in params]
            param_str = ', '.join(param_parts) if param_parts else 'void'
            lines = [f'static {ret_type} {fn_name}({param_str}) {{']
        else:
            # 有捕获：增加 void *__env 首参数
            env_struct_name = f'__env_{fn_counter}'
            param_parts = ['void *__env'] + [f'int {p}' for p in params]
            param_str = ', '.join(param_parts)
            lines = [f'static {ret_type} {fn_name}({param_str}) {{']
            lines.append(f'    struct {env_struct_name} *env = (struct {env_struct_name} *)__env;')
            # 为捕获变量创建局部别名（让 body 代码无需改动）
            for cap in captures:
                lines.append(f'    int {cap} = env->{cap};')
        
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
                ret_expr = stmt[1]
                ret_type = self._infer_expr_type(ret_expr)
                # 新增：函数类型 → 闭包结构体类型
                if isinstance(ret_type, str) and ret_type.startswith('fn('):
                    parsed = self._parse_fn_type(ret_type)
                    if parsed:
                        params, _ = parsed
                        ret_type = self._closure_type(len(params))
                self.func_return_types[func_name] = ret_type
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
        elif op == 'call':
            if expr[1][0] == 'var':
                func_name = expr[1][1]
                func_info = self.func_signatures.get(func_name, {})
                ret_type = func_info.get('return_type', 'int')
                if isinstance(ret_type, str) and ret_type.startswith('fn('):
                    parsed = self._parse_fn_type(ret_type)
                    if parsed:
                        params, _ = parsed
                        return self._closure_type(len(params))
                return self.func_return_types.get(func_name, 'int')
            return 'int'
        
        elif op == 'fn_expr':
            params = expr[1]
            body = expr[2]
            ret_type = 'void'
            for stmt in body:
                if isinstance(stmt, tuple) and stmt[0] == 'return':
                    ret_expr = stmt[1]
                    ret_type = self._infer_expr_type(ret_expr)
                    break
            param_types = ['i32'] * len(params)
            return f"fn({','.join(param_types)})->{ret_type}"
        return 'int'

    # ==================== 程序组装 ====================
    def _build_program(self) -> str:
        lines = []
        lines.append('#include "option.h"')
        lines.append('#include "vec.h"')
        lines.append('#include "closure.h"')
        lines.append('')

        # 动态生成的闭包结构体（返回闭包的情况）
        for closure_def in self.closure_struct_defs.values():
            lines.append(closure_def)
            lines.append('')
        
        # 先输出 Env 结构体（函数定义依赖它们）
        for env_def in self.env_struct_defs:
            lines.append(env_def)
            lines.append('')
        
        # 命名函数定义
        for func in self.func_defs:
            lines.append(func)
            lines.append('')
        
        # 提升的匿名函数定义
        for fn_def in self.fn_expr_defs:
            lines.append(fn_def)
            lines.append('')
        
        lines.append('int main() {')
        for stmt in self.main_stmts:
            for line in stmt.split('\n'):
                lines.append(f"    {line}")
        
        for var in self.vec_vars:
            lines.append(f"    free({var}.data);")
        
        # 释放顶层闭包 Env
        for var in self.closure_env_vars:
            lines.append(f"    free({var}_env);")

        # 释放临时闭包 Env
        for tmp in self.temp_closures:
            lines.append(f"    free({tmp}.env);")
        
        lines.append('    return 0;')
        lines.append('}')
        
        return '\n'.join(lines)

    # ==================== 函数定义 ====================
    def _gen_func_def(self, node: Tuple) -> str:
        func_name = node[1]
        params = node[2]
        body = node[3]
        ret_type = self.func_return_types.get(func_name, 'int')
        
        # 记录当前函数参数，避免与顶层闭包变量同名冲突
        self.current_func_params = set(params)
        
        func_sig = self.func_signatures.get(func_name, {})
        sig_params = func_sig.get('params', [])

        if any(i < len(sig_params) and sig_params[i] == 'Vec<i32>' for i in range(len(params))):
            self.includes.add('vec.h')
        
        param_parts = []
        for i, p in enumerate(params):
            if i < len(sig_params):
                param_type = sig_params[i]
                if param_type == 'Vec<i32>':
                    param_parts.append(f'Vec_i32 {p}')
                elif isinstance(param_type, str) and param_type.startswith('fn('):
                    parsed = self._parse_fn_type(param_type)
                    if parsed:
                        fn_params, _ = parsed
                        param_parts.append(f'int (*{p})({", ".join(["int"] * len(fn_params))})')
                    else:
                        param_parts.append(f'int {p}')
                else:
                    param_parts.append(f'int {p}')
            else:
                param_parts.append(f'int {p}')
                
        param_str = ', '.join(param_parts) if param_parts else 'void'
        
        func_vec_vars = []
        self.in_function = True
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
        self.in_function = False
        self.current_func_params = set()  # 清理
        return '\n'.join(lines)

    # ==================== 顶层语句 ====================
    def _gen_top_stmt(self, node: Tuple):
        self.main_stmts.append(self._gen_stmt(node))

    def _gen_stmt(self, node: Tuple) -> str:
        if node[0] == 'let_decl':
            return self._gen_let(node)
        elif node[0] == 'return':
            expr_code = self._generate_expr(node[1])
            if '\n' in expr_code:
                parts = expr_code.split('\n')
                pre_stmts = parts[:-1]
                actual_expr = parts[-1]
                return '\n'.join(pre_stmts + [f'return {actual_expr};'])
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
            captures = self.fn_expr_captures.get(id(expr), [])
            params = expr[1]
            body = expr[2]
            
            # 推断返回类型
            ret_c_type = 'int'
            for stmt in body:
                if stmt[0] == 'return':
                    ret_c_type = self._infer_expr_type(stmt[1])
                    if isinstance(ret_c_type, str) and ret_c_type.startswith('fn('):
                        parsed = self._parse_fn_type(ret_c_type)
                        if parsed:
                            params_ret, _ = parsed
                            ret_c_type = self._closure_type(len(params_ret))
                    break
            
            fn_name = self._new_fn_name()
            fn_counter = self.fn_expr_counter
            fn_def = self._gen_fn_expr_def(expr, fn_name)
            self.fn_expr_defs.append(fn_def)
            
            if not captures:
                # 无捕获：函数指针
                param_str = ', '.join(['int'] * len(params)) if params else 'void'
                return f'{ret_c_type} (*{var_name})({param_str}) = {fn_name};'
            else:
                # 有捕获：闭包结构体
                env_struct_name = f'__env_{fn_counter}'
                fields = '\n    '.join([f'int {cap};' for cap in captures])
                env_def = f'struct {env_struct_name} {{\n    {fields}\n}};'
                self.env_struct_defs.append(env_def)
                
                lines = []
                lines.append(f'struct {env_struct_name} *{var_name}_env = malloc(sizeof(struct {env_struct_name}));')
                for cap in captures:
                    lines.append(f'{var_name}_env->{cap} = {cap};')
                
                closure_type = self._closure_type_for(len(params), ret_c_type)
                lines.append(f'{closure_type} {var_name} = {{{var_name}_env, {fn_name}}};')
                
                if not self.in_function:
                    self.closure_env_vars.add(var_name)
                
                return '\n'.join(lines)

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
                if isinstance(ret_type_str, str) and ret_type_str.startswith('fn('):
                    parsed = self._parse_fn_type(ret_type_str)
                    if parsed:
                        params_ret, _ = parsed
                        ret_c_type = self._closure_type(len(params_ret))
                
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
                fn_name = self._new_fn_name()
                fn_counter = self.fn_expr_counter
                captures = self.fn_expr_captures.get(id(expr), [])
                
                fn_def = self._gen_fn_expr_def(expr, fn_name)
                self.fn_expr_defs.append(fn_def)
                
                if not captures:
                    return fn_name
                else:
                    # 生成 Env 结构体定义
                    env_struct_name = f'__env_{fn_counter}'
                    fields = '\n    '.join([f'int {cap};' for cap in captures])
                    env_def = f'struct {env_struct_name} {{\n    {fields}\n}};'
                    self.env_struct_defs.append(env_def)
                    
                    # 生成 Env 实例 + 闭包结构体
                    env_name = self._new_temp()
                    pre_stmts = [
                        f'struct {env_struct_name} *{env_name} = malloc(sizeof(struct {env_struct_name}));'
                    ]
                    for cap in captures:
                        pre_stmts.append(f'{env_name}->{cap} = {cap};')
                    
                    # 推断返回类型
                    ret_c_type = 'int'
                    for stmt in expr[2]:
                        if stmt[0] == 'return':
                            ret_c_type = self._infer_expr_type(stmt[1])
                            if isinstance(ret_c_type, str) and ret_c_type.startswith('fn('):
                                parsed = self._parse_fn_type(ret_c_type)
                                if parsed:
                                    params_ret, _ = parsed
                                    ret_c_type = self._closure_type(len(params_ret))
                            break
                    
                    closure_type = self._closure_type_for(len(expr[1]), ret_c_type)
                    closure_name = self._new_temp()
                    pre_stmts.append(f'{closure_type} {closure_name} = {{{env_name}, {fn_name}}};')
                    
                    return '\n'.join(pre_stmts + [closure_name])
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
                callee_expr = expr[1]
                args = expr[2]
                # 判断 callee 是否为闭包
                is_closure = self._is_closure_callee(callee_expr)
                # 生成参数代码（支持 vec_literal 前置语句）
                arg_codes = []
                pre_stmts = []
                for a in args:
                    if a[0] == 'vec_literal':
                        tmp = self._new_temp()
                        self.includes.add('vec.h')
                        pre_stmts.append(f'Vec_i32 {tmp} = vec_new_i32();')
                        for elem in a[1]:
                            elem_code = self._generate_expr(elem, subs)
                            pre_stmts.append(f'vec_push_i32(&{tmp}, {elem_code});')
                        arg_codes.append(tmp)
                    else:
                        arg_code = self._generate_expr(a, subs)
                        if '\n' in arg_code:
                            parts = arg_code.split('\n')
                            pre_stmts.extend(parts[:-1])
                            arg_codes.append(parts[-1])
                        else:
                            arg_codes.append(arg_code) 
                # 生成 callee 代码
                callee_code = self._generate_expr(callee_expr, subs)
                if is_closure and callee_expr[0] == 'call':
                    tmp = self._new_temp()
                    closure_type = self._closure_type(len(args))
                    pre_stmts.append(f'{closure_type} {tmp} = {callee_code};')
                    callee_code = tmp
                    self.temp_closures.append(tmp)
                if '\n' in callee_code:
                    parts = callee_code.split('\n')
                    pre_stmts.extend(parts[:-1])
                    callee_code = parts[-1]
                
                # 构建调用
                if is_closure:
                    call_code = f"{callee_code}.fn({callee_code}.env, {', '.join(arg_codes)})"
                else:
                    call_code = f"{callee_code}({', '.join(arg_codes)})"
                
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