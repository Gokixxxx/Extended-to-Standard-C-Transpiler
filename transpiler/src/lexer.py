"""
词法分析器 - 将源代码分解为token序列
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Token:
    """Token类定义"""
    type: str
    value: str
    line: int
    column: int
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}', line={self.line}, col={self.column})"

class Lexer:
    """词法分析器类"""
    
    def __init__(self, source_code: str):
        """初始化词法分析器
        
        Args:
            source_code: 源代码字符串
        """
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
    
    def tokenize(self) -> List[Token]:
        """将源代码分解为token序列
        
        Returns:
            Token列表
        """
        pass
    
    def get_next_token(self) -> Optional[Token]:
        """获取下一个token
        
        Returns:
            下一个Token对象，如果没有则返回None
        """
        pass
    
    def peek_token(self, lookahead: int = 1) -> Optional[Token]:
        """预览下一个token（不消耗）
        
        Args:
            lookahead: 向前预览的token数量
            
        Returns:
            预览的Token对象，如果没有则返回None
        """
        pass
    
    def _is_whitespace(self, char: str) -> bool:
        """检查字符是否为空白字符"""
        pass
    
    def _is_digit(self, char: str) -> bool:
        """检查字符是否为数字"""
        pass
    
    def _is_letter(self, char: str) -> bool:
        """检查字符是否为字母"""
        pass
    
    def _scan_identifier(self) -> Token:
        """扫描标识符"""
        pass
    
    def _scan_number(self) -> Token:
        """扫描数字"""
        pass
    
    def _scan_string(self) -> Token:
        """扫描字符串字面量"""
        pass
    
    def _scan_comment(self) -> Optional[Token]:
        """扫描注释"""
        pass

def tokenize(source_code: str) -> List[Token]:
    """词法分析入口函数
    
    Args:
        source_code: 源代码字符串
        
    Returns:
        Token列表
    """
    lexer = Lexer(source_code)
    return lexer.tokenize()