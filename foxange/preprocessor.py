import re
from .tokens import KEYWORDS, TokenType, Token


class Macro:
    def __init__(self, name, body, params=None):
        self.name = name
        self.body = body
        self.params = params

    @property
    def is_function_like(self):
        return self.params is not None

    def expand(self, match):
        if not self.params:
            return self.body

        args_str = match.group(1)
        args = self._parse_args(args_str)
        if len(args) != len(self.params):
            return match.group(0)

        result = self.body
        for param, arg in zip(self.params, args):
            result = re.sub(r"\b" + re.escape(param) + r"\b", arg.strip(), result)
        return result

    @staticmethod
    def _parse_args(s):
        args = []
        depth = 0
        current = []
        for ch in s:
            if ch == "," and depth == 0:
                args.append("".join(current))
                current = []
            else:
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth -= 1
                current.append(ch)
        if current:
            args.append("".join(current))
        return args


class Preprocessor:
    def __init__(self):
        self.macros = []
        self.keyword_additions = []
        self.import_once = False
        self.annotations = []
        self._stripped_lines = []

    def process(self, source):
        lines = source.split("\n")
        output_lines = []
        self.annotations = []
        self._stripped_lines = []

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("@define ") or stripped.startswith("#define "):
                self._handle_define(stripped)
                self._stripped_lines.append(idx)
                continue
            if stripped.startswith("@appendToken ") or stripped.startswith("#appendToken "):
                self._handle_append_token(stripped)
                self._stripped_lines.append(idx)
                continue
            if stripped == "@import once" or stripped == "@import onec":
                self.import_once = True
                self._stripped_lines.append(idx)
                continue
            if stripped.startswith("@return ") or stripped == "@return":
                self._handle_annotation("return", stripped, idx)
                self._stripped_lines.append(idx)
                continue
            if stripped.startswith("@true ") or stripped == "@true":
                self._handle_annotation("true", stripped, idx)
                self._stripped_lines.append(idx)
                continue
            if stripped.startswith("@false ") or stripped == "@false":
                self._handle_annotation("false", stripped, idx)
                self._stripped_lines.append(idx)
                continue
            output_lines.append(line)

        result = "\n".join(output_lines)

        if self.macros:
            result = self._apply_macros(result)

        self._apply_keywords()
        return result

    def _handle_annotation(self, kind, line, line_no):
        body = line[len("@" + kind):].strip()
        entry = {"kind": kind, "line": line_no, "expr": None, "expected": None, "raw": body}
        if kind == "return" and body:
            parts = body.rsplit(None, 1)
            if len(parts) == 2:
                entry["expr"] = parts[0]
                entry["expected"] = parts[1]
            else:
                entry["expr"] = body
        elif body:
            entry["expr"] = body
        self.annotations.append(entry)

    def _tokenize_expr(self, text):
        from .lexer import Lexer
        tokens = Lexer(text + "\n").tokenize()
        return [t for t in tokens if t.type not in (
            TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT, TokenType.EOF)]

    def apply_force_annotations(self, tokens):
        result = list(tokens)
        for ann in self.annotations:
            kind = ann.get("kind")
            if kind not in ("true", "false", "return"):
                continue
            expr = ann.get("expr")
            if not expr:
                continue
            pattern = self._tokenize_expr(expr)
            if not pattern:
                continue
            if kind == "return":
                expected = ann.get("expected")
                if not expected:
                    continue
                repl = self._tokenize_expr(expected)
            elif kind == "true":
                repl = [Token(TokenType.BOOL_LIT, "True", 0, 0)]
            else:
                repl = [Token(TokenType.BOOL_LIT, "False", 0, 0)]
            result = self._replace_token_sequence(result, pattern, repl)
        return self._apply_line_offset(result)

    def _apply_line_offset(self, tokens):
        stripped = sorted(self._stripped_lines)
        if not stripped:
            return tokens
        import bisect
        result = []
        for t in tokens:
            n = bisect.bisect_right(stripped, t.line)
            if n:
                result.append(Token(t.type, t.value, t.line + n, t.col))
            else:
                result.append(t)
        return result

    def _replace_token_sequence(self, tokens, pattern, repl):
        result = []
        i = 0
        n = len(tokens)
        m = len(pattern)
        while i < n:
            if self._match_at(tokens, i, pattern):
                anchor = tokens[i]
                for t in repl:
                    result.append(Token(t.type, t.value, anchor.line, anchor.col))
                i += m
            else:
                result.append(tokens[i])
                i += 1
        return result

    def _match_at(self, tokens, i, pattern):
        m = len(pattern)
        if i + m > len(tokens):
            return False
        for t in tokens[i:i + m]:
            if t.type in (TokenType.NEWLINE, TokenType.INDENT,
                          TokenType.DEDENT, TokenType.EOF):
                return False
        for j, pt in enumerate(pattern):
            st = tokens[i + j]
            if st.type != pt.type or st.value != pt.value:
                return False
        return True

    def _handle_define(self, line):
        content = line[len("@define "):].strip()
        if not content:
            return

        m = re.match(r"^([A-Za-z_]\w*)\s*\(([^)]*)\)\s+(.+)$", content)
        if m:
            name = m.group(1)
            params = [p.strip() for p in m.group(2).split(",") if p.strip()]
            body = m.group(3)
            self.macros.append(Macro(name, body, params))
            return

        parts = content.split(None, 1)
        if len(parts) >= 2:
            self.macros.append(Macro(parts[0], parts[1]))
        else:
            self.macros.append(Macro(content, ""))

    def _handle_append_token(self, line):
        parts = line.split(None, 2)
        if len(parts) < 3:
            return
        existing = parts[1]
        new_word = parts[2]
        self.keyword_additions.append((existing, new_word))

    def _apply_macros(self, source):
        for macro in self.macros:
            if macro.is_function_like:
                pattern = r"\b" + re.escape(macro.name) + r"\(" + \
                    r"([^()]*(?:\([^()]*\)[^()]*)*)\)"
            else:
                pattern = r"\b" + re.escape(macro.name) + r"\b"
            source = self._replace_outside_strings(source, pattern, macro)
        return source

    @staticmethod
    def _replace_outside_strings(source, pattern, macro):
        result = []
        i = 0
        str_pat = re.compile(r'"[^"\n]*"|\'[^\'\n]*\'')
        for m in str_pat.finditer(source):
            before = source[i:m.start()]
            if macro.is_function_like:
                before = re.sub(pattern, macro.expand, before)
            else:
                before = re.sub(pattern, macro.body, before)
            result.append(before)
            result.append(m.group(0))
            i = m.end()
        tail = source[i:]
        if macro.is_function_like:
            tail = re.sub(pattern, macro.expand, tail)
        else:
            tail = re.sub(pattern, macro.body, tail)
        result.append(tail)
        return "".join(result)

    def _apply_keywords(self):
        for existing, new_word in self.keyword_additions:
            if existing in KEYWORDS:
                KEYWORDS[new_word] = KEYWORDS[existing]
            elif existing != "IDENTIFIER":
                for kw, tt in list(KEYWORDS.items()):
                    if kw == existing:
                        KEYWORDS[new_word] = tt
                        break
