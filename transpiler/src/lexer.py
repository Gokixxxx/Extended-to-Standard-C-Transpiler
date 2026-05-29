"""
词法分析器
"""
from sly import Lexer
from typing import Any
_: Any

class RustLikeLexer(Lexer):
    tokens = {'LET', 'FN', 'RETURN', 'IF', 'ELSE', 'FOR', 'IN', 'WHILE',
              'SOME', 'NONE', 'IS_SOME', 'IS_NONE', 'MATCH',
              'STRUCT', 'IMPL',
              'IDENTIFIER', 'NUMBER',
              'EQ', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
              'EQEQ', 'NEQ', 'GT', 'LT', 'GTE', 'LTE',
              'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
              'LBRACKET', 'RBRACKET', 'DOT',
              'SEMI', 'COMMA', 'FAT_ARROW',
              'AMPERSAND', 'COLON'}
    
    @_(r'\blet\b')
    def LET(self, t):
        return t
        
    @_(r'\bfn\b')
    def FN(self, t):
        return t
        
    @_(r'\breturn\b')
    def RETURN(self, t):
        return t
        
    @_(r'\bif\b')
    def IF(self, t):
        return t
        
    @_(r'\belse\b')
    def ELSE(self, t):
        return t
        
    @_(r'\bfor\b')
    def FOR(self, t):
        return t
        
    @_(r'\bin\b')
    def IN(self, t):
        return t
        
    @_(r'\bwhile\b')
    def WHILE(self, t):
        return t
        
    @_(r'\bSome\b')
    def SOME(self, t):
        return t
        
    @_(r'\bNone\b')
    def NONE(self, t):
        return t
        
    @_(r'\bis_some\b')
    def IS_SOME(self, t):
        return t
        
    @_(r'\bis_none\b')
    def IS_NONE(self, t):
        return t
        
    @_(r'\bmatch\b')
    def MATCH(self, t):
        return t
        
    @_(r'[a-zA-Z_][a-zA-Z0-9_]*')
    def IDENTIFIER(self, t):
        return t
        
    @_(r'\d+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t
    
    @_(r'=>')
    def FAT_ARROW(self, t):
        return t
        
    @_(r'==')
    def EQEQ(self, t):
        return t
        
    @_(r'!=')
    def NEQ(self, t):
        return t
    
    @_(r'>=')
    def GTE(self, t):
        return t
        
    @_(r'<=')
    def LTE(self, t):
        return t
    
    @_(r'\bstruct\b')
    def STRUCT(self, t):
        return t

    @_(r'\bimpl\b')
    def IMPL(self, t):
        return t

    @_(r'&')
    def AMPERSAND(self, t):
        return t

    @_(r':')
    def COLON(self, t):
        return t
        
    @_(r'>')
    def GT(self, t):
        return t
        
    @_(r'<')
    def LT(self, t):
        return t
    
    @_(r'=')
    def EQ(self, t):
        return t
        
    @_(r'\+')
    def PLUS(self, t):
        return t
        
    @_(r'-')
    def MINUS(self, t):
        return t
        
    @_(r'\*')
    def TIMES(self, t):
        return t
        
    @_(r'/')
    def DIVIDE(self, t):
        return t
        
    @_(r'\(')
    def LPAREN(self, t):
        return t
        
    @_(r'\)')
    def RPAREN(self, t):
        return t
        
    @_(r'\{')
    def LBRACE(self, t):
        return t
        
    @_(r'\}')
    def RBRACE(self, t):
        return t
        
    @_(r'\[')
    def LBRACKET(self, t):
        return t
        
    @_(r'\]')
    def RBRACKET(self, t):
        return t
        
    @_(r'\.')
    def DOT(self, t):
        return t
        
    @_(r';')
    def SEMI(self, t):
        return t
        
    @_(r',')
    def COMMA(self, t):
        return t
        
    ignore = ' \t'
    
    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += len(t.value)
        
    @_(r'//.*')
    def ignore_comment(self, t):
        pass
        
    def error(self, t):
        print(f"lexical analysis error: line {self.lineno} , illegal value '{t.value[0]}'")
        self.index += 1

if __name__ == '__main__':
    lexer = RustLikeLexer()
    code ='''
    let arr1 = [1, 2, 3];
    let sum1 = 0;
    for j in arr1 {
        let f2 = fn() => j;
        let r10 = f2();
        sum1 = sum1 + r10;
    }
    let r11 = sum1;
    '''
    print("Tokens: ")
    for tok in lexer.tokenize(code):
        print(f"  {tok.type:12} {repr(tok.value):12} (line: {tok.lineno})")