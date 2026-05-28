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
        self._fn_expr_depth = 0   # fn_expr 嵌套深度
        self.moved_vars = set()   # 记录已被移动（move）的闭包变量
        self.captured_closure_vars = set()   # 有捕获闭包变量名

    def reset(self):
        self.symbol_table = [{}]
        self.func_table = {}
        self.errors = []
        self.warnings = []
        self.current_func = None
        self.deferred_funcs = []
        self._predeclared = {}
        self.fn_expr_captures.clear()
        self._fn_expr_depth = 0
        self.moved_vars.clear()
        self.captured_closure_vars.clear()

    # === 4.14限制 ===
    def _is_local_var(self, name: str) -> bool:
        """检查变量是否在当前最内层作用域中声明（参数或局部变量）"""
        return bool(self.symbol_table and name in self.symbol_table[-1])

    def _is_captured_closure_var_ref(self, node) -> bool:
        """判断 AST 节点是否是『已绑定到有捕获闭包值的变量引用』"""
        if isinstance(node, tuple) and node[0] == 'var':
            var_name = node[1]
            # 如果是当前作用域的局部变量（参数或本作用域 let），不触发 move
            if self._is_local_var(var_name):
                return False
            return var_name in self.captured_closure_vars
        return False

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
                        'param_names': list(params),   # 新增：记录参数名顺序
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
        if not type_str or not type_str.startswith('fn('):
            return None
        
        # 找与 "fn(" 匹配的 ")"，维护括号深度
        depth = 1
        i = 3  # 跳过前缀 "fn("
        while i < len(type_str) and depth > 0:
            if type_str[i] == '(':
                depth += 1
            elif type_str[i] == ')':
                depth -= 1
            i += 1
        
        # i 现在指向匹配 ')' 的下一个字符
        if i >= len(type_str) or type_str[i:i+2] != '->':
            return None
        
        params_str = type_str[3:i-1]   # i-1 是 ')' 的位置
        ret_type   = type_str[i+2:]
        
        # 解析参数列表（支持嵌套括号中的逗号）
        params = []
        depth = 0
        current = ''
        for ch in params_str:
            if ch == '(':
                depth += 1
                current += ch
            elif ch == ')':
                depth -= 1
                current += ch
            elif ch == ',' and depth == 0:
                if current.strip():
                    params.append(current.strip())
                current = ''
            else:
                current += ch
        if current.strip():
            params.append(current.strip())
        
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

            # 4.14：若右侧是闭包变量，标记源变量已被移动
            if self._is_captured_closure_var_ref(expr_node):
                src_name = expr_node[1]
                self.moved_vars.add(src_name)

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
                param_type = 'fn_unknown'  # 保持未知，标记为"待推断"
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

        # 判断本变量是否绑定到有捕获闭包（直接字面量 或 调用返回）
        if isinstance(expr_node, tuple) and expr_node[0] == 'fn_expr':
            # 直接绑定 fn_expr 字面量：有捕获才加入
            if (id(expr_node) in self.fn_expr_captures 
                    and self.fn_expr_captures[id(expr_node)]):
                self.captured_closure_vars.add(var_name)
        elif isinstance(expr_type, str) and expr_type.startswith('fn('):
            # 通过调用/其他表达式获得函数类型：保守假设为有捕获闭包
            # （如 add(3) 返回的闭包，make_adder(5) 返回的闭包）
            self.captured_closure_vars.add(var_name)

        # 4.14：若右侧是有捕获闭包变量，标记源变量已被移动
        if self._is_captured_closure_var_ref(expr_node):
            src_name = expr_node[1]
            self.moved_vars.add(src_name)

    # ============ return 语句 ============
    def visit_return(self, node: Tuple):
        # fn_expr 内允许 return
        if self.current_func is None and not self._in_fn_expr:
            self.errors.append("错误: return 语句只能在函数内部使用")
            return

        expr_node = node[1]
        expr_type = self.visit_expr(node[1])

        # 4.14：若返回的是闭包变量，标记为已移动
        if self._is_captured_closure_var_ref(expr_node):
            src_name = expr_node[1]
            self.moved_vars.add(src_name)
        
        # 匿名函数不更新 func_table（因为不在其中）
        if self.current_func == '<anonymous>':
            return
        
        # 补全当前函数参数中 fn_unknown 的返回类型
        if isinstance(node[1], tuple) and node[1][0] == 'call':
            callee_node = node[1][1]
            if callee_node[0] == 'var':
                callee_name = callee_node[1]
                callee_type = self.lookup(callee_name)
                if isinstance(callee_type, str) and callee_type.startswith('fn(') and '->unknown' in callee_type:
                    # 提取参数部分
                    arrow_idx = callee_type.find(')->')
                    params_part = callee_type[3:arrow_idx]
                    new_type = f"fn({params_part})->{expr_type}"
                    self.declare(callee_name, new_type, is_shadowing_allowed=True)
                    if self.current_func and self.current_func in self.func_table:
                        func_info = self.func_table[self.current_func]
                        param_names = func_info.get('param_names', [])
                        if callee_name in param_names:
                            idx = param_names.index(callee_name)
                            func_info['params'][idx] = new_type

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
        
        callee_type = self.visit_expr(callee_node)

        # 重新 lookup，可能已被其他调用或 return 补全
        if isinstance(callee_type, str) and callee_type.startswith('fn(') and '->unknown' in callee_type:
            if callee_node[0] == 'var':
                refreshed = self.lookup(callee_node[1])
                if refreshed and refreshed != callee_type and isinstance(refreshed, str) and refreshed.startswith('fn('):
                    callee_type = refreshed

        # 反向推断：如果 callee 是 fn_unknown，根据本次调用推断参数类型
        if callee_type == 'fn_unknown' and callee_node[0] == 'var':
            func_name = callee_node[1]
            # 推断实参类型
            inferred_params = []
            for arg in args:
                arg_type = self.visit_expr(arg)
                inferred_params.append(arg_type)
            # 返回类型暂时 unknown，留待 return 语句推断
            inferred_type = f"fn({','.join(inferred_params)})->unknown"
            # 更新符号表（允许 shadowing 覆盖 fn_unknown）
            self.declare(func_name, inferred_type, is_shadowing_allowed=True)
            callee_type = inferred_type
            if self.current_func and self.current_func in self.func_table:
                func_info = self.func_table[self.current_func]
                param_names = func_info.get('param_names', [])
                if func_name in param_names:
                    idx = param_names.index(func_name)
                    func_info['params'][idx] = inferred_type
        
        if not isinstance(callee_type, str) or not callee_type.startswith('fn('):
            if callee_type != 'unknown':
                self.errors.append(f"错误: callee 不是函数类型，而是 {callee_type}")
            return 'unknown'
        
        parsed = self.parse_fn_type(callee_type)
        if not parsed:
            self.warnings.append(f"警告: 无法解析函数类型 {callee_type}")
            return 'unknown'
        
        param_types, ret_type = parsed
        
        # 参数数量检查
        if len(args) != len(param_types):
            self.errors.append(
                f"错误: 函数期望 {len(param_types)} 个参数，实际 {len(args)} 个"
            )
        
        # 参数类型检查
        for i, arg in enumerate(args):
            arg_type = self.visit_expr(arg)
            if i < len(param_types) and arg_type != param_types[i]:
                expected = param_types[i]
                if expected == 'unknown':
                    continue
                # 允许 fn(...)->unknown 与实际函数类型暂时兼容（返回类型待推断）
                if isinstance(expected, str) and expected.startswith('fn(') and '->unknown' in expected:
                    if isinstance(arg_type, str) and arg_type.startswith('fn('):
                        parsed_expected = self.parse_fn_type(expected)
                        parsed_actual = self.parse_fn_type(arg_type)
                        if parsed_expected and parsed_actual and parsed_expected[0] == parsed_actual[0]:
                            continue
                self.errors.append(
                    f"错误: 函数第 {i+1} 个参数期望 {expected}，实际 {arg_type}"
                )
        
        return ret_type
    
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
                    # 递归收集内层自由变量，合并到当前层
                    inner_params = node[1]
                    inner_body  = node[2]
                    inner_free = self._collect_free_vars(inner_body, inner_params)
                    for var in inner_free:
                        if var not in local_vars and var not in free_vars:
                            free_vars.append(var)
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

                # 4.14：检查是否已被移动
                if not self._is_local_var(name) and name in self.moved_vars:
                    self.errors.append(f"错误: 变量 '{name}' 已被移动，不能再次使用")
                    return 'unknown'

                t = self.lookup(name)
                if t is None:
                    # fallback 查命名函数表
                    func_info = self.func_table.get(name)
                    if func_info:
                        params = func_info.get('params', [])
                        ret = func_info.get('return_type', 'unknown')
                        t = f"fn({','.join(params)})->{ret}"
                    else:
                        self.errors.append(f"错误: 未声明的变量 '{name}'")
                        return 'unknown'
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
                return 'Option<i32>'

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

                # 自由变量分析
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
                self._fn_expr_depth += 1        # 进入内层
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
                    else:
                        self.visit(stmt)  # 处理 let_decl、if、while 等
                
                self._in_fn_expr = prev_in_fn
                self.exit_scope()
                self._fn_expr_depth -= 1        # 退出内层
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
        ("解除嵌套闭包的语义限制", """
        let x = 1;
        let add = fn(a) => fn(b) => x + a + b;
        let result = add(3)(4);
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

    # 临时验证 Step 1
    code = """
    let x = 1;
    let add = fn(a) => fn(b) => x + a + b;
    """
    tokens = lexer.tokenize(code)
    ast = parser.parse(tokens)
    analyzer.reset()
    analyzer.analyze(ast)
    
    # 打印所有 fn_expr 的捕获列表
    for node_id, caps in analyzer.fn_expr_captures.items():
        print(f"fn_expr {node_id}: captures {caps}")