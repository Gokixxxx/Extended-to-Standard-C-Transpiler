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

    def reset(self):
        self.symbol_table = [{}]
        self.func_table = {}
        self.errors = []
        self.warnings = []
        self.current_func = None

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
        self.visit(ast)
        return len(self.errors) == 0

    def visit(self, node: Any):
        if node is None:
            return

        if isinstance(node, tuple):
            node_type = node[0]

            if node_type == 'program':
                for top in node[1]:
                    self.visit(top)

            elif node_type == 'func_def':
                self.visit_func_def(node)

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
        var_name = node[1]
        expr_node = node[2]
        
        var_type = self.lookup(var_name)
        if var_type is None:
            self.errors.append(f"错误: 赋值前未声明变量 '{var_name}'")
            return
        
        expr_type = self.visit_expr(expr_node)
        if expr_type != var_type:
            self.errors.append(f"错误: 不能将 {expr_type} 赋值给 {var_type} 类型的变量 '{var_name}'")

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
    def visit_func_def(self, node: Tuple):
        func_name = node[1]
        params = node[2]
        body = node[3]

        param_types = ['i32'] * len(params)
        self.func_table[func_name] = {
            'params': param_types,
            'return_type': 'unknown'
        }

        prev_func = self.current_func
        self.current_func = func_name
        self.enter_scope()

        for param in params:
            self.declare(param, 'i32')

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
        if self.current_func is None:
            self.errors.append("错误: return 语句只能在函数内部使用")
            return

        expr_type = self.visit_expr(node[1])
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

        if callee_node[0] != 'var':
            self.errors.append("错误: 目前只支持直接函数名调用")
            return 'unknown'

        func_name = callee_node[1]
        func_info = self.func_table.get(func_name)

        if func_info is None:
            self.errors.append(f"错误: 未定义的函数 '{func_name}'")
            return 'unknown'

        if len(args) != len(func_info['params']):
            self.errors.append(
                f"错误: 函数 '{func_name}' 期望 {len(func_info['params'])} 个参数，实际 {len(args)} 个"
            )

        for i, arg in enumerate(args):
            arg_type = self.visit_expr(arg)
            if i < len(func_info['params']) and arg_type != func_info['params'][i]:
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
                return 'Option<unknown>'

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
        ("基本函数", """
            fn add(a, b) {
                return a + b;
            }
            let x = add(1, 2);
        """),

        ("数组操作", """
            let v = [1, 2, 3];
            v.push(16);
            let k = v[1];
            let n = v.len();
        """),

        ("if/else", """
            let x = 5;
            if x > 0 {
                x = x - 1;
            } else {
                x = x + 1;
            }
        """),

        ("for_in", """
            let arr = [1, 2, 3];
            for x in arr {
                x = x + 1;
            }
        """),

        ("while", """
            let i = 0;
            while i < 10 {
                i = i + 1;
            }
        """),

        ("Option + 函数", """
            fn make_some(x) {
                return Some(x);
            }
            let y = make_some(10);
            let z = match y { Some(v) => v + 1, None => 0 };
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