"""
语法分析器（重构版 — 消除 shift/reduce 冲突）
"""
from sly import Parser
from transpiler.src.lexer import RustLikeLexer
from typing import Any
_: Any

class RustLikeParser(Parser):
    tokens = RustLikeLexer.tokens
    expect = 6  # 允许 6 个 shift/reduce 冲突（is_some/is_none 前缀/后缀/属性写法重叠）

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
    
    # ==================== 表达式层级重构 ====================
    
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
    
    @_('LPAREN expr RPAREN')
    def atom(self, p):
        return p.expr
    
    @_('LBRACKET expr_list RBRACKET')
    def atom(self, p):
        return ('vec_literal', p.expr_list)
    
    @_('LBRACKET RBRACKET')
    def atom(self, p):
        return ('vec_literal', [])
    
    # --- Lambda / 匿名函数（直接作为 postfix 的一种）---
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
    
    # --- expr：中缀运算（左递归）---
    @_('postfix')
    def expr(self, p):
        return p.postfix
    
    @_('expr PLUS postfix')
    def expr(self, p):
        return ('add', p.expr, p.postfix)
    
    @_('expr MINUS postfix')
    def expr(self, p):
        return ('sub', p.expr, p.postfix)
    
    @_('expr TIMES postfix')
    def expr(self, p):
        return ('mul', p.expr, p.postfix)
    
    @_('expr DIVIDE postfix')
    def expr(self, p):
        return ('div', p.expr, p.postfix)
    
    @_('expr EQEQ postfix')
    def expr(self, p):
        return ('eq', p.expr, p.postfix)
    
    @_('expr NEQ postfix')
    def expr(self, p):
        return ('neq', p.expr, p.postfix)
    
    @_('expr GT postfix')
    def expr(self, p):
        return ('gt', p.expr, p.postfix)
    
    @_('expr LT postfix')
    def expr(self, p):
        return ('lt', p.expr, p.postfix)
    
    @_('expr GTE postfix')
    def expr(self, p):
        return ('gte', p.expr, p.postfix)
    
    @_('expr LTE postfix')
    def expr(self, p):
        return ('lte', p.expr, p.postfix)
    
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

if __name__ == '__main__':
    from transpiler.src.lexer import RustLikeLexer
    lexer = RustLikeLexer()
    parser = RustLikeParser()
    
    code ='''
    let add = fn(x, y) => x + y;
    let result = add(3, 4);

    let greet = fn() => 42;
    let g = greet();
    
    let v = [1, 2, 3];
    v.push(10);
    let x = v[1];
    v[1] = 5;
    
    let opt = Some(10);
    let b = opt.is_some;
    let c = is_some(opt);
    let d = opt is_some;
    
    let y = match opt {
        Some(v) => v + 1,
        None => 0
    };
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