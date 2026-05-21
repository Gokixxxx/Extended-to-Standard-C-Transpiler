"""
词法分析器
"""
from sly import Lexer
from typing import Any
_: Any

class RustLikeLexer(Lexer):
    tokens = {'LET', 'SOME', 'NONE', 'IS_SOME', 'IS_NONE', 'MATCH',
              'IDENTIFIER', 'NUMBER',
              'EQ', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
              'EQEQ', 'NEQ',
              'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
              'SEMI', 'COMMA', 'FAT_ARROW'}
    
    @_(r'\blet\b')
    def LET(self, t):
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
    
    # 多字符运算符（必须在单字符运算符之前定义！）
    @_(r'=>')
    def FAT_ARROW(self, t):
        return t
        
    @_(r'==')
    def EQEQ(self, t):
        return t
        
    @_(r'!=')
    def NEQ(self, t):
        return t
    
    # 单字符运算符
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
        print(f"词法错误：第 {self.lineno} 行，非法字符 '{t.value[0]}'")
        self.index += 1

# 测试
if __name__ == '__main__':
    lexer = RustLikeLexer()
    code ='''let x = Some(5); 
    let y = match x { Some(v) => v + 1, None => 0 };
    '''
    print("Tokens: ")
    for tok in lexer.tokenize(code):
        print(f"  {tok.type:10} {repr(tok.value):12} ( {tok.lineno})")