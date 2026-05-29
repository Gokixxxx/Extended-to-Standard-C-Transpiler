"""
语法分析器
"""
from sly import Parser
from transpiler.src.lexer import RustLikeLexer
from typing import Any
_: Any

class RustLikeParser(Parser):
    tokens = RustLikeLexer.tokens
    expect = 8

    precedence = (
        ('right', 'EQ'),
        ('right', 'FAT_ARROW'),
        ('left', 'EQEQ', 'NEQ'),
        ('left', 'GT', 'LT', 'GTE', 'LTE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('left', 'LPAREN', 'LBRACKET', 'DOT', 'IS_SOME', 'IS_NONE'),
    )
    
    start = 'program'
    
    # ==================== 程序结构 ====================
    @_('top_level_list')
    def program(self, p):
        return ('program', p.top_level_list)
    
    @_('top_level')
    def top_level_list(self, p):
        return [p.top_level]
    
    @_('top_level_list top_level')
    def top_level_list(self, p):
        return p.top_level_list + [p.top_level]
    
    @_('func_def')
    def top_level(self, p):
        return p.func_def
    
    @_('statement')
    def top_level(self, p):
        return p.statement
    
    @_('struct_def')
    def top_level(self, p):
        return p.struct_def
    
    @_('impl_def')
    def top_level(self, p):
        return p.impl_def
    
    # ==================== 函数定义（独立参数列表，与 Lambda 隔离）====================
    @_('FN IDENTIFIER LPAREN func_params RPAREN LBRACE statements RBRACE')
    def func_def(self, p):
        return ('func_def', p.IDENTIFIER, p.func_params, p.statements)
    
    @_('FN IDENTIFIER LPAREN RPAREN LBRACE statements RBRACE')
    def func_def(self, p):
        return ('func_def', p.IDENTIFIER, [], p.statements)
    
    @_('IDENTIFIER')
    def func_params(self, p):
        return [p.IDENTIFIER]
    
    @_('func_params COMMA IDENTIFIER')
    def func_params(self, p):
        return p.func_params + [p.IDENTIFIER]
    
    # ==================== 语句块 ====================
    @_('statement')
    def statements(self, p):
        return [p.statement]
    
    @_('statements statement')
    def statements(self, p):
        return p.statements + [p.statement]
    
    # ==================== 语句 ====================
    @_('LET IDENTIFIER EQ expr SEMI')
    def statement(self, p):
        return ('let_decl', p.IDENTIFIER, p.expr)
    
    @_('RETURN expr SEMI')
    def statement(self, p):
        return ('return', p.expr)
    
    @_('expr SEMI')
    def statement(self, p):
        return ('expr_stmt', p.expr)
    
    @_('IF expr LBRACE statements RBRACE')
    def statement(self, p):
        return ('if', p.expr, p.statements, [])
    
    @_('IF expr LBRACE statements RBRACE ELSE LBRACE statements RBRACE')
    def statement(self, p):
        return ('if', p.expr, p.statements0, p.statements1)
    
    @_('FOR IDENTIFIER IN expr LBRACE statements RBRACE')
    def statement(self, p):
        return ('for_in', p.IDENTIFIER, p.expr, p.statements)
    
    @_('WHILE expr LBRACE statements RBRACE')
    def statement(self, p):
        return ('while', p.expr, p.statements)
    
    # ==================== 表达式层级 ====================
    
    # --- atom：最基础、无后缀的表达式单元 ---
    @_('IDENTIFIER')
    def atom(self, p):
        return ('var', p.IDENTIFIER)
    
    @_('NUMBER')
    def atom(self, p):
        return ('num', int(p.NUMBER))
    
    @_('SOME LPAREN expr RPAREN')
    def atom(self, p):
        return ('some', p.expr)
    
    @_('NONE')
    def atom(self, p):
        return ('none',)
    
    @_('IDENTIFIER LBRACE field_init_list RBRACE')
    def atom(self, p):
        return ('struct_literal', p.IDENTIFIER, p.field_init_list)

    @_('IDENTIFIER LBRACE RBRACE')
    def atom(self, p):
        return ('struct_literal', p.IDENTIFIER, [])
    
    @_('LPAREN expr RPAREN')
    def atom(self, p):
        return p.expr
    
    @_('LBRACKET expr_list RBRACKET')
    def atom(self, p):
        return ('vec_literal', p.expr_list)
    
    @_('LBRACKET RBRACKET')
    def atom(self, p):
        return ('vec_literal', [])
    
    # --- Lambda / 匿名函数 ---
    @_('FN IDENTIFIER FAT_ARROW expr')
    def lambda_or_fn(self, p):
        return ('fn_expr', [p.IDENTIFIER], [('return', p.expr)])
    
    @_('FN LPAREN param_list RPAREN FAT_ARROW expr')
    def lambda_or_fn(self, p):
        return ('fn_expr', p.param_list, [('return', p.expr)])
    
    @_('FN LPAREN RPAREN FAT_ARROW expr')
    def lambda_or_fn(self, p):
        return ('fn_expr', [], [('return', p.expr)])
    
    @_('FN LPAREN param_list RPAREN LBRACE statements RBRACE')
    def lambda_or_fn(self, p):
        return ('fn_expr', p.param_list, p.statements)
    
    @_('FN LPAREN RPAREN LBRACE statements RBRACE')
    def lambda_or_fn(self, p):
        return ('fn_expr', [], p.statements)
    
    # --- 参数列表（仅用于 Lambda / 匿名函数，与 func_params 隔离）---
    @_('IDENTIFIER')
    def param_list(self, p):
        return [p.IDENTIFIER]
    
    @_('param_list COMMA IDENTIFIER')
    def param_list(self, p):
        return p.param_list + [p.IDENTIFIER]
    
    # --- postfix：atom / lambda + 任意后缀操作 ---
    @_('atom')
    def postfix(self, p):
        return p.atom
    
    @_('lambda_or_fn')
    def postfix(self, p):
        return p.lambda_or_fn
    
    @_('postfix DOT IDENTIFIER')
    def postfix(self, p):
        return ('field_access', p.postfix, p.IDENTIFIER)
    
    @_('postfix LPAREN arg_list RPAREN')
    def postfix(self, p):
        return ('call', p.postfix, p.arg_list)
    
    @_('postfix LPAREN RPAREN')
    def postfix(self, p):
        return ('call', p.postfix, [])
    
    @_('postfix LBRACKET expr RBRACKET')
    def postfix(self, p):
        return ('index', p.postfix, p.expr)
    
    @_('postfix DOT IDENTIFIER LPAREN arg_list RPAREN')
    def postfix(self, p):
        return ('method_call', p.postfix, p.IDENTIFIER, p.arg_list)
    
    @_('postfix DOT IDENTIFIER LPAREN RPAREN')
    def postfix(self, p):
        return ('method_call', p.postfix, p.IDENTIFIER, [])
    
    # is_some / is_none 后缀风格：x.is_some
    @_('postfix DOT IS_SOME')
    def postfix(self, p):
        return ('is_some', p.postfix)
    
    @_('postfix DOT IS_NONE')
    def postfix(self, p):
        return ('is_none', p.postfix)
    
    @_('postfix IS_SOME')
    def postfix(self, p):
        return ('is_some', p.postfix)

    @_('postfix IS_NONE')
    def postfix(self, p):
        return ('is_none', p.postfix)

    # --- 表达式列表 & 参数列表 ---
    @_('expr')
    def expr_list(self, p):
        return [p.expr]
    
    @_('expr_list COMMA expr')
    def expr_list(self, p):
        return p.expr_list + [p.expr]
    
    @_('expr')
    def arg_list(self, p):
        return [p.expr]
    
    @_('arg_list COMMA expr')
    def arg_list(self, p):
        return p.arg_list + [p.expr]
    
    # --- expr：顶层表达式（precedence 处理优先级）---
    
    # 默认规则：expr 可以是 postfix（最低优先级入口）
    @_('postfix')
    def expr(self, p):
        return p.postfix
    
    # 算术运算：右操作数改为 expr，让 precedence 处理优先级
    @_('expr PLUS expr')
    def expr(self, p):
        return ('add', p.expr0, p.expr1)
    
    @_('expr MINUS expr')
    def expr(self, p):
        return ('sub', p.expr0, p.expr1)
    
    @_('expr TIMES expr')
    def expr(self, p):
        return ('mul', p.expr0, p.expr1)
    
    @_('expr DIVIDE expr')
    def expr(self, p):
        return ('div', p.expr0, p.expr1)
    
    # 比较运算
    @_('expr EQEQ expr')
    def expr(self, p):
        return ('eq', p.expr0, p.expr1)
    
    @_('expr NEQ expr')
    def expr(self, p):
        return ('neq', p.expr0, p.expr1)
    
    @_('expr GT expr')
    def expr(self, p):
        return ('gt', p.expr0, p.expr1)
    
    @_('expr LT expr')
    def expr(self, p):
        return ('lt', p.expr0, p.expr1)
    
    @_('expr GTE expr')
    def expr(self, p):
        return ('gte', p.expr0, p.expr1)
    
    @_('expr LTE expr')
    def expr(self, p):
        return ('lte', p.expr0, p.expr1)
    
    # 赋值（最低优先级，右结合）
    @_('postfix EQ expr')
    def expr(self, p):
        return ('assign', p.postfix, p.expr)
    
    # Match 表达式
    @_('MATCH IDENTIFIER LBRACE match_cases RBRACE')
    def expr(self, p):
        return ('match', p.IDENTIFIER, p.match_cases)
    
    # is_some / is_none 前缀风格：is_some(x)
    @_('IS_SOME LPAREN expr RPAREN')
    def expr(self, p):
        return ('is_some', p.expr)
    
    @_('IS_NONE LPAREN expr RPAREN')
    def expr(self, p):
        return ('is_none', p.expr)
    
    # ==================== Match 分支 ====================
    @_('match_case')
    def match_cases(self, p):
        return [p.match_case]
    
    @_('match_cases COMMA match_case')
    def match_cases(self, p):
        return p.match_cases + [p.match_case]
    
    @_('SOME LPAREN IDENTIFIER RPAREN FAT_ARROW expr')
    def match_case(self, p):
        return ('some_case', p.IDENTIFIER, p.expr)
    
    @_('NONE FAT_ARROW expr')
    def match_case(self, p):
        return ('none_case', p.expr)
    
    # ===== struct_def / field_list / field 规则 =====
    @_('STRUCT IDENTIFIER LBRACE field_list RBRACE')
    def struct_def(self, p):
        return ('struct_def', p.IDENTIFIER, p.field_list)

    @_('STRUCT IDENTIFIER LBRACE RBRACE')
    def struct_def(self, p):
        return ('struct_def', p.IDENTIFIER, [])

    @_('field')
    def field_list(self, p):
        return [p.field]

    @_('field_list COMMA field')
    def field_list(self, p):
        return p.field_list + [p.field]

    @_('IDENTIFIER COLON IDENTIFIER')
    def field(self, p):
        return ('field', p.IDENTIFIER0, p.IDENTIFIER1)

    # ===== impl_def / method_list / method_def / self_param 规则 =====
    @_('IMPL IDENTIFIER LBRACE method_list RBRACE')
    def impl_def(self, p):
        return ('impl_def', p.IDENTIFIER, p.method_list)

    @_('method_def')
    def method_list(self, p):
        return [p.method_def]

    @_('method_list method_def')
    def method_list(self, p):
        return p.method_list + [p.method_def]

    @_('FN IDENTIFIER LPAREN self_param RPAREN LBRACE statements RBRACE')
    def method_def(self, p):
        return ('method_def', p.IDENTIFIER, [p.self_param], p.statements)

    @_('FN IDENTIFIER LPAREN self_param COMMA func_params RPAREN LBRACE statements RBRACE')
    def method_def(self, p):
        return ('method_def', p.IDENTIFIER, [p.self_param] + p.func_params, p.statements)

    @_('AMPERSAND IDENTIFIER')
    def self_param(self, p):
        return ('&', p.IDENTIFIER)
    

    # ===== field_init_list / field_init 规则=====
    @_('field_init')
    def field_init_list(self, p):
        return [p.field_init]

    @_('field_init_list COMMA field_init')
    def field_init_list(self, p):
        return p.field_init_list + [p.field_init]

    @_('IDENTIFIER COLON expr')
    def field_init(self, p):
        return ('field_init', p.IDENTIFIER, p.expr)

if __name__ == '__main__':
    from transpiler.src.lexer import RustLikeLexer
    lexer = RustLikeLexer()
    parser = RustLikeParser()
    
    code = '''
    struct Rectangle {
        width: i32,
        height: i32
    }

    impl Rectangle {
        fn area(&self) {
            return self.width * self.height;
        }
    }

    let rect1 = Rectangle { width: 30, height: 50 };
    let a = rect1.area();
    let w = rect1.width;
    '''
    
    print("Parsing code:")
    print(code)
    print("\nParse tree:")
    
    try:
        result = parser.parse(lexer.tokenize(code))
        import pprint
        pprint.pprint(result)
    except Exception as e:
        print(f"Error: {e}")