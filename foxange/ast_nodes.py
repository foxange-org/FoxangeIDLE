from dataclasses import dataclass, field
from typing import Any, Optional

class ASTNode:
    line: int = 0
    col: int = 0

@dataclass
class NumberLiteral(ASTNode):
    value: Any
    type_hint: str = None

@dataclass
class StringLiteral(ASTNode):
    value: str

@dataclass
class CharLiteral(ASTNode):
    value: str

@dataclass
class BoolLiteral(ASTNode):
    value: bool

@dataclass
class Identifier(ASTNode):
    name: str

@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode

@dataclass
class BinaryOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode

@dataclass
class OperatorDef(ASTNode):
    return_type: str
    operator_tokens: list = field(default_factory=list)
    format_template: str = ""

@dataclass
class OperatorExpr(ASTNode):
    op_tokens: tuple = ()
    operands: list = field(default_factory=list)
    format_template: str = ""

@dataclass
class OperatorFuncDef(ASTNode):
    op_tokens: tuple = ()
    params: list = field(default_factory=list)
    return_type: Optional[str] = None
    body: ASTNode = None
    varargs: Optional[str] = None
    kwargs: Optional[str] = None
    is_hidden: bool = False
    is_private: bool = False
    is_inline: bool = False
    format_template: str = ""

@dataclass
class TernaryExpr(ASTNode):
    condition: ASTNode
    true_expr: ASTNode
    false_expr: ASTNode
    style: str = "python"

@dataclass
class Call(ASTNode):
    callee: ASTNode
    arguments: list = field(default_factory=list)
    star_arg: Optional[ASTNode] = None
    star_star_arg: Optional[ASTNode] = None

@dataclass
class LambdaExpr(ASTNode):
    params: list = field(default_factory=list)
    body: ASTNode = None
    varargs: Optional[str] = None
    kwargs: Optional[str] = None

@dataclass
class MemberAccess(ASTNode):
    obj: ASTNode
    member: str
    style: str = "dot"

@dataclass
class IndexAccess(ASTNode):
    obj: ASTNode
    index: ASTNode

@dataclass
class SliceExpr(ASTNode):
    start: Optional[ASTNode] = None
    stop: Optional[ASTNode] = None
    step: Optional[ASTNode] = None

@dataclass
class ExpressionStmt(ASTNode):
    expr: ASTNode

@dataclass
class VarDecl(ASTNode):
    name: str
    type_name: Optional[str] = None
    value: Optional[ASTNode] = None

@dataclass
class Assign(ASTNode):
    target: ASTNode
    value: ASTNode
    op: str = "="

@dataclass
class CompoundStatement(ASTNode):
    statements: list = field(default_factory=list)

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_branch: ASTNode
    else_branch: Optional[ASTNode] = None
    elif_branches: list = field(default_factory=list)

@dataclass
class ForLoop(ASTNode):
    var: ASTNode
    iterable: ASTNode
    body: ASTNode

@dataclass
class WhileLoop(ASTNode):
    condition: ASTNode
    body: ASTNode

@dataclass
class WithStmt(ASTNode):
    expr: ASTNode
    alias: Optional[str] = None
    body: ASTNode = None

@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode] = None

@dataclass
class BreakStmt(ASTNode):
    pass

@dataclass
class ContinueStmt(ASTNode):
    pass

@dataclass
class FuncDef(ASTNode):
    name: str
    params: list = field(default_factory=list)
    return_type: Optional[str] = None
    body: ASTNode = None
    varargs: Optional[str] = None
    kwargs: Optional[str] = None
    is_hidden: bool = False
    is_private: bool = False
    is_inline: bool = False

@dataclass
class ClassDef(ASTNode):
    name: str
    type_params: list = field(default_factory=list)
    bases: list = field(default_factory=list)
    body: list = field(default_factory=list)
    is_hidden: bool = False
    is_private: bool = False
    is_inline: bool = False

@dataclass
class StructDef(ASTNode):
    name: str
    body: list = field(default_factory=list)
    is_hidden: bool = False
    is_private: bool = False
    is_inline: bool = False

@dataclass
class DeleteStmt(ASTNode):
    target: ASTNode

@dataclass
class WalrusExpr(ASTNode):
    target: ASTNode
    value: ASTNode

@dataclass
class PrintStmt(ASTNode):
    values: list = field(default_factory=list)
    end: str = "\n"
    space: str = ""
    file: Optional[str] = None

@dataclass
class InputStmt(ASTNode):
    prompt: Optional[str] = None

@dataclass
class ListLiteral(ASTNode):
    elements: list = field(default_factory=list)
    element_type: Optional[str] = None

@dataclass
class MapLiteral(ASTNode):
    entries: list = field(default_factory=list)

@dataclass
class SetLiteral(ASTNode):
    elements: list = field(default_factory=list)

@dataclass
class QueueLiteral(ASTNode):
    elements: list = field(default_factory=list)

@dataclass
class PairLiteral(ASTNode):
    first: ASTNode
    second: ASTNode

@dataclass
class ImportStmt(ASTNode):
    module: str
    alias: Optional[str] = None

@dataclass
class FromImportStmt(ASTNode):
    module: str
    names: list = field(default_factory=list)

@dataclass
class HaveClause(ASTNode):
    error_types: list = field(default_factory=list)
    alias: Optional[str] = None
    body: ASTNode = None

@dataclass
class TryStmt(ASTNode):
    try_body: ASTNode
    have_clauses: list = field(default_factory=list)

@dataclass
class RaiseStmt(ASTNode):
    expr: ASTNode = None

@dataclass
class Program(ASTNode):
    statements: list = field(default_factory=list)
