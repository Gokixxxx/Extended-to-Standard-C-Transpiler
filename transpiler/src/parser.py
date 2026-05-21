"""
语法分析器
"""
import ply.yacc as yacc
from .lexer import tokens, reserved

# AST 节点定义
class ASTNode:
    def __init__(self, line=None):
        self.line = line

class Program(ASTNode):
    def __init__(self, functions, line=None):
        super().__init__(line)
        self.functions = functions

class FunctionDecl(ASTNode):
    def __init__(self, name, params, body, line=None):
        super().__init__(line)
        self.name = name
        self.params = params
        self.body = body

class Block(ASTNode):
    def __init__(self, statements, line=None):
        super().__init__(line)
        self.statements = statements

class LetStmt(ASTNode):
    def __init__(self, name, value, line=None):
        super().__init__(line)
        self.name = name
        self.value = value

class IfStmt(ASTNode):
    def __init__(self, condition, then_branch, else_branch, line=None):
        super().__init__(line)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

class ReturnStmt(ASTNode):
    def __init__(self, value, line=None):
        super().__init__(line)
        self.value = value

class BinaryExpr(ASTNode):
    def __init__(self, left, op, right, line=None):
        super().__init__(line)
        self.left = left
        self.op = op
        self.right = right

class Literal(ASTNode):
    def __init__(self, value, line=None):
        super().__init__(line)
        self.value = value

class Identifier(ASTNode):
    def __init__(self, name, line=None):
        super().__init__(line)
        self.name = name

class Parser:
    def __init__(self):
        self.tokens = tokens
        # 定义运算符优先级
        self.precedence = (
            ('left', 'OR'),
            ('left', 'AND'),
            ('nonassoc', 'EQUALS', 'NEQUALS'),
            ('nonassoc', 'LESS', 'GREATER', 'LESSEQUAL', 'GREATEREQUAL'),
            ('left', 'PLUS', 'MINUS'),
            ('left', 'TIMES', 'DIVIDE'),
            ('right', 'UMINUS'),
        )
        
        # 构建 parser
        self.parser = yacc.yacc(module=self, debug=False, write_tables=False)
    
    def parse(self, code):
        return self.parser.parse(code)
    
    # 语法规则
    def p_program(self, p):
        '''program : function_decl program
                   | function_decl
                   | empty'''
        if len(p) == 3:
            if p[2] is None:
                p[0] = [p[1]]
            else:
                p[0] = [p[1]] + p[2]
        elif p[1] is not None:
            p[0] = [p[1]]
        else:
            p[0] = []
    
    def p_function_decl(self, p):
        '''function_decl : FN IDENTIFIER LPAREN param_list RPAREN block'''
        p[0] = FunctionDecl(p[2], p[4], p[6])
    
    def p_param_list(self, p):
        '''param_list : IDENTIFIER COMMA param_list
                      | IDENTIFIER
                      | empty'''
        if len(p) == 4:
            p[0] = [p[1]] + p[3]
        elif p[1] is not None:
            p[0] = [p[1]]
        else:
            p[0] = []
    
    def p_block(self, p):
        '''block : LBRACE statement_list RBRACE'''
        p[0] = Block(p[2])
    
    def p_statement_list(self, p):
        '''statement_list : statement statement_list
                          | statement
                          | empty'''
        if len(p) == 3:
            if p[2] is None:
                p[0] = [p[1]]
            else:
                p[0] = [p[1]] + p[2]
        elif p[1] is not None:
            p[0] = [p[1]]
        else:
            p[0] = []
    
    def p_statement(self, p):
        '''statement : let_stmt SEMICOLON
                     | if_stmt
                     | return_stmt SEMICOLON'''
        p[0] = p[1]
    
    def p_let_stmt(self, p):
        '''let_stmt : LET IDENTIFIER ASSIGN expression'''
        p[0] = LetStmt(p[2], p[4])
    
    def p_if_stmt(self, p):
        '''if_stmt : IF expression block ELSE block
                   | IF expression block'''
        if len(p) == 6:
            p[0] = IfStmt(p[2], p[3], p[5])
        else:
            p[0] = IfStmt(p[2], p[3], None)
    
    def p_return_stmt(self, p):
        '''return_stmt : RETURN expression'''
        p[0] = ReturnStmt(p[2])
    
    def p_expression_binop(self, p):
        '''expression : expression PLUS expression
                      | expression MINUS expression
                      | expression TIMES expression
                      | expression DIVIDE expression
                      | expression EQUALS expression
                      | expression NEQUALS expression
                      | expression LESS expression
                      | expression GREATER expression
                      | expression LESSEQUAL expression
                      | expression GREATEREQUAL expression'''
        p[0] = BinaryExpr(p[1], p[2], p[3])
    
    def p_expression_group(self, p):
        '''expression : LPAREN expression RPAREN'''
        p[0] = p[2]
    
    def p_expression_literal(self, p):
        '''expression : INTEGER
                      | FLOAT_LITERAL
                      | STRING_LITERAL'''
        p[0] = Literal(p[1])
    
    def p_expression_identifier(self, p):
        '''expression : IDENTIFIER'''
        p[0] = Identifier(p[1])
    
    def p_empty(self, p):
        '''empty :'''
        pass
    
    def p_error(self, p):
        if p:
            print(f"Syntax error at token {p.type} (value: {p.value}) on line {p.lineno}")
        else:
            print("Syntax error at EOF")

# 为了兼容性，提供简单的解析函数
def parse(code):
    parser = Parser()
    return parser.parse(code)

def test_parser():
    code = '''
    fn main() {
        let x = 42;
        let y = 3.14;
        if x > 0 {
            return x;
        }
    }
    '''
    
    # 测试 lexer
    print("=== Lexer Output ===")
    lexer.input(code)
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)
    
    # 测试 parser
    print("\n=== Parser Output ===")
    result = parse(code)
    print(f"Parsed {len(result)} function(s)")
    
    # 打印 AST 结构
    for func in result:
        print(f"Function: {func.name}")
        print(f"Body has {len(func.body.statements)} statements")

if __name__ == "__main__":
    from .lexer import lexer
    test_parser()