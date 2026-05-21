"""
抽象语法树(AST)节点定义
"""

from typing import List, Optional, Any, Dict
from dataclasses import dataclass

@dataclass
class ASTNode:
    """AST节点基类"""
    pass

@dataclass
class ProgramNode(ASTNode):
    """程序根节点"""
    statements: List['StatementNode']
    
    def __init__(self, statements: List['StatementNode']):
        self.statements = statements

@dataclass
class StatementNode(ASTNode):
    """语句节点基类"""
    pass

@dataclass
class LetStatementNode(StatementNode):
    """let声明节点"""
    name: str
    value: 'ExpressionNode'
    
    def __init__(self, name: str, value: 'ExpressionNode'):
        self.name = name
        self.value = value

@dataclass
class ReturnStatementNode(StatementNode):
    """return语句节点"""
    value: Optional['ExpressionNode']
    
    def __init__(self, value: Optional['ExpressionNode'] = None):
        self.value = value

@dataclass
class ExpressionStatementNode(StatementNode):
    """表达式语句节点"""
    expression: 'ExpressionNode'
    
    def __init__(self, expression: 'ExpressionNode'):
        self.expression = expression

@dataclass
class ExpressionNode(ASTNode):
    """表达式节点基类"""
    pass

@dataclass
class IdentifierNode(ExpressionNode):
    """标识符节点"""
    name: str
    
    def __init__(self, name: str):
        self.name = name

@dataclass
class IntegerLiteralNode(ExpressionNode):
    """整数字面量节点"""
    value: int
    
    def __init__(self, value: int):
        self.value = value

@dataclass
class StringLiteralNode(ExpressionNode):
    """字符串字面量节点"""
    value: str
    
    def __init__(self, value: str):
        self.value = value

@dataclass
class BooleanLiteralNode(ExpressionNode):
    """布尔字面量节点"""
    value: bool
    
    def __init__(self, value: bool):
        self.value = value

@dataclass
class InfixExpressionNode(ExpressionNode):
    """中缀表达式节点"""
    operator: str
    left: 'ExpressionNode'
    right: 'ExpressionNode'
    
    def __init__(self, operator: str, left: 'ExpressionNode', right: 'ExpressionNode'):
        self.operator = operator
        self.left = left
        self.right = right

@dataclass
class PrefixExpressionNode(ExpressionNode):
    """前缀表达式节点"""
    operator: str
    right: 'ExpressionNode'
    
    def __init__(self, operator: str, right: 'ExpressionNode'):
        self.operator = operator
        self.right = right

@dataclass
class FunctionLiteralNode(ExpressionNode):
    """函数字面量节点"""
    parameters: List[str]
    body: List[StatementNode]
    
    def __init__(self, parameters: List[str], body: List[StatementNode]):
        self.parameters = parameters
        self.body = body

@dataclass
class CallExpressionNode(ExpressionNode):
    """函数调用节点"""
    function: 'ExpressionNode'
    arguments: List['ExpressionNode']
    
    def __init__(self, function: 'ExpressionNode', arguments: List['ExpressionNode']):
        self.function = function
        self.arguments = arguments

@dataclass
class MatchExpressionNode(ExpressionNode):
    """match表达式节点"""
    value: 'ExpressionNode'
    arms: List[tuple]  # (pattern, expression)
    
    def __init__(self, value: 'ExpressionNode', arms: List[tuple]):
        self.value = value
        self.arms = arms

@dataclass
class OptionValueNode(ExpressionNode):
    """Option值节点"""
    is_some: bool
    value: Optional['ExpressionNode']
    
    def __init__(self, is_some: bool, value: Optional['ExpressionNode'] = None):
        self.is_some = is_some
        self.value = value

@dataclass
class VectorLiteralNode(ExpressionNode):
    """Vector字面量节点"""
    elements: List['ExpressionNode']
    
    def __init__(self, elements: List['ExpressionNode']):
        self.elements = elements

@dataclass
class IndexExpressionNode(ExpressionNode):
    """索引表达式节点"""
    left: 'ExpressionNode'
    index: 'ExpressionNode'
    
    def __init__(self, left: 'ExpressionNode', index: 'ExpressionNode'):
        self.left = left
        self.index = index

@dataclass
class StructDefinitionNode(StatementNode):
    """结构体定义节点"""
    name: str
    fields: Dict[str, str]  # field_name -> type
    
    def __init__(self, name: str, fields: Dict[str, str]):
        self.name = name
        self.fields = fields

@dataclass
class MethodImplementationNode(StatementNode):
    """方法实现节点"""
    struct_name: str
    method_name: str
    parameters: List[tuple]  # (name, type)
    return_type: Optional[str]
    body: List[StatementNode]
    
    def __init__(self, struct_name: str, method_name: str, 
                 parameters: List[tuple], return_type: Optional[str],
                 body: List[StatementNode]):
        self.struct_name = struct_name
        self.method_name = method_name
        self.parameters = parameters
        self.return_type = return_type
        self.body = body

@dataclass
class IfExpressionNode(ExpressionNode):
    """if表达式节点"""
    condition: 'ExpressionNode'
    consequence: List[StatementNode]
    alternative: Optional[List[StatementNode]]
    
    def __init__(self, condition: 'ExpressionNode', 
                 consequence: List[StatementNode],
                 alternative: Optional[List[StatementNode]] = None):
        self.condition = condition
        self.consequence = consequence
        self.alternative = alternative