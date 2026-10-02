from .tokens import TokenType
from .ast_nodes import *
from .error_utils import FoxangeError


class Parser:
    _OPDEF_OP_TYPES = (
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
        TokenType.DOUBLE_SLASH, TokenType.PERCENT, TokenType.DOUBLE_STAR,
        TokenType.BIT_AND, TokenType.BIT_OR, TokenType.BIT_XOR,
        TokenType.RIGHT_SHIFT, TokenType.LEFT_SHIFT,
        TokenType.EQ, TokenType.NE, TokenType.GT, TokenType.LT,
        TokenType.GE, TokenType.LE,
        TokenType.LOG_AND, TokenType.LOG_OR,
        TokenType.IS, TokenType.IN, TokenType.AND, TokenType.OR,
        TokenType.QUESTION, TokenType.COLON, TokenType.AT,
        TokenType.IDENTIFIER, TokenType.STRING,
    )

    def __init__(self, tokens, source=None, file_path=None):
        self.tokens = tokens
        self.pos = 0
        self.source = source or ""
        self.file_path = file_path
        self._source_lines = None
        self.operator_registry = {}
        self._custom_ops = []

    @property
    def source_lines(self):
        if self._source_lines is None:
            self._source_lines = self.source.split("\n")
        return self._source_lines

    def _pos(self, node, token):
        if token:
            node.line = token.line
            node.col = token.col

    def peek(self, offset=0):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def advance(self):
        tok = self.peek()
        if tok:
            self.pos += 1
        return tok

    def push_back(self, tok):
        self.tokens.insert(self.pos, tok)

    def check(self, *types):
        t = self.peek()
        return t and t.type in types

    def match(self, *types):
        if self.check(*types):
            return self.advance()
        return None

    def expect(self, typ, msg=None):
        tok = self.peek()
        if tok and tok.type == typ:
            return self.advance()
        err_tok = tok
        line = err_tok.line if err_tok else 1
        col = err_tok.col if err_tok else 0
        sl = None
        if err_tok and err_tok.line > 0:
            idx = err_tok.line - 1
            if 0 <= idx < len(self.source_lines):
                sl = self.source_lines[idx].rstrip("\n").rstrip("\r")
        raise FoxangeError(
            msg or f"Expected {typ}, got {err_tok.type if err_tok else 'EOF'}",
            exc_type="SyntaxError", line=line, col=col,
            source_line=sl, file_path=self.file_path
        )

    def skip_newlines(self):
        while self.check(TokenType.NEWLINE) or self.check(TokenType.SEMICOLON):
            self.advance()

    def error(self, msg):
        tok = self.peek()
        line = tok.line if tok else 1
        col = tok.col if tok else 0
        sl = None
        if tok and tok.line > 0:
            idx = tok.line - 1
            if 0 <= idx < len(self.source_lines):
                sl = self.source_lines[idx].rstrip("\n").rstrip("\r")
        raise FoxangeError(msg, exc_type="SyntaxError",
                          line=line, col=col, source_line=sl,
                          file_path=self.file_path)

    def is_at_end(self):
        return self.check(TokenType.EOF) or self.check(TokenType.DEDENT)
    COMPOUND_OPS = {
        TokenType.PLUS_ASSIGN: "+=",
        TokenType.MINUS_ASSIGN: "-=",
        TokenType.STAR_ASSIGN: "*=",
        TokenType.SLASH_ASSIGN: "/=",
        TokenType.DBLSLASH_ASSIGN: "//=",
        TokenType.PERCENT_ASSIGN: "%=",
        TokenType.DBLSTAR_ASSIGN: "**=",
        TokenType.BITAND_ASSIGN: "&=",
        TokenType.BITOR_ASSIGN: "|=",
        TokenType.BITNOT_ASSIGN: "~=",
        TokenType.BITXOR_ASSIGN: "^=",
        TokenType.RSHIFT_ASSIGN: ">>=",
        TokenType.LSHIFT_ASSIGN: "<<=",
    }
    RIGHT_TO_LEFT_OP = {
        TokenType.ASSIGN_PLUS: "+=",
        TokenType.ASSIGN_MINUS: "-=",
        TokenType.ASSIGN_STAR: "*=",
        TokenType.ASSIGN_SLASH: "/=",
        TokenType.ASSIGN_DBLSLASH: "//=",
        TokenType.ASSIGN_PERCENT: "%=",
        TokenType.ASSIGN_DBLSTAR: "**=",
        TokenType.ASSIGN_BITAND: "&=",
        TokenType.ASSIGN_BITOR: "|=",
        TokenType.ASSIGN_BITNOT: "~=",
        TokenType.ASSIGN_BITXOR: "^=",
        TokenType.ASSIGN_RSHIFT: ">>=",
        TokenType.ASSIGN_LSHIFT: "<<=",
    }

    def parse(self):
        statements = []
        while not self.check(TokenType.EOF):
            self.skip_newlines()
            if self.check(TokenType.EOF):
                break
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        return Program(statements)

    def statement(self):
        if self.check(TokenType.INLINE):
            nxt = self.peek(1)
            if nxt and nxt.type == TokenType.CLASS:
                return self.class_def()
            if nxt and nxt.type == TokenType.STRUCT:
                return self.struct_def()
            if self._operator_func_def_start():
                return self.operator_func_def()
            return self.func_def()
        if self.check(TokenType.DEF):
            return self.func_def()
        if self.check(TokenType.CLASS):
            return self.class_def()
        if self.check(TokenType.STRUCT):
            return self.struct_def()
        if self.check(TokenType.LET):
            return self.var_decl()
        if self.check(TokenType.IMPORT):
            return self.import_stmt()
        if self.check(TokenType.FROM):
            return self.from_import()
        if self.check(TokenType.IF):
            return self.if_stmt()
        if self.check(TokenType.FOR):
            return self.for_loop()
        if self.check(TokenType.WHILE):
            return self.while_loop()
        if self.check(TokenType.BREAK):
            self.advance()
            return BreakStmt()
        if self.check(TokenType.CONTINUE):
            self.advance()
            return ContinueStmt()
        if self.check(TokenType.TRY):
            return self.try_stmt()
        if self.check(TokenType.RAISE):
            return self.raise_stmt()
        if self.check(TokenType.WITH):
            return self.with_stmt()
        if self.check(TokenType.RETURN):
            return self.return_stmt()
        if self.check(TokenType.DEL):
            return self.delete_stmt()
        if self.check(TokenType.IDENTIFIER):
            name_tok = self.peek()
            name = name_tok.value
            if name == "print":
                return self.print_stmt()
            if name == "input":
                return self.input_stmt()
            if self.peek(1) and self.peek(1).type == TokenType.LE:
                target = Identifier(self.advance().value)
                self.advance()  # skip <=
                value = self.expression()
                return ExpressionStmt(Assign(target, value, "="))
            if self._operator_func_def_start():
                return self.operator_func_def()
            if self._is_operator_def_start():
                return self.operator_def()
            return self.expr_stmt()
        if self._is_expr_start():
            return self.expr_stmt()

        self.error(f"Unexpected token '{self.peek().value}'")

    def _block_intro(self, what="Expected ':' or '{'"):
        """块语句的可选冒号引导：支持 ':' + 缩进体、':' + 单行体、'{' 花括号体。"""
        if not self.match(TokenType.COLON) and not self.check(TokenType.LBRACE):
            self.error(what)

    def brace_block(self):
        """花括号块：'{' ... '}' 包裹语句体，块内缩进无关（自动跳过词法产生的 INDENT/DEDENT）。"""
        self.expect(TokenType.LBRACE)
        stmts = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            if self.check(TokenType.NEWLINE) or self.check(TokenType.INDENT) or self.check(TokenType.DEDENT):
                self.advance()
                continue
            stmts.append(self.statement())
        self.expect(TokenType.RBRACE)
        if self.check(TokenType.NEWLINE):
            self.advance()
        return CompoundStatement(stmts)

    def block(self):
        self.skip_newlines()
        self.expect(TokenType.INDENT, "Expected indented block")
        stmts = []
        while not self.check(TokenType.DEDENT) and not self.check(TokenType.EOF):
            self.skip_newlines()
            if self.check(TokenType.DEDENT) or self.check(TokenType.EOF):
                break
            stmts.append(self.statement())
            self.skip_newlines()
        self.expect(TokenType.DEDENT, "Expected DEDENT")
        return CompoundStatement(stmts)

    def _parse_body(self):
        if self.check(TokenType.LBRACE):
            return self.brace_block()
        if self.check(TokenType.NEWLINE):
            return self.block()
        stmt = self.statement()
        return CompoundStatement([stmt])

    def _is_expr_start(self):
        return self.check(
            TokenType.INTEGER, TokenType.FLOAT_LIT, TokenType.STRING,
            TokenType.CHAR_LIT, TokenType.BOOL_LIT,
            TokenType.LPAREN, TokenType.LBRACKET, TokenType.LBRACE,
            TokenType.MINUS, TokenType.BIT_NOT, TokenType.NOT,
            TokenType.PLUS,  # 一元+
        )

    def expr_stmt(self):
        expr = self.expression()
        node = ExpressionStmt(expr)
        node.line = getattr(expr, 'line', 0)
        node.col = getattr(expr, 'col', 0)
        return node

    @staticmethod
    def _parse_format_template(fmt):
        parts = []
        i = 0
        n = len(fmt)
        while i < n:
            ch = fmt[i]
            if ch == "%":
                parts.append(("%", None))
                i += 1
            elif ch == "&":
                j = i + 1
                num_s = ""
                while j < n and fmt[j].isdigit():
                    num_s += fmt[j]
                    j += 1
                if not num_s:
                    return None
                parts.append(("&", int(num_s)))
                i = j
            elif ch in " \t":
                i += 1
            else:
                return None
        return parts

    def _is_operator_token(self, tok):
        return tok is not None and tok.type in self._OPDEF_OP_TYPES

    def _token_list_end_offset(self):
        if self.peek(1) is None or self.peek(1).type != TokenType.LPAREN:
            return -1
        i = 2
        if not self._is_operator_token(self.peek(i)):
            return -1
        i += 1
        while True:
            t = self.peek(i)
            if t is None:
                return -1
            if t.type == TokenType.COMMA:
                i += 1
                if not self._is_operator_token(self.peek(i)):
                    return -1
                i += 1
            elif t.type == TokenType.RPAREN:
                return i
            else:
                return -1

    def _is_format_string_after(self, offset):
        if self.peek(offset) is None or self.peek(offset).type != TokenType.LPAREN:
            return False
        if self.peek(offset + 1) is None or self.peek(offset + 1).type != TokenType.STRING:
            return False
        if self.peek(offset + 2) is None or self.peek(offset + 2).type != TokenType.RPAREN:
            return False
        return True

    def _is_operator_def_start(self):
        if not self.check(TokenType.IDENTIFIER):
            return False
        nxt = self.peek(1)
        if nxt is None:
            return False
        if nxt.type == TokenType.LPAREN:
            end = self._token_list_end_offset()
            if end < 0:
                return False
            return self._is_format_string_after(end + 1)
        if self._is_operator_token(nxt):
            return self._is_format_string_after(2)
        return False

    def operator_def(self):
        ret_tok = self.advance()
        op_tokens = []
        if self.check(TokenType.LPAREN):
            self.advance()
            op_tokens.append(self.advance().value)
            while self.check(TokenType.COMMA):
                self.advance()
                op_tokens.append(self.advance().value)
            self.expect(TokenType.RPAREN)
        else:
            op_tokens.append(self.advance().value)
        self.expect(TokenType.LPAREN)
        fmt_tok = self.expect(TokenType.STRING, "Expected operator format string")
        self.expect(TokenType.RPAREN)
        node = OperatorDef(ret_tok.value, op_tokens, fmt_tok.value)
        self._pos(node, ret_tok)
        self._validate_opdef(node)
        self._register_operator(node)
        return node

    def _operator_func_def_start(self):
        i = 0
        if self.peek(i) is None:
            return False
        if self.peek(i).type == TokenType.INLINE:
            i += 1
            if self.peek(i) is None:
                return False
        if self.peek(i).type != TokenType.IDENTIFIER:
            return False
        depth = 0
        while True:
            t = self.peek(i)
            if t is None:
                return False
            if t.type == TokenType.OPERATOR:
                return depth == 0
            if t.type == TokenType.IDENTIFIER:
                i += 1
            elif t.type in (TokenType.LT, TokenType.LBRACKET):
                depth += 1
                i += 1
            elif t.type in (TokenType.GT, TokenType.RBRACKET):
                if depth == 0:
                    return False
                depth -= 1
                i += 1
            elif t.type == TokenType.COMMA and depth > 0:
                i += 1
            else:
                return False

    def _extract_format_literals(self, fmt):
        literals = []
        cur = ""
        i = 0
        n = len(fmt)
        while i < n:
            ch = fmt[i]
            if ch == "\\" and i + 1 < n and fmt[i + 1] == "%":
                cur += "%"
                i += 2
            elif ch in " \t%":
                if cur:
                    literals.append(cur)
                    cur = ""
                i += 1
            else:
                cur += ch
                i += 1
        if cur:
            literals.append(cur)
        return literals

    @staticmethod
    def _to_internal_template(fmt):
        out = []
        opnd = 1
        cur = ""
        i = 0
        n = len(fmt)
        while i < n:
            ch = fmt[i]
            if ch == "\\" and i + 1 < n and fmt[i + 1] == "%":
                cur += "%"
                i += 2
            elif ch in " \t%":
                if cur:
                    out.append("%")
                    cur = ""
                if ch == "%":
                    out.append(f"&{opnd}")
                    opnd += 1
                i += 1
            else:
                cur += ch
                i += 1
        if cur:
            out.append("%")
        return " ".join(out)

    def operator_func_def(self):
        inline = False
        if self.check(TokenType.INLINE):
            inline = True
            self.advance()
        ret_tok = self.peek()
        ret_type = self._parse_type()
        self.expect(TokenType.OPERATOR)
        self.expect(TokenType.LBRACKET)
        op_tokens = [self.expect(TokenType.STRING, "Expected operator token string").value]
        while self.check(TokenType.COMMA):
            self.advance()
            op_tokens.append(self.expect(TokenType.STRING, "Expected operator token string").value)
        self.expect(TokenType.RBRACKET)
        self.expect(TokenType.LPAREN)
        fmt_tok = self.expect(TokenType.STRING, "Expected operator format string")
        literals = self._extract_format_literals(fmt_tok.value)
        if literals != op_tokens:
            self.error(
                f"Operator tokens in format '{fmt_tok.value}' do not match "
                f"[{', '.join(op_tokens)}]"
            )
        self.expect(TokenType.COMMA)
        params = []
        varargs = None
        kwargs = None
        if not self.check(TokenType.RPAREN):
            self._parse_params(params)
            while self.check(TokenType.COMMA):
                self.advance()
                if self.check(TokenType.STAR):
                    self.advance()
                    if self.check(TokenType.STAR):
                        self.advance()
                        kwargs = self.expect(TokenType.IDENTIFIER).value
                        break
                    else:
                        varargs = self.expect(TokenType.IDENTIFIER).value
                        break
                else:
                    self._parse_params(params)
        self.expect(TokenType.RPAREN)
        self._block_intro()
        body = self._parse_body()
        internal_fmt = self._to_internal_template(fmt_tok.value)
        node = OperatorFuncDef(tuple(op_tokens), params, ret_type, body,
                               varargs, kwargs, False, False, inline, internal_fmt)
        self._pos(node, ret_tok)
        self._register_operator(OperatorDef(ret_type, list(op_tokens), internal_fmt))
        return node

    def _validate_opdef(self, node):
        parts = self._parse_format_template(node.format_template)
        if parts is None:
            self.error(
                f"Invalid operator format template '{node.format_template}'"
            )
        op_count = sum(1 for p in parts if p[0] == "%")
        if op_count != len(node.operator_tokens):
            self.error(
                f"Operator '{' '.join(node.operator_tokens)}': format has "
                f"{op_count} '%' placeholder(s) but the operator defines "
                f"{len(node.operator_tokens)} token(s)"
            )
        opnds = [p[1] for p in parts if p[0] == "&"]
        if not opnds or opnds != list(range(1, len(opnds) + 1)):
            self.error(
                f"Operator format must reference operands &1,&2,... in order: "
                f"'{node.format_template}'"
            )
        if parts[0][0] != "&" or parts[-1][0] != "&":
            self.error(
                "Only infix operator formats are supported (the format must "
                "start and end with an operand)"
            )

    def _register_operator(self, node):
        self.operator_registry[tuple(node.operator_tokens)] = (
            node.return_type, node.format_template
        )
        items = []
        for key, (ret, fmt) in self.operator_registry.items():
            parts = self._parse_format_template(fmt)
            if parts is None:
                continue
            op_count = sum(1 for p in parts if p[0] == "%")
            items.append((op_count, key, ret, fmt))
        items.sort(key=lambda x: x[0], reverse=True)
        self._custom_ops = [(k, r, f) for _, k, r, f in items]

    def _try_custom_operator(self, left):
        if not self._custom_ops:
            return None
        for op_tokens, ret_type, fmt in self._custom_ops:
            node = self._match_operator_template(left, op_tokens, fmt)
            if node is not None:
                return node
        return None

    def _match_operator_template(self, left, op_tokens, fmt):
        parts = self._parse_format_template(fmt)
        if parts is None:
            return None
        if sum(1 for p in parts if p[0] == "%") != len(op_tokens):
            return None
        saved = self.pos
        operands = [left]
        op_index = 0
        for kind, val in parts:
            if kind == "&":
                n = val
                if n == 1:
                    continue
                if n != len(operands) + 1:
                    self.pos = saved
                    return None
                operand = self.unary()
                operands.append(operand)
            else:
                tok = self.peek()
                if tok is None or tok.value != op_tokens[op_index]:
                    self.pos = saved
                    return None
                self.advance()
                op_index += 1
        node = OperatorExpr(tuple(op_tokens), operands, fmt)
        node.line = getattr(left, 'line', 0)
        node.col = getattr(left, 'col', 0)
        return node

    def var_decl(self):
        self.advance()
        type_name = None
        if self._is_type_token():
            type_name = self._parse_type()
        name = self.expect(TokenType.IDENTIFIER, "Expected variable name").value
        value = None
        if self.check(TokenType.ASSIGN, TokenType.LE, TokenType.LEFT_ASSIGN, TokenType.RIGHT_ASSIGN):
            self.advance()
            value = self.expression()
        return VarDecl(name, type_name, value)

    def _is_type_token(self):
        if not self.check(TokenType.IDENTIFIER):
            return False
        nxt = self.peek(1)
        if nxt is None:
            return False
        if nxt.type == TokenType.IDENTIFIER:
            return True
        if nxt.type == TokenType.LT:
            depth = 1
            i = 2
            while depth > 0 and self.peek(i):
                t = self.peek(i).type
                if t == TokenType.LT:
                    depth += 1
                elif t == TokenType.GT:
                    depth -= 1
                elif t == TokenType.RIGHT_SHIFT:
                    depth -= min(depth, 2)
                i += 1
            if depth != 0:
                return False
            after = self.peek(i)
            return after is not None and after.type == TokenType.IDENTIFIER
        return False

    def _parse_type(self):
        tok = self.advance()

        if tok.type == TokenType.LBRACKET:
            type_name = self._parse_type()
            result = f"[{type_name}"
            while self.check(TokenType.COMMA):
                self.advance()
                type_name = self._parse_type()
                result += f", {type_name}"
            self.expect(TokenType.RBRACKET, "Expected ]")
            result += "]"
            return result

        type_name = tok.value
        
        while self.check(TokenType.LT):
            self.advance()  # <
            params = [self._parse_type()]
            while self.check(TokenType.COMMA):
                self.advance()
                params.append(self._parse_type())
            type_name = f"{type_name}<{', '.join(params)}>"
            self._expect_gt()
        return type_name

    def _expect_gt(self):
        if self.check(TokenType.GT):
            self.advance()
        elif self.check(TokenType.RIGHT_SHIFT):
            self.advance() 
            from .tokens import Token
            gt_tok = Token(TokenType.GT, ">", self.peek().line if self.peek() else 1, 1)
            self.push_back(gt_tok)
        else:
            self.error("Expected > in type annotation")

    def import_stmt(self):
        self.advance()
        module_parts = []
        while self.check(TokenType.IDENTIFIER):
            module_parts.append(self.advance().value)
            if self.check(TokenType.DOT):
                self.advance()
            else:
                break
        module = ".".join(module_parts)
        alias = None
        if self.check(TokenType.AS):
            self.advance()
            alias = self.expect(TokenType.IDENTIFIER).value
        return ImportStmt(module, alias)

    def from_import(self):
        self.advance()
        module_parts = []
        while self.check(TokenType.IDENTIFIER):
            module_parts.append(self.advance().value)
            if self.check(TokenType.DOT):
                self.advance()
            else:
                break
        module = ".".join(module_parts)
        self.expect(TokenType.IMPORT)
        names = []
        if self.check(TokenType.STAR):
            self.advance()
            names.append(("*", None))
        else:
            while True:
                name = self.expect(TokenType.IDENTIFIER).value
                alias = None
                if self.check(TokenType.AS):
                    self.advance()
                    alias = self.expect(TokenType.IDENTIFIER).value
                names.append((name, alias))
                if not self.check(TokenType.COMMA):
                    break
                self.advance()
        return FromImportStmt(module, names)

    def if_stmt(self):
        self.advance()
        condition = self.expression()
        self._block_intro()
        then_body = self._parse_body()
        elif_branches = []
        else_body = None
        while self.check(TokenType.ELSE, TokenType.ELIF):
            if self.check(TokenType.ELIF):
                self.advance()
                elif_cond = self.expression()
                self._block_intro()
                elif_body = self._parse_body()
                elif_branches.append((elif_cond, elif_body))
            else:
                self.advance()
                if self.check(TokenType.IF):
                    self.advance()
                    elif_cond = self.expression()
                    self._block_intro()
                    elif_body = self._parse_body()
                    elif_branches.append((elif_cond, elif_body))
                else:
                    self._block_intro()
                    else_body = self._parse_body()
                    break
        return IfStmt(condition, then_body, else_body, elif_branches)

    def for_loop(self):
        t = self.advance()
        var = self.primary()
        self.expect(TokenType.IN)
        iterable = self.expression()
        self._block_intro()
        body = self._parse_body()
        node = ForLoop(var, iterable, body)
        self._pos(node, t)
        return node

    def while_loop(self):
        t = self.advance()
        condition = self.expression()
        self._block_intro()
        body = self._parse_body()
        node = WhileLoop(condition, body)
        self._pos(node, t)
        return node

    def with_stmt(self):
        self.advance()
        expr = self.expression()
        alias = None
        if self.check(TokenType.AS):
            self.advance()
            alias = self.expect(TokenType.IDENTIFIER).value
        self._block_intro()
        body = self._parse_body()
        return WithStmt(expr, alias, body)

    def try_stmt(self):
        self.advance()
        self._block_intro()
        try_body = self._parse_body()
        have_clauses = []
        while self.check(TokenType.HAVE) or self.check(TokenType.EXCEPT):
            self.advance()
            error_types = []
            alias = None
            if self.check(TokenType.LPAREN):
                self.advance()
                while True:
                    if self.check(TokenType.IDENTIFIER):
                        error_types.append(self.advance().value)
                    if not self.check(TokenType.COMMA):
                        break
                    self.advance()
                self.expect(TokenType.RPAREN)
            elif self.check(TokenType.IDENTIFIER):
                error_types.append(self.advance().value)
            if self.check(TokenType.AS):
                self.advance()
                alias = self.expect(TokenType.IDENTIFIER).value
            self._block_intro()
            have_body = self._parse_body()
            have_clauses.append(HaveClause(error_types, alias, have_body))
        return TryStmt(try_body, have_clauses)

    def raise_stmt(self):
        self.advance()
        expr = None
        if not self.is_at_end() and not self.check(TokenType.NEWLINE):
            expr = self.expression()
        return RaiseStmt(expr)

    def return_stmt(self):
        self.advance()
        if self.check(TokenType.LPAREN):
            self.advance()
            value = self.expression()
            self.expect(TokenType.RPAREN)
        elif not self.is_at_end() and not self.check(TokenType.NEWLINE):
            value = self.expression()
        else:
            value = None
        return ReturnStmt(value)

    def delete_stmt(self):
        self.advance()
        target = self.expression()
        return DeleteStmt(target)

    def print_stmt(self):
        self.advance()
        self.expect(TokenType.LPAREN)
        values = []
        end = "\n"
        space = ""
        file = None

        if not self.check(TokenType.RPAREN):
            while True:
                if self.check(TokenType.IDENTIFIER):
                    name = self.peek().value
                    if name in ("end", "space", "file") and \
                       self.peek(1) and self.peek(1).type == TokenType.ASSIGN:
                        self.advance()
                        self.advance()
                        val = self._parse_kw_string()
                        if name == "end":
                            end = val
                        elif name == "space":
                            space = val
                        elif name == "file":
                            file = val
                    else:
                        values.append(self.expression())
                else:
                    values.append(self.expression())
                if not self.check(TokenType.COMMA):
                    break
                self.advance()

        self.expect(TokenType.RPAREN)
        return PrintStmt(values, end, space, file)

    def _parse_kw_string(self):
        if self.check(TokenType.STRING):
            return self.advance().value
        elif self.check(TokenType.CHAR_LIT):
            return self.advance().value
        elif self.check(TokenType.IDENTIFIER):
            return self.advance().value
        return ""

    def input_stmt(self):
        self.advance()
        self.expect(TokenType.LPAREN)
        prompt = None
        if not self.check(TokenType.RPAREN):
            prompt = self.expression()
        self.expect(TokenType.RPAREN)
        return InputStmt(prompt)

    def func_def(self):
        inline = False
        if self.check(TokenType.INLINE):
            inline = True
            self.advance()
        if not self.check(TokenType.DEF):
            self.error("Expected func or def after inline")
        self.advance()
        name_tok = self.expect(TokenType.IDENTIFIER)
        name = name_tok.value
        is_hidden = name.startswith("__")
        is_private = not is_hidden and name.startswith("_")

        self.expect(TokenType.LPAREN)
        params = []
        varargs = None
        kwargs = None
        if not self.check(TokenType.RPAREN):
            if self.check(TokenType.STAR):
                self.advance()
                if self.check(TokenType.STAR):
                    self.advance()
                    kwargs = self.expect(TokenType.IDENTIFIER).value
                else:
                    varargs = self.expect(TokenType.IDENTIFIER).value
            else:
                self._parse_params(params)
                while self.check(TokenType.COMMA):
                    self.advance()
                    if self.check(TokenType.STAR):
                        self.advance()
                        if self.check(TokenType.STAR):
                            self.advance()
                            kwargs = self.expect(TokenType.IDENTIFIER).value
                            break
                        else:
                            varargs = self.expect(TokenType.IDENTIFIER).value
                            break
                    else:
                        self._parse_params(params)
        self.expect(TokenType.RPAREN)

        return_type = None
        if self.check(TokenType.ARROW):
            self.advance()
            return_type = self._parse_type()

        self._block_intro()
        body = self._parse_body()
        return FuncDef(name, params, return_type, body, varargs, kwargs,
                       is_hidden, is_private, is_inline=inline)

    def _parse_params(self, params):
        ptype = None
        if self._is_type_token():
            ptype = self._parse_type()
        pname = self.expect(TokenType.IDENTIFIER).value
        default = None
        if self.check(TokenType.ASSIGN):
            self.advance()
            default = self.expression()
        params.append((pname, ptype, default))

    def _parse_lambda(self):
        self.advance()
        params = []
        varargs = None
        kwargs = None
        if not self.check(TokenType.COLON):
            if self.check(TokenType.STAR):
                self.advance()
                if self.check(TokenType.STAR):
                    self.advance()
                    kwargs = self.expect(TokenType.IDENTIFIER).value
                else:
                    varargs = self.expect(TokenType.IDENTIFIER).value
            else:
                self._parse_params(params)
                while self.check(TokenType.COMMA):
                    self.advance()
                    if self.check(TokenType.STAR):
                        self.advance()
                        if self.check(TokenType.STAR):
                            self.advance()
                            kwargs = self.expect(TokenType.IDENTIFIER).value
                            break
                        else:
                            varargs = self.expect(TokenType.IDENTIFIER).value
                            break
                    else:
                        self._parse_params(params)
        self.expect(TokenType.COLON)
        body = self.expression()
        return LambdaExpr(params, body, varargs, kwargs)

    def class_def(self):
        inline = False
        if self.check(TokenType.INLINE):
            inline = True
            self.advance()
        self.advance()
        name_tok = self.expect(TokenType.IDENTIFIER)
        name = name_tok.value
        is_hidden = name.startswith("__")
        is_private = not is_hidden and name.startswith("_")

        type_params = []
        if self.check(TokenType.LT):
            self.advance()
            type_params.append(self.expect(TokenType.IDENTIFIER, "Expected type parameter").value)
            while self.check(TokenType.COMMA):
                self.advance()
                type_params.append(self.expect(TokenType.IDENTIFIER, "Expected type parameter").value)
            self.expect(TokenType.GT, "Expected > after type parameters")

        bases = []
        if self.check(TokenType.LPAREN):
            self.advance()
            bases.append(self.expect(TokenType.IDENTIFIER).value)
            while self.check(TokenType.COMMA):
                self.advance()
                bases.append(self.expect(TokenType.IDENTIFIER).value)
            self.expect(TokenType.RPAREN)

        self._block_intro()
        body_stmts = self._parse_class_body()
        return ClassDef(name, type_params, bases, body_stmts, is_hidden, is_private, inline)

    def _parse_class_body(self):
        if self.check(TokenType.LBRACE):
            self.expect(TokenType.LBRACE)
            stmts = []
            while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
                if self.check(TokenType.NEWLINE) or self.check(TokenType.INDENT) or self.check(TokenType.DEDENT):
                    self.advance()
                    continue
                stmts.append(self.statement())
            self.expect(TokenType.RBRACE)
            if self.check(TokenType.NEWLINE):
                self.advance()
            return stmts
        self.skip_newlines()
        self.expect(TokenType.INDENT, "Expected indented class body")
        stmts = []
        while not self.check(TokenType.DEDENT) and not self.check(TokenType.EOF):
            self.skip_newlines()
            if self.check(TokenType.DEDENT) or self.check(TokenType.EOF):
                break
            stmts.append(self.statement())
            self.skip_newlines()
        self.expect(TokenType.DEDENT, "Expected DEDENT")
        return stmts

    def struct_def(self):
        inline = False
        if self.check(TokenType.INLINE):
            inline = True
            self.advance()
        self.advance()
        name_tok = self.expect(TokenType.IDENTIFIER)
        name = name_tok.value
        is_hidden = name.startswith("__")
        is_private = not is_hidden and name.startswith("_")

        self._block_intro()
        body_stmts = self._parse_class_body()
        return StructDef(name, body_stmts, is_hidden, is_private, inline)

    def expression(self):
        return self.assignment()

    def assignment(self):
        expr = self.ternary()

        if self.check(TokenType.WALRUS_LEFT):
            self.advance()
            value = self.assignment()
            return WalrusExpr(expr, value)
        if self.check(TokenType.WALRUS_RIGHT):
            self.advance()
            target = self.assignment()
            return WalrusExpr(target, expr)

        if self.peek() and self.peek().type in self.RIGHT_TO_LEFT_OP:
            op_tok = self.advance()
            op_str = self.RIGHT_TO_LEFT_OP[op_tok.type]
            target = self.assignment()
            return Assign(target, expr, op_str)

        if self.check(TokenType.ASSIGN):
            self.advance()
            value = self.assignment()
            return Assign(expr, value, "=")
        if self.check(TokenType.LEFT_ASSIGN):
            self.advance()
            value = self.assignment()
            return Assign(expr, value, "=")
        if self.check(TokenType.RIGHT_ASSIGN):
            self.advance()
            target = self.assignment()
            return Assign(target, expr, "=")
        if self.peek() and self.peek().type in self.COMPOUND_OPS:
            op_tok = self.advance()
            op_str = self.COMPOUND_OPS[op_tok.type]
            value = self.assignment()
            return Assign(expr, value, op_str)

        return expr

    def ternary(self):
        expr = self.logic_or()

        if self.check(TokenType.QUESTION):
            self.advance()
            true_expr = self.expression()
            self.expect(TokenType.COLON)
            false_expr = self.ternary()
            return TernaryExpr(expr, true_expr, false_expr, "c")

        if self.check(TokenType.IF):
            self.advance()
            condition = self.logic_or()
            self.expect(TokenType.ELSE)
            false_expr = self.ternary()
            return TernaryExpr(condition, expr, false_expr, "python")

        return expr

    def logic_or(self):
        left = self.logic_and()
        while self.check(TokenType.LOG_OR, TokenType.OR):
            op = self.advance().value
            right = self.logic_and()
            left = BinaryOp(op, left, right)
        return left

    def logic_and(self):
        left = self.equality()
        while self.check(TokenType.LOG_AND, TokenType.AND):
            op = self.advance().value
            right = self.equality()
            left = BinaryOp(op, left, right)
        return left

    def equality(self):
        left = self.comparison()
        while self.check(TokenType.EQ, TokenType.NE):
            op = self.advance().value
            right = self.comparison()
            left = BinaryOp(op, left, right)
        return left

    def comparison(self):
        left = self.bitwise_or()
        while self.check(TokenType.GT, TokenType.LT, TokenType.GE, TokenType.LE,
                         TokenType.IS, TokenType.IN):
            op = self.advance().value
            right = self.bitwise_or()
            left = BinaryOp(op, left, right)
        return left

    def bitwise_or(self):
        left = self.bitwise_xor()
        while self.check(TokenType.BIT_OR):
            self.advance()
            right = self.bitwise_xor()
            left = BinaryOp("|", left, right)
        return left

    def bitwise_xor(self):
        left = self.bitwise_and()
        while self.check(TokenType.BIT_XOR):
            self.advance()
            right = self.bitwise_and()
            left = BinaryOp("^", left, right)
        return left

    def bitwise_and(self):
        left = self.shift()
        while self.check(TokenType.BIT_AND):
            self.advance()
            right = self.shift()
            left = BinaryOp("&", left, right)
        return left

    def shift(self):
        left = self.addition()
        while self.check(TokenType.RIGHT_SHIFT, TokenType.LEFT_SHIFT):
            op = self.advance().value
            right = self.addition()
            left = BinaryOp(op, left, right)
        return left

    def addition(self):
        left = self.multiplication()
        while self.check(TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self.multiplication()
            left = BinaryOp(op, left, right)
        return left

    def multiplication(self):
        left = self.unary()
        while True:
            custom = self._try_custom_operator(left)
            if custom is not None:
                left = custom
                continue
            if self.check(TokenType.STAR, TokenType.SLASH, TokenType.DOUBLE_SLASH,
                         TokenType.PERCENT, TokenType.DOUBLE_STAR):
                op = self.advance().value
                right = self.unary()
                left = BinaryOp(op, left, right)
                continue
            break
        return left

    def unary(self):
        if self.check(TokenType.MINUS):
            t = self.advance()
            node = UnaryOp("-", self.unary())
            self._pos(node, t)
            return node
        if self.check(TokenType.BIT_NOT):
            t = self.advance()
            node = UnaryOp("~", self.unary())
            self._pos(node, t)
            return node
        if self.check(TokenType.NOT):
            t = self.advance()
            node = UnaryOp("not", self.unary())
            self._pos(node, t)
            return node
        if self.check(TokenType.PLUS):
            self.advance()
            return self.unary()
        return self.member_access()

    def member_access(self):
        expr = self.primary()

        while True:
            if self.check(TokenType.DOT):
                self.advance()
                member = self.expect(TokenType.IDENTIFIER).value
                
                if self.check(TokenType.LPAREN):
                    self.advance()
                    args, star_arg, star_star_arg = self._parse_args()
                    self.expect(TokenType.RPAREN)
                    expr = Call(MemberAccess(expr, member, "dot"), args, star_arg, star_star_arg)
                else:
                    expr = MemberAccess(expr, member, "dot")
            elif self.check(TokenType.ARROW):
                self.advance()
                member = self.expect(TokenType.IDENTIFIER).value
                if self.check(TokenType.LPAREN):
                    self.advance()
                    args, star_arg, star_star_arg = self._parse_args()
                    self.expect(TokenType.RPAREN)
                    expr = Call(MemberAccess(expr, member, "arrow"), args, star_arg, star_star_arg)
                else:
                    expr = MemberAccess(expr, member, "arrow")

            elif self.check(TokenType.LT) and self.peek(1) and self.peek(1).type == TokenType.MINUS:
                self.advance()
                self.advance()
                if isinstance(expr, Identifier):
                    member_name = expr.name
                    expr = MemberAccess(
                        Identifier("__reverse_target__"), member_name, "reverse_arrow"
                    )
            elif self.check(TokenType.LBRACKET):
                self.advance()
                index = self.expression()
                self.expect(TokenType.RBRACKET)
                expr = IndexAccess(expr, index)

            elif self.check(TokenType.LPAREN):
                self.advance()
                args, star_arg, star_star_arg = self._parse_args()
                self.expect(TokenType.RPAREN)
                expr = Call(expr, args, star_arg, star_star_arg)

            else:
                break

        return expr

    def _parse_args(self):
        args = []
        star_arg = None
        star_star_arg = None
        if not self.check(TokenType.RPAREN):
            if not self.check(TokenType.STAR):
                args.append(self.expression())
                while self.check(TokenType.COMMA):
                    self.advance()
                    if self.check(TokenType.RPAREN):
                        break
                    if self.check(TokenType.STAR):
                        if self.peek(1) and self.peek(1).type == TokenType.STAR:
                            self.advance()
                            self.advance()
                            star_star_arg = self.expression()
                            break
                        else:
                            self.advance()
                            star_arg = self.expression()
                            if self.check(TokenType.COMMA):
                                self.advance()
                                if self.check(TokenType.STAR) and self.peek(1) and self.peek(1).type == TokenType.STAR:
                                    self.advance()
                                    self.advance()
                                    star_star_arg = self.expression()
                            break
                    else:
                        args.append(self.expression())
            else:
                if self.peek(1) and self.peek(1).type == TokenType.STAR:
                    self.advance()
                    self.advance()
                    star_star_arg = self.expression()
                else:
                    self.advance()
                    star_arg = self.expression()
                    if self.check(TokenType.COMMA):
                        self.advance()
                        if self.check(TokenType.STAR) and self.peek(1) and self.peek(1).type == TokenType.STAR:
                            self.advance()
                            self.advance()
                            star_star_arg = self.expression()
        return args, star_arg, star_star_arg

    def primary(self):
        tok = self.peek()
        if not tok:
            self.error("Unexpected end of input")

        if self.check(TokenType.LAMBDA):
            return self._parse_lambda()

        if self.check(TokenType.INTEGER):
            t = self.advance()
            node = NumberLiteral(t.value)
            self._pos(node, t)
            return node

        if self.check(TokenType.FLOAT_LIT):
            t = self.advance()
            node = NumberLiteral(t.value)
            self._pos(node, t)
            return node

        if self.check(TokenType.STRING):
            t = self.advance()
            node = StringLiteral(t.value)
            self._pos(node, t)
            return node

        if self.check(TokenType.CHAR_LIT):
            t = self.advance()
            node = CharLiteral(t.value)
            self._pos(node, t)
            return node

        if self.check(TokenType.BOOL_LIT):
            t = self.advance()
            node = BoolLiteral(t.value == "True")
            self._pos(node, t)
            return node

        if self.check(TokenType.IDENTIFIER):
            t = self.advance()
            node = Identifier(t.value)
            self._pos(node, t)
            return node

        if self.check(TokenType.LPAREN):
            self.advance()
            if self.check(TokenType.RPAREN):
                self.advance()
                return QueueLiteral([])
            expr = self.expression()
            if self.check(TokenType.COMMA):
                elements = [expr]
                while self.check(TokenType.COMMA):
                    self.advance()
                    if self.check(TokenType.RPAREN):
                        break
                    elements.append(self.expression())
                self.expect(TokenType.RPAREN)
                return QueueLiteral(elements)
            self.expect(TokenType.RPAREN)
            return expr

        if self.check(TokenType.LBRACKET):
            self.advance()
            elements = []
            if not self.check(TokenType.RBRACKET):
                elements.append(self.expression())
                while self.check(TokenType.COMMA):
                    self.advance()
                    if self.check(TokenType.RBRACKET):
                        break
                    elements.append(self.expression())
            self.expect(TokenType.RBRACKET)
            return ListLiteral(elements)

        if self.check(TokenType.LBRACE):
            self.advance()
            if self.check(TokenType.RBRACE):
                self.advance()
                return MapLiteral([])
            first = self.expression()
            if self.check(TokenType.COLON):
                self.advance()
                second = self.expression()
                if isinstance(first, StringLiteral) and first.value == "first" and self.check(TokenType.COMMA):
                    self.advance()
                    key2 = self.expect(TokenType.STRING)
                    if key2.value == "second":
                        self.expect(TokenType.COLON)
                        second2 = self.expression()
                        self.expect(TokenType.RBRACE)
                        return PairLiteral(second, second2)
                entries = [(first, second)]
                while self.check(TokenType.COMMA):
                    self.advance()
                    k = self.expression()
                    self.expect(TokenType.COLON)
                    v = self.expression()
                    entries.append((k, v))
                self.expect(TokenType.RBRACE)
                return MapLiteral(entries)
            elif self.check(TokenType.COMMA):
                elements = [first]
                while self.check(TokenType.COMMA):
                    self.advance()
                    elements.append(self.expression())
                self.expect(TokenType.RBRACE)
                return SetLiteral(elements)
            else:
                self.expect(TokenType.RBRACE)
                return SetLiteral([first])

        self.error(f"Unexpected token '{tok.value}'")
