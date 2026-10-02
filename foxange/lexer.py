from .tokens import Token, TokenType, KEYWORDS, RIGHT_COMPOUND_MAP

class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []
        self.indent_stack = [0]
        self.paren_depth = 0

    def error(self, msg):
        raise SyntaxError(f"Lexer Error at line {self.line}, col {self.col}: {msg}")

    def peek(self, offset=0):
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else None

    def advance(self):
        ch = self.peek()
        if ch is not None:
            self.pos += 1
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
        return ch

    def match(self, expected):
        if self.peek() == expected:
            self.advance()
            return True
        return False

    def skip_whitespace(self):
        while self.peek() in (" ", "\t", "\r"):
            self.advance()

    def skip_comment(self):
        if self.peek() == "#":
            self.advance()
            if self.peek() == "#":
                self.advance()
            while self.peek() and self.peek() != "\n":
                self.advance()

    def read_string(self, quote):
        start_line, start_col = self.line, self.col
        self.advance()
        s = ""
        while self.peek() and self.peek() != quote:
            if self.peek() == "\\":
                self.advance()
                esc = self.advance()
                if esc == "n":
                    s += "\n"
                elif esc == "t":
                    s += "\t"
                elif esc == "r":
                    s += "\r"
                elif esc == "0":
                    octal_digits = ""
                    for _ in range(2):
                        nxt = self.peek()
                        if nxt and nxt in "01234567":
                            octal_digits += self.advance()
                        else:
                            break
                    if octal_digits:
                        s += chr(int(octal_digits, 8))
                    else:
                        s += "\0"
                elif esc == "x":
                    hex_digits = ""
                    for _ in range(2):
                        nxt = self.peek()
                        if nxt and nxt in "0123456789abcdefABCDEF":
                            hex_digits += self.advance()
                        else:
                            break
                    if hex_digits:
                        s += chr(int(hex_digits, 16))
                    else:
                        s += "\\x"
                elif esc == "e":
                    s += "\033"
                elif esc == "\\":
                    s += "\\"
                elif esc == quote:
                    s += quote
                else:
                    s += "\\" + (esc or "")
            else:
                s += self.advance()
        if not self.peek():
            self.error("Unterminated string literal")
        self.advance()
        return Token(TokenType.STRING, s, start_line, start_col)

    def read_char(self):
        start_line, start_col = self.line, self.col
        self.advance()
        ch = ""
        if self.peek() == "\\":
            self.advance()
            esc = self.advance()
            if esc == "n":
                ch = "\n"
            elif esc == "t":
                ch = "\t"
            elif esc == "r":
                ch = "\r"
            elif esc == "0":
                octal_digits = ""
                for _ in range(2):
                    nxt = self.peek()
                    if nxt and nxt in "01234567":
                        octal_digits += self.advance()
                    else:
                        break
                ch = chr(int(octal_digits, 8)) if octal_digits else "\0"
            elif esc == "x":
                hex_digits = ""
                for _ in range(2):
                    nxt = self.peek()
                    if nxt and nxt in "0123456789abcdefABCDEF":
                        hex_digits += self.advance()
                    else:
                        break
                ch = chr(int(hex_digits, 16)) if hex_digits else "\\x"
            elif esc == "e":
                ch = "\033"
            elif esc == "\\":
                ch = "\\"
            elif esc == "'":
                ch = "'"
            else:
                ch = "\\" + (esc or "")
        else:
            ch = self.advance() or ""
        if not self.match("'"):
            self.error("Unterminated char literal")
        return Token(TokenType.CHAR_LIT, ch, start_line, start_col)

    def read_number(self):
        start_line, start_col = self.line, self.col
        num = ""
        is_float = False
        while self.peek() and self.peek().isdigit():
            num += self.advance()
        if self.peek() == "." and self.peek(1) and self.peek(1).isdigit():
            is_float = True
            num += self.advance()
            while self.peek() and self.peek().isdigit():
                num += self.advance()
        if self.peek() in ("e", "E"):
            is_float = True
            num += self.advance()
            if self.peek() in ("+", "-"):
                num += self.advance()
            while self.peek() and self.peek().isdigit():
                num += self.advance()
        if self.peek() and self.peek().isalpha():
            self.error(f"Invalid number: {num}{self.peek()}")
        if is_float:
            return Token(TokenType.FLOAT_LIT, float(num), start_line, start_col)
        return Token(TokenType.INTEGER, int(num), start_line, start_col)

    def read_identifier(self):
        start_line, start_col = self.line, self.col
        ident = ""
        while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
            ident += self.advance()
        tok_type = KEYWORDS.get(ident, TokenType.IDENTIFIER)
        return Token(tok_type, ident, start_line, start_col)

    def tokenize(self):

        raw_tokens = self._tokenize_raw()
        result = self._process_indent(raw_tokens)
        eof_idx = None
        dedents_after_eof = []
        for i, tok in enumerate(result):
            if tok.type == TokenType.EOF:
                eof_idx = i
        if eof_idx is not None:
            for i in range(eof_idx + 1, len(result)):
                if result[i].type == TokenType.DEDENT:
                    dedents_after_eof.append(result[i])
            if dedents_after_eof:
                result = [t for t in result if not (t.type == TokenType.DEDENT and t in dedents_after_eof)]
                for i, tok in enumerate(result):
                    if tok.type == TokenType.EOF:
                        for d in dedents_after_eof:
                            result.insert(i, d)
                        break

        return result

    def _tokenize_raw(self):
        tokens = []
        while self.pos < len(self.source):
            self.skip_comment()
            if self.pos >= len(self.source):
                break

            ch = self.peek()

            if ch == "\n":
                line, col = self.line, self.col
                self.advance()
                tokens.append(
                    Token(TokenType.NEWLINE, "\n", line, col)
                )
                continue

            if ch in (" ", "\t", "\r"):
                self.advance()
                continue

            if ch == '"':
                tokens.append(self.read_string('"'))
                continue

            if ch == "'":
                tokens.append(self.read_char())
                continue

            if ch.isdigit():
                tokens.append(self.read_number())
                continue

            if ch.isalpha() or ch == "_":
                tokens.append(self.read_identifier())
                continue

            line, col = self.line, self.col

            if ch == "=" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.EQ, "==", line, col))
                continue
            if ch == "=" and self.peek(1) == ":":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.WALRUS_RIGHT, "=:", line, col))
                continue
            if ch == "=" and self.peek(1) == ">":
                self.advance(); self.advance()
                if self.peek() == ">":
                    self.advance()
                    tokens.append(Token(TokenType.ASSIGN_RSHIFT, "=>>", line, col))
                else:
                    tokens.append(Token(TokenType.RIGHT_ASSIGN, "=>", line, col))
                continue
            if ch == "=" and self.peek(1) == "*":
                self.advance(); self.advance()
                if self.peek() == "*":
                    self.advance()
                    tokens.append(Token(TokenType.ASSIGN_DBLSTAR, "=**", line, col))
                else:
                    tokens.append(Token(TokenType.ASSIGN_STAR, "=*", line, col))
                continue
            if ch == "=" and self.peek(1) == "/":
                self.advance(); self.advance()
                if self.peek() == "/":
                    self.advance()
                    tokens.append(Token(TokenType.ASSIGN_DBLSLASH, "=//", line, col))
                else:
                    tokens.append(Token(TokenType.ASSIGN_SLASH, "=/", line, col))
                continue
            if ch == "=" and self.peek(1) == "+":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.ASSIGN_PLUS, "=+", line, col))
                continue
            if ch == "=" and self.peek(1) == "-":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.ASSIGN_MINUS, "=-", line, col))
                continue
            if ch == "=" and self.peek(1) == "%":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.ASSIGN_PERCENT, "=%", line, col))
                continue
            if ch == "=" and self.peek(1) == "&":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.ASSIGN_BITAND, "=&", line, col))
                continue
            if ch == "=" and self.peek(1) == "|":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.ASSIGN_BITOR, "=|", line, col))
                continue
            if ch == "=" and self.peek(1) == "~":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.ASSIGN_BITNOT, "=~", line, col))
                continue
            if ch == "=" and self.peek(1) == "^":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.ASSIGN_BITXOR, "=^", line, col))
                continue
            if ch == "=" and self.peek(1) == "<":
                self.advance(); self.advance()
                if self.peek() == "<":
                    self.advance()
                    tokens.append(Token(TokenType.ASSIGN_LSHIFT, "=<<", line, col))
                else:
                    self.error("Expected =<<")
                continue
            if ch == ":" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.WALRUS_LEFT, ":=", line, col))
                continue
            if ch == "!" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.NE, "!=", line, col))
                continue
            if ch == ">" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.GE, ">=", line, col))
                continue
            if ch == ">" and self.peek(1) == ">":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.RIGHT_SHIFT, ">>", line, col))
                continue
            if ch == "<" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.LE, "<=", line, col))
                continue
            if ch == "<" and self.peek(1) == "<":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.LEFT_SHIFT, "<<", line, col))
                continue
            if ch == "*" and self.peek(1) == "*":
                self.advance(); self.advance()
                if self.peek() == "=":
                    self.advance()
                    tokens.append(Token(TokenType.DBLSTAR_ASSIGN, "**=", line, col))
                else:
                    tokens.append(Token(TokenType.DOUBLE_STAR, "**", line, col))
                continue
            if ch == "/" and self.peek(1) == "/":
                self.advance(); self.advance()
                if self.peek() == "=":
                    self.advance()
                    tokens.append(Token(TokenType.DBLSLASH_ASSIGN, "//=", line, col))
                else:
                    tokens.append(Token(TokenType.DOUBLE_SLASH, "//", line, col))
                continue
            if ch == "&" and self.peek(1) == "&":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.LOG_AND, "&&", line, col))
                continue
            if ch == "|" and self.peek(1) == "|":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.LOG_OR, "||", line, col))
                continue
            if ch == "-" and self.peek(1) == ">":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.ARROW, "->", line, col))
                continue
            if ch == "+" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.PLUS_ASSIGN, "+=", line, col))
                continue
            if ch == "-" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.MINUS_ASSIGN, "-=", line, col))
                continue
            if ch == "*" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.STAR_ASSIGN, "*=", line, col))
                continue
            if ch == "/" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.SLASH_ASSIGN, "/=", line, col))
                continue
            if ch == "%" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.PERCENT_ASSIGN, "%=", line, col))
                continue
            if ch == "&" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.BITAND_ASSIGN, "&=", line, col))
                continue
            if ch == "|" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.BITOR_ASSIGN, "|=", line, col))
                continue
            if ch == "~" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.BITNOT_ASSIGN, "~=", line, col))
                continue
            if ch == "^" and self.peek(1) == "=":
                self.advance(); self.advance()
                tokens.append(Token(TokenType.BITXOR_ASSIGN, "^=", line, col))
                continue
            if ch == ">" and self.peek(1) == ">":
                self.advance(); self.advance()
                if self.peek() == "=":
                    self.advance()
                    tokens.append(Token(TokenType.RSHIFT_ASSIGN, ">>=", line, col))
                else:
                    tokens.append(Token(TokenType.RIGHT_SHIFT, ">>", line, col))
                continue
            if ch == "<" and self.peek(1) == "<":
                self.advance(); self.advance()
                if self.peek() == "=":
                    self.advance()
                    tokens.append(Token(TokenType.LSHIFT_ASSIGN, "<<=", line, col))
                else:
                    tokens.append(Token(TokenType.LEFT_SHIFT, "<<", line, col))
                continue
            single_map = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "%": TokenType.PERCENT,
                "=": TokenType.ASSIGN,
                ">": TokenType.GT,
                "<": TokenType.LT,
                "!": TokenType.NOT,
                "~": TokenType.BIT_NOT,
                "&": TokenType.BIT_AND,
                "|": TokenType.BIT_OR,
                "^": TokenType.BIT_XOR,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
                ",": TokenType.COMMA,
                ":": TokenType.COLON,
                ".": TokenType.DOT,
                ";": TokenType.SEMICOLON,
                "?": TokenType.QUESTION,
                "@": TokenType.AT,
            }
            if ch in single_map:
                self.advance()
                tokens.append(Token(single_map[ch], ch, line, col))
                continue

            self.error(f"Unexpected character: {ch!r}")

        tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return tokens

    def _process_indent(self, raw_tokens):
        result = []
        i = 0
        while i < len(raw_tokens):
            tok = raw_tokens[i]

            if tok.type == TokenType.NEWLINE:
                result.append(tok)
                i += 1
                col_offset = 0
                while i < len(raw_tokens):
                    nxt = raw_tokens[i]
                    if nxt.type == TokenType.NEWLINE:
                        result.append(nxt)
                        i += 1
                        col_offset = 0
                    elif nxt.type == TokenType.EOF:
                        break
                    else:
                        col_offset = nxt.col
                        break
                else:
                    break

                if i >= len(raw_tokens):
                    break
                indent_level = max(0, col_offset - 1)
                current_indent = self.indent_stack[-1]

                if indent_level > current_indent:
                    self.indent_stack.append(indent_level)
                    result.append(Token(TokenType.INDENT, "INDENT",
                                         raw_tokens[i].line, 1))
                elif indent_level < current_indent:
                    while len(self.indent_stack) > 1 and indent_level < self.indent_stack[-1]:
                        self.indent_stack.pop()
                        result.append(Token(TokenType.DEDENT, "DEDENT",
                                            raw_tokens[i].line, 1))
                    if indent_level != self.indent_stack[-1]:
                        self._lexer_error_lines(raw_tokens, i, indent_level)
                continue
            else:
                result.append(tok)
                i += 1

        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            result.append(Token(TokenType.DEDENT, "DEDENT",
                                raw_tokens[-1].line, 1) if raw_tokens else
                         Token(TokenType.DEDENT, "DEDENT", 1, 1))

        return result

    def _lexer_error_lines(self, raw_tokens, i, indent_level):
        tok = raw_tokens[i] if i < len(raw_tokens) else raw_tokens[-1]
        raise IndentationError(
            f"Unexpected indentation at line {tok.line}, col {tok.col}"
        )
