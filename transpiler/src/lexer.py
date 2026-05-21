"""
词法分析器 - 将源代码分解为token序列
"""
import ply.lex as lex
import re

# Token 列表
tokens = (
    # 关键字
    'FN', 'LET', 'MUT', 'IF', 'ELSE', 'WHILE', 'FOR', 'IN',
    'MATCH', 'RETURN', 'PUB', 'USE', 'MOD', 'CRATE',
    'STRUCT', 'ENUM', 'IMPL', 'TRAIT',
    'BOOL', 'I8', 'I16', 'I32', 'I64', 'I128', 'ISIZE',
    'U8', 'U16', 'U32', 'U64', 'U128', 'USIZE',
    'F32', 'F64', 'CHAR', 'STR',
    
    # 标识符和字面量
    'IDENTIFIER',
    'INTEGER', 'FLOAT_LITERAL',
    'CHAR_LITERAL', 'STRING_LITERAL',
    'RAW_STRING_LITERAL',
    'BYTE_STRING_LITERAL', 'RAW_BYTE_STRING_LITERAL',
    
    # 运算符
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULO',
    'EQUALS', 'NEQUALS', 'LESSEQUAL', 'GREATEREQUAL',
    'LESS', 'GREATER',
    'LOGICAL_AND', 'LOGICAL_OR', 'LOGICAL_NOT',
    'ASSIGN', 'PLUS_ASSIGN', 'MINUS_ASSIGN', 'TIMES_ASSIGN', 'DIVIDE_ASSIGN', 'MODULO_ASSIGN',
    
    # Rust 特有运算符
    'REFERENCE', 'DEREFERENCE',  # & 和 *
    'MATCH_ARROW',  # =>
    'RANGE', 'RANGE_INCLUSIVE',  # .. 和 ..=
    'COLON', 'DOUBLE_COLON',  # : 和 ::
    
    # 分隔符
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET', 'RBRACKET',
    'SEMICOLON', 'COMMA', 'DOT',
    
    # 泛型和生命周期
    'LT', 'GT', 'LIFETIME',
    
    # 属性宏
    'ATTRIBUTE',
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
    'bool': 'BOOL',
    'i8': 'I8', 'i16': 'I16', 'i32': 'I32', 'i64': 'I64', 'i128': 'I128', 'isize': 'ISIZE',
    'u8': 'U8', 'u16': 'U16', 'u32': 'U32', 'u64': 'U64', 'u128': 'U128', 'usize': 'USIZE',
    'f32': 'F32', 'f64': 'F64',
    'char': 'CHAR',
    'str': 'STR',
}

# 单字符 token
t_PLUS      = r'\+'
t_MINUS     = r'-'
t_TIMES     = r'\*'
t_DIVIDE    = r'/'
t_MODULO    = r'%'
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_LBRACE    = r'\{'
t_RBRACE    = r'\}'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_SEMICOLON = r';'
t_COMMA     = r','
t_DOT       = r'\.'
t_LT        = r'<'
t_GT        = r'>'
t_COLON     = r':'

# 复合运算符
t_EQUALS            = r'=='
t_NEQUALS           = r'!='
t_LESSEQUAL         = r'<='
t_GREATEREQUAL      = r'>='
t_LOGICAL_AND       = r'&&'
t_LOGICAL_OR        = r'\|\|'
t_LOGICAL_NOT       = r'!'
t_PLUS_ASSIGN       = r'\+='
t_MINUS_ASSIGN      = r'-='
t_TIMES_ASSIGN      = r'\*='
t_DIVIDE_ASSIGN     = r'/='
t_MODULO_ASSIGN     = r'%='
t_MATCH_ARROW       = r'=>'
t_RANGE_INCLUSIVE   = r'\.\.='
t_RANGE             = r'\.\.'
t_DOUBLE_COLON      = r'::'

# 引用和解引用
t_REFERENCE         = r'&'
t_DEREFERENCE       = r'\*'

# 赋值运算符（必须在复合运算符之后定义）
t_ASSIGN            = r'='

# 忽略的字符
t_ignore = ' \t'

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

def t_INTEGER(t):
    r'\d+(_\d+)*'
    # 移除下划线并转换为整数
    t.value = int(t.value.replace('_', ''))
    return t

