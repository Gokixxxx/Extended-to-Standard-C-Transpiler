"""
语法分析器
"""
from sly import Parser
from transpiler.src.lexer import RustLikeLexer
from typing import Any
_: Any

class RustLikeParser(Parser):
    tokens = RustLikeLexer.tokens

    # 调试
    # debugfile = 'parser.out'
    
    # 优先级声明：从低到高
    precedence = (
        ('right', 'EQ'),
        ('right', 'FAT_ARROW'),
        ('left', 'EQEQ', 'NEQ'),
        ('left', 'GT', 'LT', 'GTE', 'LTE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
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
    
    # ==================== Lambda 表达式====================
    @_('FN IDENTIFIER FAT_ARROW expr')
    def lambda_expr(self, p):
        # fn x => expr  等价于  fn(x) { return expr; }
        return ('fn_expr', [p.IDENTIFIER], [('return', p.expr)])
    
    @_('FN LPAREN param_list RPAREN FAT_ARROW expr')
    def lambda_expr(self, p):
        # fn(x, y) => expr  脱糖为  fn(x, y) { return expr; }
        return ('fn_expr', p.param_list, [('return', p.expr)])

    @_('FN LPAREN RPAREN FAT_ARROW expr')
    def lambda_expr(self, p):
        # fn() => expr  脱糖为  fn() { return expr; }
        return ('fn_expr', [], [('return', p.expr)])
    
    # ==================== 函数定义 ====================
    @_('FN IDENTIFIER LPAREN param_list RPAREN LBRACE statements RBRACE')
    def func_def(self, p):
        return ('func_def', p.IDENTIFIER, p.param_list, p.statements)
    
    @_('FN IDENTIFIER LPAREN RPAREN LBRACE statements RBRACE')
    def func_def(self, p):
        return ('func_def', p.IDENTIFIER, [], p.statements)
    
    @_('IDENTIFIER')
    def param_list(self, p):
        return [p.IDENTIFIER]
    
    @_('param_list COMMA IDENTIFIER')
    def param_list(self, p):
        return p.param_list + [p.IDENTIFIER]
    
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
    
    # ==================== 表达式 ====================
    @_('primary EQ expr')
    def expr(self, p):
        return ('assign', p.primary, p.expr)
    
    @_('match_expr')
    def expr(self, p):
        return p.match_expr
    
    @_('term')
    def expr(self, p):
        return p.term
    
    @_('expr PLUS term')
    def expr(self, p):
        return ('add', p.expr, p.term)
    
    @_('expr MINUS term')
    def expr(self, p):
        return ('sub', p.expr, p.term)
    
    @_('expr EQEQ term')
    def expr(self, p):
        return ('eq', p.expr, p.term)
    
    @_('expr NEQ term')
    def expr(self, p):
        return ('neq', p.expr, p.term)
    
    @_('expr GT term')
    def expr(self, p):
        return ('gt', p.expr, p.term)
    
    @_('expr LT term')
    def expr(self, p):
        return ('lt', p.expr, p.term)
    
    @_('expr GTE term')
    def expr(self, p):
        return ('gte', p.expr, p.term)
    
    @_('expr LTE term')
    def expr(self, p):
        return ('lte', p.expr, p.term)
    
    @_('term TIMES factor')
    def term(self, p):
        return ('mul', p.term, p.factor)
    
    @_('term DIVIDE factor')
    def term(self, p):
        return ('div', p.term, p.factor)
    
    @_('factor')
    def term(self, p):
        return p.factor
    
    @_('primary')
    def factor(self, p):
        return p.primary
    
    # 函数调用风格：is_some(x), is_none(x)
    @_('IS_SOME LPAREN expr RPAREN')
    def primary(self, p):
        return ('is_some', p.expr)

    @_('IS_NONE LPAREN expr RPAREN')
    def primary(self, p):
        return ('is_none', p.expr)

    # 属性访问风格：x.is_some, x.is_none
    @_('primary DOT IS_SOME')
    def primary(self, p):
        return ('is_some', p.primary)

    @_('primary DOT IS_NONE')
    def primary(self, p):
        return ('is_none', p.primary)
    
    # ==================== 数组字面量 ====================
    @_('LBRACKET expr_list RBRACKET')
    def primary(self, p):
        return ('vec_literal', p.expr_list)
    
    @_('LBRACKET RBRACKET')
    def primary(self, p):
        return ('vec_literal', [])
    
    @_('expr')
    def expr_list(self, p):
        return [p.expr]
    
    @_('expr_list COMMA expr')
    def expr_list(self, p):
        return p.expr_list + [p.expr]
    
    # ==================== 索引访问 & 方法调用 ====================
    @_('primary LBRACKET expr RBRACKET')
    def primary(self, p):
        return ('index', p.primary, p.expr)
    
    @_('primary DOT IDENTIFIER LPAREN arg_list RPAREN')
    def primary(self, p):
        return ('method_call', p.primary, p.IDENTIFIER, p.arg_list)
    
    @_('primary DOT IDENTIFIER LPAREN RPAREN')
    def primary(self, p):
        return ('method_call', p.primary, p.IDENTIFIER, [])
    
    # ==================== 函数调用（作为 primary 的一种）====================
    @_('primary LPAREN arg_list RPAREN')
    def primary(self, p):
        return ('call', p.primary, p.arg_list)
    
    @_('primary LPAREN RPAREN')
    def primary(self, p):
        return ('call', p.primary, [])
    
    @_('expr')
    def arg_list(self, p):
        return [p.expr]
    
    @_('arg_list COMMA expr')
    def arg_list(self, p):
        return p.arg_list + [p.expr]
    
    # ==================== Match 表达式 ====================
    @_('MATCH IDENTIFIER LBRACE match_cases RBRACE')
    def match_expr(self, p):
        return ('match', p.IDENTIFIER, p.match_cases)
    
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
    
    # ==================== 基本表达式 ====================
    @_('IDENTIFIER')
    def primary(self, p):
        return ('var', p.IDENTIFIER)
    
    @_('NUMBER')
    def primary(self, p):
        return ('num', int(p.NUMBER))
    
    @_('SOME LPAREN expr RPAREN')
    def primary(self, p):
        return ('some', p.expr)
    
    @_('NONE')
    def primary(self, p):
        return ('none',)
    
    @_('LPAREN expr RPAREN')
    def primary(self, p):
        return p.expr
    
    # Lambda 归入 primary
    @_('lambda_expr')
    def primary(self, p):
        return p.lambda_expr
    
    # ==================== 类型测试 ====================
    @_('expr IS_SOME')
    def expr(self, p):
        return ('is_some', p.expr)
    
    @_('expr IS_NONE')
    def expr(self, p):
        return ('is_none', p.expr)
    
    # ==================== 匿名函数表达式 ====================
    @_('FN LPAREN param_list RPAREN LBRACE statements RBRACE')
    def primary(self, p):
        return ('fn_expr', p.param_list, p.statements)

    @_('FN LPAREN RPAREN LBRACE statements RBRACE')
    def primary(self, p):
        return ('fn_expr', [], p.statements)

if __name__ == '__main__':
    lexer = RustLikeLexer()
    parser = RustLikeParser()
    
    code ='''
    let add = fn(x, y) => x + y;
    let result = add(3, 4);

    let greet = fn() => 42;
    let g = greet(); 
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