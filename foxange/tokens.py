from enum import Enum, auto


class TokenType(Enum):
    LET = auto()
    INLINE = auto()
    DEF = auto()
    CLASS = auto()
    STRUCT = auto()
    IF = auto()
    ELSE = auto()
    ELIF = auto()
    FOR = auto()
    WHILE = auto()
    BREAK = auto()
    CONTINUE = auto()
    WITH = auto()
    RETURN = auto()
    IMPORT = auto()
    FROM = auto()
    IN = auto()
    IS = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    DEL = auto()
    AS = auto()
    TRY = auto()
    HAVE = auto()
    EXCEPT = auto()
    RAISE = auto()
    LAMBDA = auto()
    OPERATOR = auto()

    TYPE_INT = auto()
    TYPE_FLOAT = auto()
    TYPE_STR = auto()
    TYPE_BOOL = auto()
    TYPE_CHAR = auto()
    TYPE_VOID = auto()
    TYPE_DEFS = auto()
    TYPE_ANY = auto()
    TYPE_LIST = auto()
    TYPE_MAP = auto()
    TYPE_SET = auto()
    TYPE_QUEUE = auto()
    TYPE_STACK = auto()
    TYPE_PAIR = auto()

    INTEGER = auto()
    FLOAT_LIT = auto()
    STRING = auto()
    CHAR_LIT = auto()
    BOOL_LIT = auto()

    IDENTIFIER = auto()

    PLUS = auto()        # +
    MINUS = auto()       # -
    STAR = auto()        # *
    SLASH = auto()       # /
    DOUBLE_SLASH = auto()  # //
    PERCENT = auto()     # %
    DOUBLE_STAR = auto() # **

    BIT_AND = auto()     # &
    BIT_OR = auto()      # |
    BIT_NOT = auto()     # ~
    BIT_XOR = auto()     # ^
    RIGHT_SHIFT = auto() # >>
    LEFT_SHIFT = auto()  # <<

    EQ = auto()          # ==
    NE = auto()          # !=
    GT = auto()          # >
    LT = auto()          # <
    GE = auto()          # >=
    LE = auto()          # <=

    LOG_AND = auto()     # &&
    LOG_OR = auto()      # ||

    ASSIGN = auto()      # =
    LEFT_ASSIGN = auto() # <=
    RIGHT_ASSIGN = auto() # =>

    WALRUS_LEFT = auto()   # :=
    WALRUS_RIGHT = auto()  # =:

    PLUS_ASSIGN = auto()      # +=
    MINUS_ASSIGN = auto()     # -=
    STAR_ASSIGN = auto()      # *=
    SLASH_ASSIGN = auto()     # /=
    DBLSLASH_ASSIGN = auto()  # //=
    PERCENT_ASSIGN = auto()   # %=
    DBLSTAR_ASSIGN = auto()   # **=
    BITAND_ASSIGN = auto()    # &=
    BITOR_ASSIGN = auto()     # |=
    BITNOT_ASSIGN = auto()    # ~=
    BITXOR_ASSIGN = auto()    # ^=
    RSHIFT_ASSIGN = auto()    # >>=
    LSHIFT_ASSIGN = auto()    # <<=

    ASSIGN_PLUS = auto()      # =+
    ASSIGN_MINUS = auto()     # =-
    ASSIGN_STAR = auto()      # =*
    ASSIGN_SLASH = auto()     # =/
    ASSIGN_DBLSLASH = auto()  # =//
    ASSIGN_PERCENT = auto()   # =%
    ASSIGN_DBLSTAR = auto()   # =**
    ASSIGN_BITAND = auto()    # =&
    ASSIGN_BITOR = auto()     # =|
    ASSIGN_BITNOT = auto()    # =~
    ASSIGN_BITXOR = auto()    # =^
    ASSIGN_RSHIFT = auto()    # =>>
    ASSIGN_LSHIFT = auto()    # =<<

    LPAREN = auto()     # (
    RPAREN = auto()     # )
    LBRACE = auto()     # {
    RBRACE = auto()     # }
    LBRACKET = auto()   # [
    RBRACKET = auto()   # ]
    COMMA = auto()      # ,
    COLON = auto()      # :
    DOT = auto()        # .
    SEMICOLON = auto()  # ;
    ARROW = auto()      # ->

    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()
    QUESTION = auto()   # ?
    AT = auto()         # @

KEYWORDS = {
    "let": TokenType.LET,
    "inline": TokenType.INLINE,
    "def": TokenType.DEF,
    "func": TokenType.DEF,
    "class": TokenType.CLASS,
    "struct": TokenType.STRUCT,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "elif": TokenType.ELIF,
    "for": TokenType.FOR,
    "while": TokenType.WHILE,
    "with": TokenType.WITH,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "return": TokenType.RETURN,
    "import": TokenType.IMPORT,
    "from": TokenType.FROM,
    "in": TokenType.IN,
    "is": TokenType.IS,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "del": TokenType.DEL,
    "as": TokenType.AS,
    "try": TokenType.TRY,
    "have": TokenType.HAVE,
    "except": TokenType.EXCEPT,
    "raise": TokenType.RAISE,
    "lambda": TokenType.LAMBDA,
    "operator": TokenType.OPERATOR,
    "int": TokenType.IDENTIFIER,
    "float": TokenType.IDENTIFIER,
    "str": TokenType.IDENTIFIER,
    "bool": TokenType.IDENTIFIER,
    "char": TokenType.IDENTIFIER,
    "void": TokenType.IDENTIFIER,
    "defs": TokenType.IDENTIFIER,
    "any": TokenType.IDENTIFIER,
    "list": TokenType.IDENTIFIER,
    "map": TokenType.IDENTIFIER,
    "set": TokenType.IDENTIFIER,
    "queue": TokenType.IDENTIFIER,
    "stack": TokenType.IDENTIFIER,
    "pair": TokenType.IDENTIFIER,
    "True": TokenType.BOOL_LIT,
    "False": TokenType.BOOL_LIT,
    "print": TokenType.IDENTIFIER,
    "input": TokenType.IDENTIFIER,
    "len": TokenType.IDENTIFIER,
    "mod": TokenType.IDENTIFIER,
    "xor": TokenType.IDENTIFIER,
    "pow": TokenType.IDENTIFIER,
}

RIGHT_COMPOUND_MAP = {
    TokenType.ASSIGN_PLUS: TokenType.PLUS_ASSIGN,
    TokenType.ASSIGN_MINUS: TokenType.MINUS_ASSIGN,
    TokenType.ASSIGN_STAR: TokenType.STAR_ASSIGN,
    TokenType.ASSIGN_SLASH: TokenType.SLASH_ASSIGN,
    TokenType.ASSIGN_DBLSLASH: TokenType.DBLSLASH_ASSIGN,
    TokenType.ASSIGN_PERCENT: TokenType.PERCENT_ASSIGN,
    TokenType.ASSIGN_DBLSTAR: TokenType.DBLSTAR_ASSIGN,
    TokenType.ASSIGN_BITAND: TokenType.BITAND_ASSIGN,
    TokenType.ASSIGN_BITOR: TokenType.BITOR_ASSIGN,
    TokenType.ASSIGN_BITNOT: TokenType.BITNOT_ASSIGN,
    TokenType.ASSIGN_BITXOR: TokenType.BITXOR_ASSIGN,
    TokenType.ASSIGN_RSHIFT: TokenType.RSHIFT_ASSIGN,
    TokenType.ASSIGN_LSHIFT: TokenType.LSHIFT_ASSIGN,
}


class Token:
    def __init__(self, type, value, line, col):
        self.type = type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, L{self.line}:{self.col})"