def t_FLOAT_LITERAL(t):
    r'(\d+(_\d+)*)?\.\d+(_\d+)*(?:[eE][+-]?\d+(_\d+)*)?|\d+(_\d+)*[eE][+-]?\d+(_\d+)*'
    t.value = float(t.value.replace('_', ''))
    return t

def t_CHAR_LITERAL(t):
    r"'(?:[^'\\]|\\.)*'"
    # 提取字符内容，保留转义序列
    t.value = t.value[1:-1]
    return t

def t_RAW_STRING_LITERAL(t):
    r'r(#*)"([^"\\]*(?:\\.[^"\\]*)*)"\1'
    # 提取分隔符数量和内容
    hash_count = len(re.match(r'r(#*)', t.value).group(1))
    content_start = t.value.find('"') + 1
    content_end = t.value.rfind('"')
    t.value = t.value[content_start:content_end]
    return t

def t_BYTE_STRING_LITERAL(t):
    r'b"([^"\\]*(?:\\.[^"\\]*)*)"'
    # 提取字节字符串内容
    t.value = t.value[2:-1]  # 移除 b"
    return t

def t_RAW_BYTE_STRING_LITERAL(t):
    r'br(#*)"([^"\\]*(?:\\.[^"\\]*)*)"\1'
    hash_count = len(re.match(r'br(#*)', t.value).group(1))
    content_start = t.value.find('"') + 1
    content_end = t.value.rfind('"')
    t.value = t.value[content_start:content_end]
    return t

def t_STRING_LITERAL(t):
    r'"([^"\\]*(?:\\.[^"\\]*)*)"'
    # 提取字符串内容，保留转义序列
    t.value = t.value[1:-1]
    return t

def t_LIFETIME(t):
    r"'[a-zA-Z_][a-zA-Z_0-9]*"
    return t

def t_ATTRIBUTE(t):
    r'#\[.*?\]'
    return t

def t_DOC_COMMENT(t):
    r'///.*'
    pass  # 忽略文档注释

def t_COMMENT(t):
    r'//.*|/\*(.|\n)*?\*/'
    pass  # 忽略普通注释

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Lexical error: Illegal character '{t.value[0]}' at line {t.lexer.lineno}")
    t.lexer.skip(1)

class RustLexer:
    def __init__(self):
        self.lexer = lex.lex(module=self)
    
    def tokenize(self, code):
        self.lexer.input(code)
        tokens = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            tokens.append(tok)
        return tokens

# 测试函数
def test_lexer():
    """测试词法分析器"""
    lexer = RustLexer()
    
    # 测试代码
    test_code = '''
    // 基本语法
    fn main() {
        let x = 42;
        let y = 3.14_f64;
        let s = "hello world";
        let c = 'A';
        
        // Raw string
        let raw = r#"Hello "world""#;
        
        // 生命周期
        let ref_str: &'static str = "test";
        
        // 条件语句
        if x > 0 && y < 10.0 {
            return x;
        } else {
            match x {
                1 => println!("one"),
                _ => println!("other"),
            }
        }
    }
    '''
    
    print("Tokenizing test code:")
    tokens = lexer.tokenize(test_code)
    
    for i, token in enumerate(tokens):
        print(f"{i+1:2d}. {token.type:20} = {repr(token.value)} (line {token.lineno})")
    
    # 验证关键 token
    assert tokens[0].type == 'FN'
    assert tokens[1].type == 'IDENTIFIER' and tokens[1].value == 'main'
    assert tokens[5].type == 'LET'
    assert tokens[7].type == 'INTEGER' and tokens[7].value == 42
    assert tokens[11].type == 'FLOAT_LITERAL' and abs(tokens[11].value - 3.14) < 0.001
    assert tokens[15].type == 'STRING_LITERAL' and tokens[15].value == 'hello world'
    assert tokens[19].type == 'CHAR_LITERAL' and tokens[19].value == 'A'
    assert tokens[24].type == 'RAW_STRING_LITERAL' and tokens[24].value == 'Hello "world"'
    assert tokens[31].type == 'LIFETIME' and tokens[31].value == "'static"
    assert tokens[40].type == 'LOGICAL_AND'
    assert tokens[48].type == 'MATCH_ARROW'
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    test_lexer()