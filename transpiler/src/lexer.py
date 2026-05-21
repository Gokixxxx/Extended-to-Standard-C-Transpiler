"""
词法分析器
"""
import ply.lex as lex

# Token 列表
tokens = (
    'FN', 'LET', 'MUT', 'IF', 'ELSE', 'WHILE', 'FOR', 'IN',
    'MATCH', 'RETURN', 'PUB', 'USE', 'MOD', 'CRATE',
    'STRUCT', 'ENUM', 'IMPL', 'TRAIT', 'TYPE',
    'IDENTIFIER',
    'INTEGER', 'FLOAT_LITERAL',
    'CHAR_LITERAL', 'STRING_LITERAL',
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
    'SEMICOLON', 'COMMA', 'DOT',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'EQUALS', 'NEQUALS', 'LESS', 'GREATER', 'LESSEQUAL', 'GREATEREQUAL',
    'ASSIGN',
    'AMPERSAND',
)

# 关键字映射
reserved = {
    'fn': 'FN',
    'let': 'LET',
    'mut': 'MUT',
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'for': 'FOR',
    'in': 'IN',
    'match': 'MATCH',
    'return': 'RETURN',
    'pub': 'PUB',
    'use': 'USE',
    'mod': 'MOD',
    'crate': 'CRATE',
    'struct': 'STRUCT',
    'enum': 'ENUM',
    'impl': 'IMPL',
    'trait': 'TRAIT',
    'type': 'TYPE',
}

# 简单的 token 规则
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_LBRACE    = r'\{'
t_RBRACE    = r'\}'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_SEMICOLON = r';'
t_COMMA     = r','
t_DOT       = r'\.'
t_PLUS      = r'\+'
t_MINUS     = r'-'
t_TIMES     = r'\*'
t_DIVIDE    = r'/'
t_EQUALS    = r'=='
t_NEQUALS   = r'!='
t_LESS      = r'<'
t_GREATER   = r'>'
t_LESSEQUAL = r'<='
t_GREATEREQUAL = r'>='
t_ASSIGN    = r'='
t_AMPERSAND = r'&'

# 忽略空白字符
t_ignore = ' \t'

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

def t_FLOAT_LITERAL(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_CHAR_LITERAL(t):
    r"'([^'\\]|\\.)*'"
    t.value = t.value[1:-1]  # 去掉引号
    return t

def t_STRING_LITERAL(t):
    r'"([^"\\]|\\.)*"'
    t.value = t.value[1:-1]  # 去掉引号
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)

# 构建 lexer
lexer = lex.lex()

# 测试函数
def test():
    data = '''
    fn main() {
        let x = 42;
        let y = 3.14;
        let s = "hello";
        if x > 0 {
            return x;
        }
    }
    '''
    
    lexer.input(data)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)

if __name__ == "__main__":
    test()