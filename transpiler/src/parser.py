"""
语法分析器
"""
from sly import Parser
from transpiler.src.lexer import RustLikeLexer
from typing import Any
_: Any

class RustLikeParser(Parser):
    tokens = RustLikeLexer.tokens
    
    start = 'program'
    
    # ==================== 程序结构 ====================
    @_('statements')
    def program(self, p):
        return ('program', p.statements)
    
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
    
    # ==================== 表达式 ====================
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
    
    # ==================== 比较运算符 ====================
    @_('expr EQEQ term')
    def expr(self, p):
        return ('eq', p.expr, p.term)
    
    @_('expr NEQ term')
    def expr(self, p):
        return ('neq', p.expr, p.term)
    
    # ==================== 类型测试 ====================
    @_('expr IS_SOME')
    def expr(self, p):
        return ('is_some', p.expr)
    
    @_('expr IS_NONE')
    def expr(self, p):
        return ('is_none', p.expr)

if __name__ == '__main__':
    lexer = RustLikeLexer()
    parser = RustLikeParser()
    
    code ='''let x = Some(5); 
    let y = match x { Some(v) => v + 1, None => 0 };
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