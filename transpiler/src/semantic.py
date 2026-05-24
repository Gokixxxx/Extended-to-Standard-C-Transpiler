"""
语义分析器
"""

from typing import Dict, List, Optional, Tuple, Any

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table: List[Dict[str, str]] = [{}]
        self.func_table: Dict[str, Dict[str, Any]] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.current_func: Optional[str] = None
        self.deferred_funcs = []
        self._in_fn_expr = False
        self._fn_expr_ret_type = 'void'
        self._predeclared: Dict[str, str] = {}
        self.fn_expr_captures: Dict[int, List[str]] = {}

    def reset(self):
        self.symbol_table = [{}]
        self.func_table = {}
        self.errors = []
        self.warnings = []
        self.current_func = None
        self.deferred_funcs = []
        self._predeclared = {}
        self.fn_expr_captures.clear()

    # ============ 作用域管理 ============
    def enter_scope(self):
        self.symbol_table.append({})

    def exit_scope(self):
        if len(self.symbol_table) > 1:
            self.symbol_table.pop()

    def declare(self, name: str, type_info: str, is_shadowing_allowed: bool = False):
        if name in self.symbol_table[-1]:
            if not is_shadowing_allowed:
                self.errors.append(f"错误: 变量 '{name}' 在当前作用域中已声明")
            return False
        self.symbol_table[-1][name] = type_info
        return True

    def lookup(self, name: str) -> Optional[str]:
        for scope in reversed(self.symbol_table):
            if name in scope:
                return scope[name]
        return None

    # ============ 主分析入口 ============
    def analyze(self, ast: Tuple) -> bool:
        self.reset()
        if ast is None:
            self.errors.append("Error: parse error, AST is None")
            return False
        
        # 第一遍：收集所有顶层函数签名
        if ast[0] == 'program':
            for top in ast[1]:
                if top[0] == 'func_def':
                    func_name = top[1]
                    params = top[2]
                    self.func_table[func_name] = {
                        'params': ['unknown'] * len(params),
                        'return_type': 'unknown'
                    }

        # 第1.5遍：预收集顶层 let_decl 变量类型（用于调用参数推断）
        self._predeclared.clear()
        if ast[0] == 'program':
            for top in ast[1]:
                if top[0] == 'let_decl':
                    var_name = top[1]
                    expr_node = top[2]
                    if expr_node[0] == 'fn_expr':
                        params = expr_node[1]
                        body = expr_node[2]
                        ret_type = 'void'
                        for stmt in body:
                            if isinstance(stmt, tuple) and stmt[0] == 'return':
                                ret_type = self._quick_infer_type(stmt[1])
                                break
                        expr_type = f"fn({','.join(['i32'] * len(params))})->{ret_type}"
                    else:
                        expr_type = self._quick_infer_type(expr_node)
                    self._predeclared[var_name] = expr_type
        
        # 第二遍：扫描所有调用节点，推断顶层函数参数类型
        self._collect_calls(ast)
        
        # 第三遍：分析所有节点（包括顶层 let_decl、expr_stmt、func_def）
        self.visit(ast)
        
        return len(self.errors) == 0
    
    def parse_fn_type(self, type_str: str):
        """将 'fn(i32,i32)->i32' 解析为 (['i32', 'i32'], 'i32')，失败返回 None"""
        if not type_str or not type_str.startswith('fn('):
            return None
        arrow_idx = type_str.find(')->')
        if arrow_idx == -1:
            return None
        params_str = type_str[3:arrow_idx]
        ret_type = type_str[arrow_idx + 3:]
        params = [p.strip() for p in params_str.split(',') if p.strip()]
        return (params, ret_type)

    def _collect_calls(self, node: Any):
        """递归扫描 AST，找到所有 call 节点并推断参数类型"""
        if isinstance(node, tuple):
            if node[0] == 'call':
                # 处理这个调用，推断参数类型
                self._infer_call_types(node)
            
            # 递归扫描所有子节点
            for child in node[1:]:
                self._collect_calls(child)
                
        elif isinstance(node, list):
            for item in node:
                self._collect_calls(item)
    
    def _infer_call_types(self, node: Tuple):
        callee_node = node[1]
        args = node[2]

        func_info = None

        if callee_node[0] == 'var':
            func_name = callee_node[1]
            func_info = self.func_table.get(func_name)
            # 注意：第二遍扫描时符号表为空，无法 lookup 变量类型
            # 函数变量的类型在第三遍 visit_let_decl 时确定，此处不处理
        elif callee_node[0] == 'fn_expr':
            # 匿名函数直接调用，无需更新 func_table
            return

        if func_info is None:
            return

        for i, arg in enumerate(args):
            arg_type = self._quick_infer_type(arg)
            if i < len(func_info['params']) and func_info['params'][i] == 'unknown':
                func_info['params'][i] = arg_type
    
    def _quick_infer_type(self, node: Any) -> str:
        """快速推断类型，不报错，用于参数类型推断"""
        if not isinstance(node, tuple):
            return 'int'
        
        op = node[0]
        if op == 'num':
            return 'i32'
        elif op == 'vec_literal':
            return 'Vec<i32>'
        elif op == 'some':
            inner = self._quick_infer_type(node[1])
            return f'Option<{inner}>'
        elif op == 'none':
            return 'Option<i32>'
        elif op == 'var':
            t = self.lookup(node[1])
            if t:
                return t
            return self._predeclared.get(node[1], 'unknown')
        elif op in ('add', 'sub', 'mul', 'div'):
            return 'i32'
        elif op in ('eq', 'neq', 'gt', 'lt', 'gte', 'lte'):
            return 'bool'
        elif op == 'call':
            func_name = node[1][1] if node[1][0] == 'var' else ''
            func_info = self.func_table.get(func_name)
            return func_info['return_type'] if func_info else 'unknown'
        elif op == 'index':
            return 'i32'
        elif op == 'method_call':
            if node[2] in ('len', 'pop'):
                return 'i32'
            return 'void'
        elif op == 'fn_expr':
            params = node[1]
            body = node[2]
            ret_type = 'void'
            for stmt in body:
                if isinstance(stmt, tuple) and stmt[0] == 'return':
                    ret_type = self._quick_infer_type(stmt[1])
                    break
            return f"fn({','.join(['i32'] * len(params))})->{ret_type}"
        return 'unknown'

    def visit(self, node: Any):
        if node is None:
            return

        if isinstance(node, tuple):
            node_type = node[0]

            if node_type == 'program':
                for top in node[1]:
                    self.visit(top)

            elif node_type == 'func_def':
                self._analyze_func_body(node)

            elif node_type == 'let_decl':
                self.visit_let_decl(node)

            elif node_type == 'return':
                self.visit_return(node)

            elif node_type == 'expr_stmt':
                self.visit_expr(node[1])

            elif node_type == 'if':
                self.visit_if(node)

            elif node_type == 'for_in':
                self.visit_for_in(node)

            elif node_type == 'while':
                self.visit_while(node)

            elif node_type == 'match':
                self.visit_match(node)

            elif node_type in ['add', 'sub', 'mul', 'div', 'eq', 'neq', 'gt', 'lt', 'gte', 'lte']:
                self.visit_binary_op(node)

            elif node_type in ['is_some', 'is_none']:
                self.visit_type_test(node)

            elif node_type == 'call':
                self.visit_call(node)

            elif node_type == 'index':
                self.visit_index(node)

            elif node_type == 'method_call':
                self.visit_method_call(node)

            elif node_type == 'assign':
                self.visit_assign(node)

            else:
                for child in node[1:]:
                    self.visit(child)

        elif isinstance(node, list):
            for item in node:
                self.visit(item)

    # ============ 赋值 ============
    def visit_assign(self, node: Tuple):
        lhs = node[1]
        expr_node = node[2]
        expr_type = self.visit_expr(expr_node)

        if lhs[0] == 'var':
            var_name = lhs[1]
            var_type = self.lookup(var_name)
            if var_type is None:
                self.errors.append(f"错误: 赋值前未声明变量 '{var_name}'")
                return
            if expr_type != var_type:
                self.errors.append(f"错误: 不能将 {expr_type} 赋值给 {var_type} 类型的变量 '{var_name}'")

        elif lhs[0] == 'index':
            obj_type = self.visit_expr(lhs[1])
            idx_type = self.visit_expr(lhs[2])
            if obj_type != 'Vec<i32>':
                self.errors.append(f"错误: 索引赋值要求 Vec<i32>，但得到 {obj_type}")
            if idx_type != 'i32':
                self.errors.append(f"错误: 索引必须是 i32，但得到 {idx_type}")
            if expr_type != 'i32':
                self.errors.append(f"错误: 不能将 {expr_type} 赋值给 Vec<i32> 元素")

        else:
            self.errors.append(f"错误: 不支持的赋值目标")

    # ============ if ============
    def visit_if(self, node: Tuple):
        cond = node[1]
        then_stmts = node[2]
        else_stmts = node[3]
        
        cond_type = self.visit_expr(cond)
        if cond_type != 'bool':
            self.errors.append(f"错误: if 条件必须是 bool，但得到 {cond_type}")
        
        self.enter_scope()
        for stmt in then_stmts:
            self.visit(stmt)
        self.exit_scope()
        
        if else_stmts:
            self.enter_scope()
            for stmt in else_stmts:
                self.visit(stmt)
            self.exit_scope()

    # ============ for_in ============
    def visit_for_in(self, node: Tuple):
        var_name = node[1]
        iterable = node[2]
        body = node[3]
        
        iterable_type = self.visit_expr(iterable)
        if iterable_type != 'Vec<i32>':
            self.errors.append(f"错误: for 迭代对象必须是 Vec<i32>，但得到 {iterable_type}")
        
        self.enter_scope()
        self.declare(var_name, 'i32')
        for stmt in body:
            self.visit(stmt)
        self.exit_scope()

    # ============ while ============
    def visit_while(self, node: Tuple):
        cond = node[1]
        body = node[2]
        
        cond_type = self.visit_expr(cond)
        if cond_type != 'bool':
            self.errors.append(f"错误: while 条件必须是 bool，但得到 {cond_type}")
        
        self.enter_scope()
        for stmt in body:
            self.visit(stmt)
        self.exit_scope()

    # ============ 函数定义 ============
    def _analyze_func_body(self, node: Tuple):
        func_name = node[1]
        params = node[2]
        body = node[3]

        prev_func = self.current_func
        self.current_func = func_name
        self.enter_scope()

        func_info = self.func_table[func_name]
        for i, param in enumerate(params):
            param_type = func_info['params'][i] if i < len(func_info['params']) else 'unknown'
            if param_type == 'unknown':
                param_type = 'i32'
            self.declare(param, param_type)

        for stmt in body:
            self.visit(stmt)

        self.exit_scope()
        self.current_func = prev_func

    # ============ let 声明 ============
    def visit_let_decl(self, node: Tuple):
        var_name = node[1]
        expr_node = node[2]
        expr_type = self.visit_expr(expr_node)
        self.declare(var_name, expr_type)

    # ============ return 语句 ============
    def visit_return(self, node: Tuple):
        # fn_expr 内允许 return
        if self.current_func is None and not self._in_fn_expr:
            self.errors.append("错误: return 语句只能在函数内部使用")
            return

        expr_type = self.visit_expr(node[1])
        
        # 匿名函数不更新 func_table（因为不在其中）
        if self.current_func == '<anonymous>':
            return

        func_info = self.func_table[self.current_func]
        if func_info['return_type'] == 'unknown':
            func_info['return_type'] = expr_type
        elif func_info['return_type'] != expr_type:
            self.errors.append(
                f"错误: 函数 '{self.current_func}' 返回类型不一致，期望 {func_info['return_type']}，实际 {expr_type}"
            )

    # ============ 函数调用 ============
    def visit_call(self, node: Tuple):
        callee_node = node[1]
        args = node[2]

        func_info = None
        func_name = None

        # === 路径 1：通过变量名调用（顶层函数 或 函数变量）===
        if callee_node[0] == 'var':
            func_name = callee_node[1]
            # 先查顶层函数表
            func_info = self.func_table.get(func_name)
            # 再查符号表（函数值变量）
            if func_info is None:
                var_type = self.lookup(func_name)
                if var_type and var_type.startswith('fn('):
                    parsed = self.parse_fn_type(var_type)
                    if parsed:
                        param_types, ret_type = parsed
                        func_info = {'params': list(param_types), 'return_type': ret_type}
                elif var_type == 'unknown':
                    # P1 兜底：高阶函数参数类型未知时，假设为函数，仅警告
                    self.warnings.append(f"警告: 函数参数 '{func_name}' 类型未知，跳过参数检查")
                    return 'unknown'

        # === 路径 2：直接调用匿名函数，如 fn(x){...}(10) ===
        elif callee_node[0] == 'fn_expr':
            params = callee_node[1]
            body = callee_node[2]
            self.enter_scope()
            for p in params:
                self.declare(p, 'i32')
            ret_type = 'void'
            for stmt in body:
                if isinstance(stmt, tuple) and stmt[0] == 'return':
                    ret_type = self.visit_expr(stmt[1])
                    break
            self.exit_scope()
            param_types = ['i32'] * len(params)
            func_info = {'params': param_types, 'return_type': ret_type}
            func_name = '<anonymous>'

        else:
            self.errors.append("错误: 目前只支持直接函数名、变量或匿名函数调用")
            return 'unknown'

        if func_info is None:
            self.errors.append(f"错误: 未定义的函数或函数变量 '{func_name}'")
            return 'unknown'

        # 推断参数类型（仅对 func_table 中的顶层函数有意义）
        if func_name in self.func_table:
            for i, arg in enumerate(args):
                arg_type = self.visit_expr(arg)
                if i < len(func_info['params']) and func_info['params'][i] == 'unknown':
                    func_info['params'][i] = arg_type

        # 参数数量检查
        if len(args) != len(func_info['params']):
            self.errors.append(
                f"错误: 函数 '{func_name}' 期望 {len(func_info['params'])} 个参数，实际 {len(args)} 个"
            )

        # 参数类型检查
        for i, arg in enumerate(args):
            arg_type = self.visit_expr(arg)
            if i < len(func_info['params']) and arg_type != func_info['params'][i] and func_info['params'][i] != 'unknown':
                self.errors.append(
                    f"错误: 函数 '{func_name}' 第 {i+1} 个参数期望 {func_info['params'][i]}，实际 {arg_type}"
                )

        return func_info['return_type']
    
    # ============ 索引访问 ============
    def visit_index(self, node: Tuple):
        obj_expr = node[1]
        idx_expr = node[2]

        obj_type = self.visit_expr(obj_expr)
        idx_type = self.visit_expr(idx_expr)

        if obj_type != 'Vec<i32>':
            self.errors.append(f"错误: 索引访问要求 Vec<i32>，但得到 {obj_type}")

        if idx_type != 'i32':
            self.errors.append(f"错误: 索引必须是 i32，但得到 {idx_type}")

        return 'i32'

    # ============ 方法调用 ============
    def visit_method_call(self, node: Tuple):
        obj_expr = node[1]
        method_name = node[2]
        args = node[3]

        obj_type = self.visit_expr(obj_expr)

        if obj_type != 'Vec<i32>':
            self.errors.append(f"错误: 方法调用要求 Vec<i32>，但得到 {obj_type}")
            return 'unknown'

        vec_methods = {
            'push': (['i32'], 'void'),
            'len': ([], 'i32'),
            'pop': ([], 'i32'),
            'remove': (['i32'], 'void'),
        }

        if method_name not in vec_methods:
            self.errors.append(f"错误: Vec<i32> 没有方法 '{method_name}'")
            return 'unknown'

        expected_params, return_type = vec_methods[method_name]

        if len(args) != len(expected_params):
            self.errors.append(
                f"错误: 方法 '{method_name}' 期望 {len(expected_params)} 个参数，实际 {len(args)} 个"
            )

        for i, arg in enumerate(args):
            arg_type = self.visit_expr(arg)
            if i < len(expected_params) and arg_type != expected_params[i]:
                self.errors.append(
                    f"错误: 方法 '{method_name}' 第 {i+1} 个参数期望 {expected_params[i]}，实际 {arg_type}"
                )

        return return_type

    # ============ match 表达式 ============
    def visit_match(self, node: Tuple):
        scrutinee_name = node[1]
        cases = node[2]

        scrutinee_type = self.lookup(scrutinee_name)
        if scrutinee_type is None:
            self.errors.append(f"错误: 未声明的变量 '{scrutinee_name}'")
            return

        if not scrutinee_type.startswith('Option<'):
            self.errors.append(f"错误: match 要求 Option 类型，但 '{scrutinee_name}' 是 {scrutinee_type}")
            return

        has_some = any(c[0] == 'some_case' for c in cases)
        has_none = any(c[0] == 'none_case' for c in cases)

        if not (has_some and has_none):
            self.errors.append("错误: match 表达式必须同时包含 Some 和 None 分支")

        for case in cases:
            self.visit_case(case, scrutinee_type)

    def visit_case(self, case: Tuple, scrutinee_type: str):
        case_type = case[0]

        if case_type == 'some_case':
            var_name = case[1]
            expr_node = case[2]
            inner_type = scrutinee_type[7:-1] if scrutinee_type.startswith('Option<') else 'unknown'
            self.enter_scope()
            self.declare(var_name, inner_type)
            self.visit_expr(expr_node)
            self.exit_scope()

        elif case_type == 'none_case':
            expr_node = case[1]
            self.visit_expr(expr_node)

    # 扫描函数体 AST，收集自由变量（不在 params 也不在函数体内声明的变量）
    def _collect_free_vars(self, body, params):
        local_vars = set(params)
        free_vars = []

        def scan(node):
            if isinstance(node, tuple):
                op = node[0]
                if op == 'var':
                    name = node[1]
                    if name not in local_vars and name not in free_vars:
                        free_vars.append(name)
                elif op == 'let_decl':
                    scan(node[2])              # 先扫描初始化表达式
                    local_vars.add(node[1])     # 再将变量加入局部
                elif op == 'for_in':
                    scan(node[2])              # 可迭代对象
                    local_vars.add(node[1])     # 循环变量
                    for stmt in node[3]:
                        scan(stmt)
                elif op == 'match':
                    scrutinee = node[1]
                    if scrutinee not in local_vars and scrutinee not in free_vars:
                        free_vars.append(scrutinee)
                    for case in node[2]:
                        if case[0] == 'some_case':
                            saved = case[1] in local_vars
                            local_vars.add(case[1])
                            scan(case[2])
                            if not saved:
                                local_vars.remove(case[1])
                        elif case[0] == 'none_case':
                            scan(case[1])
                elif op == 'fn_expr':
                    # 不深入嵌套 fn_expr，它自己处理自己的捕获
                    pass
                elif op == 'return':
                    scan(node[1])
                elif op == 'expr_stmt':
                    scan(node[1])
                elif op == 'if':
                    scan(node[1])
                    for stmt in node[2]:
                        scan(stmt)
                    for stmt in node[3]:
                        scan(stmt)
                elif op == 'while':
                    scan(node[1])
                    for stmt in node[2]:
                        scan(stmt)
                elif op == 'assign':
                    scan(node[1])
                    scan(node[2])
                else:
                    # 通用递归：二元运算、call、index、method_call 等
                    for child in node[1:]:
                        if isinstance(child, (tuple, list)):
                            scan(child)
            elif isinstance(node, list):
                for item in node:
                    scan(item)

        for stmt in body:
            scan(stmt)
        return free_vars

    # ============ 表达式类型推导 ============
    def visit_expr(self, node: Any) -> str:
        if isinstance(node, tuple):
            node_type = node[0]

            if node_type == 'var':
                name = node[1]
                t = self.lookup(name)
                if t is None:
                    self.errors.append(f"错误: 未声明的变量 '{name}'")
                    return 'unknown'
                # 3.1 移除 P1 限制：允许闭包捕获外部变量
                return t

            elif node_type == 'num':
                return 'i32'

            elif node_type == 'vec_literal':
                for elem in node[1]:
                    elem_type = self.visit_expr(elem)
                    if elem_type != 'i32':
                        self.errors.append(f"错误: 数组元素必须是 i32，但得到 {elem_type}")
                return 'Vec<i32>'

            elif node_type == 'some':
                inner_type = self.visit_expr(node[1])
                return f'Option<{inner_type}>'

            elif node_type == 'none':
                return 'Option<i32>'  # 修复：从 Option<unknown> 改为 Option<i32>

            elif node_type in ['add', 'sub', 'mul', 'div']:
                left_type = self.visit_expr(node[1])
                right_type = self.visit_expr(node[2])
                if left_type != 'i32' or right_type != 'i32':
                    self.errors.append(f"错误: 不能对 {left_type} 和 {right_type} 进行算术运算")
                return 'i32'

            elif node_type in ['eq', 'neq', 'gt', 'lt', 'gte', 'lte']:
                left_type = self.visit_expr(node[1])
                right_type = self.visit_expr(node[2])
                if left_type != right_type:
                    self.warnings.append(f"警告: 比较不同类型 {left_type} 和 {right_type}")
                return 'bool'

            elif node_type in ['is_some', 'is_none']:
                expr_type = self.visit_expr(node[1])
                if not expr_type.startswith('Option<'):
                    self.errors.append(f"错误: {node_type} 只能用于 Option，但得到 {expr_type}")
                return 'bool'

            elif node_type == 'match':
                self.visit_match(node)
                return 'i32'

            elif node_type == 'call':
                return self.visit_call(node)

            elif node_type == 'index':
                return self.visit_index(node)

            elif node_type == 'method_call':
                return self.visit_method_call(node)

            elif node_type == 'assign':
                self.visit_assign(node)
                return 'void'
            
            elif node_type == 'fn_expr':
                params = node[1]
                body = node[2]

                # ===== 3.1 新增：自由变量分析 =====
                free_vars = self._collect_free_vars(body, params)

                # 检查捕获类型约束：只允许 i32
                for var in free_vars:
                    var_type = self.lookup(var)
                    if var_type is None:
                        var_type = self._predeclared.get(var, 'unknown')
                    if var_type != 'i32':
                        self.errors.append(
                            f"错误: 闭包暂只支持捕获 i32 类型变量，'{var}' 类型为 {var_type}"
                        )

                # 存储捕获信息，供 Codegen 阶段使用
                self.fn_expr_captures[id(node)] = free_vars
                # =================================

                # 原有逻辑继续：进入作用域、声明参数、推导返回类型
                self.enter_scope()
                for p in params:
                    self.declare(p, 'i32')
                
                prev_in_fn = self._in_fn_expr
                self._in_fn_expr = True
                
                ret_type = 'void'
                for stmt in body:
                    if isinstance(stmt, tuple) and stmt[0] == 'return':
                        prev_func = self.current_func
                        self.current_func = '<anonymous>'
                        ret_type = self.visit_expr(stmt[1])
                        self.current_func = prev_func
                        break
                
                self._in_fn_expr = prev_in_fn
                self.exit_scope()
                param_types = ['i32'] * len(params)
                return f"fn({','.join(param_types)})->{ret_type}"

        return 'unknown'

    def visit_binary_op(self, node: Tuple):
        self.visit_expr(node)

    def visit_type_test(self, node: Tuple):
        self.visit_expr(node)

    # ============ 错误报告 ============
    def print_errors(self):
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
    from transpiler.src.lexer import RustLikeLexer
    from transpiler.src.parser import RustLikeParser

    test_cases = [
        ("函数作为值", """
            let double = fn(x) { return x * 2; };
            let result = double(10);
        """),

        ("捕获外部变量", """
            let outer = 10;
            let f = fn(x) => outer + x;
            let r = f(5);
        """),
    ]

    lexer = RustLikeLexer()
    parser = RustLikeParser()
    analyzer = SemanticAnalyzer()

    for name, code in test_cases:
        print(f"\n{'='*50}")
        print(f"测试: {name}")
        print(f"{'='*50}")

        try:
            tokens = lexer.tokenize(code)
            ast = parser.parse(tokens)
            analyzer.reset()
            success = analyzer.analyze(ast)
            analyzer.print_errors()
            if success:
                print("通过")
        except Exception as e:
            print(f"解析错误: {e}")