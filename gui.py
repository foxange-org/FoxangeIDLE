import os
import re
import sys
import io
import json
import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

_FX_DIR = os.path.dirname(os.path.abspath(__file__))
if _FX_DIR not in sys.path:
    sys.path.insert(0, _FX_DIR)

_FOXANGE_DIR = os.path.join(_FX_DIR, "foxange")
_SET_DIR = os.path.join(_FOXANGE_DIR, "lib", "set")
_RECORD_DIR = os.path.join(_FOXANGE_DIR, "lib", "record")
_HIGHLIGHT_FILE = os.path.join(_SET_DIR, "highlight.json")
_RECENT_FILE = os.path.join(_RECORD_DIR, "recent_files.json")
_COMPLETION_FILE = os.path.join(_SET_DIR, "completion.json")
_VIEW_FILE = os.path.join(_SET_DIR, "view.json")
_SETTING_FILE = os.path.join(_SET_DIR, "setting.json")
MAX_RECENT = 20

DEFAULT_SETTINGS = {
    "show_linenums": False,
    "show_diagnostics": False,
}

MAIN_SIZE = "880x850"
SHELL_SIZE = "880x850"
DIALOG_SIZE = "520x440"
COMPLETION_DIALOG_SIZE = "420x400"

COLORS = {
    "bg":           "#ffffff", "fg":          "#000000",
    "keyword":      "#ff7700", "builtin":     "#900090",
    "string":       "#00aa00", "comment":     "#dd0000",
    "number":       "#000000", "definition":  "#0000ff",
    "shell_prompt": "#0000dc", "shell_error": "#dc0000",
    "shell_blue":   "#0000c8", "sel_bg":      "#c8dcff",
    "input_prompt": "#0000c8", "linenum_fg":  "#909090",
    "linenum_bg":   "#f0f0f0",
    "diag_error":   "#dc0000", "diag_warn":  "#b8860b",
}


def load_highlight_colors():
    try:
        if not os.path.exists(_HIGHLIGHT_FILE):
            return
        with open(_HIGHLIGHT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for k, v in data.items():
                if k in COLORS and isinstance(v, str):
                    COLORS[k] = v
    except Exception as e:
        print(f"[Foxange] Failed to load highlight colors: {e}")


def save_highlight_colors():
    try:
        os.makedirs(_SET_DIR, exist_ok=True)
        with open(_HIGHLIGHT_FILE, "w", encoding="utf-8") as f:
            json.dump(COLORS, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Foxange] Failed to save highlight colors: {e}")


def reset_highlight_colors():
    defaults = {
        "keyword":      "#ff7700", "builtin":     "#900090",
        "string":       "#00aa00", "comment":     "#dd0000",
        "number":       "#000000", "definition":  "#0000ff",
    }
    COLORS.update(defaults)
    save_highlight_colors()


def load_recent_files():
    try:
        if not os.path.exists(_RECENT_FILE):
            return []
        with open(_RECENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(x) for x in data if isinstance(x, str)][:MAX_RECENT]
    except Exception as e:
        print(f"[Foxange] Failed to load recent files: {e}")
    return []


def save_recent_files(files):
    try:
        os.makedirs(_RECORD_DIR, exist_ok=True)
        with open(_RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(list(files)[:MAX_RECENT], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Foxange] Failed to save recent files: {e}")


def push_recent_file(files, path):
    try:
        path = os.path.abspath(path)
    except Exception:
        return files
    if path in files:
        files.remove(path)
    files.insert(0, path)
    del files[MAX_RECENT:]
    return files


def load_view_settings():
    data = {"show_linenums": False}
    try:
        if not os.path.exists(_VIEW_FILE):
            return data
        with open(_VIEW_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            data["show_linenums"] = bool(raw.get("show_linenums", False))
    except Exception as e:
        print(f"[Foxange] Failed to load view settings: {e}")
    return data


def save_view_settings(data):
    try:
        os.makedirs(_SET_DIR, exist_ok=True)
        with open(_VIEW_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Foxange] Failed to save view settings: {e}")


def load_settings():
    data = dict(DEFAULT_SETTINGS)
    try:
        if os.path.exists(_SETTING_FILE):
            with open(_SETTING_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                for k in DEFAULT_SETTINGS:
                    if k in raw:
                        data[k] = bool(raw[k])
                return data
    except Exception as e:
        print(f"[Foxange] Failed to load settings: {e}")
    try:
        if os.path.exists(_VIEW_FILE):
            with open(_VIEW_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict) and "show_linenums" in raw:
                data["show_linenums"] = bool(raw["show_linenums"])
    except Exception:
        pass
    return data


def save_settings(data):
    try:
        os.makedirs(_SET_DIR, exist_ok=True)
        with open(_SETTING_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Foxange] Failed to save settings: {e}")


load_highlight_colors()


class CompletionProvider:
    ALL_SOURCES = ["File Variables", "Keywords", "Builtins"]
    DEFAULT_SOURCES = ["File Variables", "Keywords", "Builtins"]

    def __init__(self):
        self.enabled = False
        self.sources = list(self.DEFAULT_SOURCES)
        self.load()

    def load(self):
        try:
            if not os.path.exists(_COMPLETION_FILE):
                return
            with open(_COMPLETION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.enabled = bool(data.get("enabled", False))
                src = data.get("sources")
                if isinstance(src, list):
                    valid = [s for s in src if s in self.ALL_SOURCES]
                    for s in self.ALL_SOURCES:
                        if s not in valid:
                            valid.append(s)
                    self.sources = valid
        except Exception as e:
            print(f"[Foxange] Failed to load completion settings: {e}")

    def save(self):
        try:
            os.makedirs(_SET_DIR, exist_ok=True)
            with open(_COMPLETION_FILE, "w", encoding="utf-8") as f:
                json.dump({"enabled": self.enabled, "sources": self.sources},
                          f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Foxange] Failed to save completion settings: {e}")

    def get_candidates(self, text, prefix):
        if not prefix:
            return []
        seen = set()
        result = []
        for source in self.sources:
            for word in self._get_source_words(source, text):
                if word.startswith(prefix) and word != prefix and word not in seen:
                    seen.add(word)
                    result.append(word)
        return result

    def _get_source_words(self, source, text):
        if source == "Keywords":
            return list(KEYWORDS) + self._error_type_names(text)
        if source == "Builtins":
            return list(BUILTINS)
        if source == "File Variables":
            return self._extract_vars(text)
        return []

    def _error_type_names(self, text):
        names = set((
            "Error", "Warning", "AllError",
            "NameError", "TypeError", "ValueError", "RuntimeError",
            "AttributeError", "ImportError", "KeyError", "IndexError",
            "ZeroDivisionError", "FileNotFoundError", "IOError", "OSError",
        ))
        for m in re.finditer(r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((Error|Warning)\)", text):
            names.add(m.group(1))
        return sorted(names)

    def _extract_vars(self, text):
        return list(set(_IDENT_RE.findall(text)))

    def _scan_types(self, text):
        fields = {}
        methods = {}
        var_types = {}
        current = None
        brace_depth = 0
        in_brace = False
        for raw in text.splitlines():
            cm = re.match(r"\s*(struct|class)\s+([A-Za-z_]\w*)", raw)
            if cm:
                current = cm.group(2)
                fields.setdefault(current, set())
                methods.setdefault(current, set())
                in_brace = "{" in raw
                brace_depth = raw.count("{") - raw.count("}")
                continue
            if current is None:
                continue
            if in_brace:
                brace_depth += raw.count("{") - raw.count("}")
                if brace_depth <= 0:
                    current = None
                    continue
                lm = re.search(r"\blet\s+([A-Za-z_]\w*)\s*=", raw)
                if lm:
                    fields[current].add(lm.group(1))
                sm = re.search(r"\bself\.([A-Za-z_]\w*)", raw)
                if sm:
                    fields[current].add(sm.group(1))
                dm = re.search(r"\bdef\s+([A-Za-z_]\w*)", raw)
                if dm and dm.group(1) != "__init__":
                    methods[current].add(dm.group(1))
                continue
            if raw.strip() and raw[0] not in (" ", "\t"):
                current = None
                continue
            lm = re.search(r"\blet\s+([A-Za-z_]\w*)\s*=", raw)
            if lm:
                fields[current].add(lm.group(1))
            sm = re.search(r"\bself\.([A-Za-z_]\w*)", raw)
            if sm:
                fields[current].add(sm.group(1))
            dm = re.search(r"\bdef\s+([A-Za-z_]\w*)", raw)
            if dm and dm.group(1) != "__init__":
                methods[current].add(dm.group(1))
        for m in re.finditer(r"\blet\s+([A-Za-z_]\w*)\s+(?:<[^>\n]*>\s*)?([A-Za-z_]\w*)\s*=", text):
            var_types[m.group(2)] = m.group(1)
        for m in re.finditer(r"\blet\s+([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*(?:<[^>\n]*>)?\s*\(", text):
            var_types[m.group(1)] = m.group(2)
        self._type_fields = fields
        self._type_methods = methods
        self._var_types = var_types


    def get_member_candidates(self, text, obj, op, prefix):
        self._scan_types(text)
        obj_type = self._var_types.get(obj)
        if op == "<-":
            if obj_type in self._type_fields:
                words = set(self._type_fields[obj_type])
            else:
                words = set()
                for s in self._type_fields.values():
                    words |= s
        else:
            if obj_type in self._type_methods:
                words = set(self._type_methods[obj_type])
            else:
                words = set()
                for s in self._type_methods.values():
                    words |= s
        seen = set()
        result = []
        for w in sorted(words):
            if w.startswith(prefix) and w != prefix and w not in seen:
                seen.add(w)
                result.append(w)
        return result



class FxRuntime:
    def __init__(self):
        self.interpreter = None
        self.preprocessor = None
        self._input_fn = None
        self._load()

    def _load(self):
        try:
            from foxange.interpreter import FoxangeInterpreter, _repl_preprocessor
            self.interpreter = FoxangeInterpreter()
            self.preprocessor = _repl_preprocessor
        except Exception as e:
            print(f"[Foxange] Failed to import interpreter: {e}")

    def install_input(self, input_fn):
        self._input_fn = input_fn
        try:
            import foxange.builtins as fxb
            fxb._input_func = input_fn
        except Exception as e:
            print(f"[Foxange] Failed to inject input function: {e}")
        import builtins
        builtins.input = input_fn

    def reset(self):
        self._load()
        if self._input_fn:
            self.install_input(self._input_fn)

    def is_ready(self):
        return self.interpreter is not None and self.preprocessor is not None

    def run(self, code, file_dir=None, file_path=None):
        if not self.is_ready():
            raise RuntimeError("Foxange interpreter is not loaded")

        from foxange.lexer import Lexer
        from foxange.parser import Parser
        from foxange.ast_nodes import ExpressionStmt, InputStmt

        processed = self.preprocessor.process(code)
        lexer = Lexer(processed)
        tokens = lexer.tokenize()
        tokens = self.preprocessor.apply_force_annotations(tokens)
        parser = Parser(tokens, source=processed)
        ast = parser.parse()

        old_dir = self.interpreter.current_file_dir
        old_path = self.interpreter.current_file_path
        if file_dir:
            self.interpreter.current_file_dir = file_dir
        self.interpreter.current_file_path = file_path or "<REPL>"
        try:
            result = self.interpreter.interpret(ast)
        finally:
            self.interpreter.current_file_dir = old_dir
            self.interpreter.current_file_path = old_path

        if ast.statements and isinstance(ast.statements[-1], (ExpressionStmt, InputStmt)):
            if result is not None:
                return result
        return None


KEYWORDS = {
    "if", "else", "elif", "while", "for", "in", "def", "return",
    "break", "continue", "import", "from", "as", "class", "try",
    "except", "finally", "with", "lambda", "pass", "raise", "global",
    "and", "or", "not", "True", "False", "None", "is", "del", "yield",
    "have", "let", "func", "inline", "struct", "mod", "xor", "pow", "operator",
}
BUILTINS = {"print", "input", "int", "float", "str", "bool",
            "char", "len", "open", "type", "run_to_python",
            "List", "Map", "Set", "Queue", "Stack", "Pair",
            "types", "errors"}

FONT_FAMILY = "Consolas"
FONT_SIZE = 11

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def apply_colors(widget):
    try:
        widget.tag_configure("KEYWORD", foreground=COLORS["keyword"])
        widget.tag_configure("BUILTIN", foreground=COLORS["builtin"])
        widget.tag_configure("STRING", foreground=COLORS["string"])
        widget.tag_configure("COMMENT", foreground=COLORS["comment"])
        widget.tag_configure("NUMBER", foreground=COLORS["number"])
        widget.tag_configure("DEFINITION", foreground=COLORS["definition"])
        widget.tag_configure("PROMPT", foreground=COLORS["shell_prompt"])
        widget.tag_configure("ERROR", foreground=COLORS["shell_error"])
        widget.tag_configure("INFO", foreground=COLORS["fg"])
        widget.tag_configure("RESTART", foreground=COLORS["shell_blue"])
        widget.tag_configure("INPUT", foreground=COLORS["input_prompt"])
        widget.tag_configure("ERR_SQUIGGLE",
                             foreground=COLORS["diag_error"])
        widget.tag_configure("WARN_SQUIGGLE",
                             foreground=COLORS["diag_warn"])
    except Exception:
        pass


def highlight(text_widget, start="1.0", end="end-1c"):
    for tag in ("KEYWORD", "BUILTIN", "STRING", "COMMENT", "NUMBER",
                "DEFINITION", "ERR_SQUIGGLE", "WARN_SQUIGGLE"):
        text_widget.tag_remove(tag, start, end)

    src = text_widget.get(start, end)
    if not src:
        return

    cnt = text_widget.count("1.0", start, "chars")
    base_offset = cnt[0] if isinstance(cnt, tuple) and cnt else (cnt or 0)

    def idx(pos):
        return f"1.0 + {base_offset + pos}c"

    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == "#":
            j = src.find("\n", i)
            if j == -1:
                j = n
            text_widget.tag_add("COMMENT", idx(i), idx(j))
            i = j
            continue
        if c == '"' or c == "'":
            q = c
            j = i + 1
            while j < n and src[j] != q:
                if src[j] == "\\" and j + 1 < n:
                    j += 2
                else:
                    j += 1
            if j < n:
                j += 1
            text_widget.tag_add("STRING", idx(i), idx(j))
            i = j
            continue
        m = _IDENT_RE.match(src, i)
        if m:
            word = m.group(0)
            if word in KEYWORDS:
                text_widget.tag_add("KEYWORD", idx(i), idx(m.end()))
                if word in ("def", "class"):
                    k = m.end()
                    while k < n and src[k] in " \t":
                        k += 1
                    m2 = _IDENT_RE.match(src, k)
                    if m2:
                        text_widget.tag_add("DEFINITION", idx(k), idx(m2.end()))
            elif word in BUILTINS:
                text_widget.tag_add("BUILTIN", idx(i), idx(m.end()))
            elif word == "self":
                text_widget.tag_add("DEFINITION", idx(i), idx(m.end()))
            i = m.end()
            continue
        m = _NUMBER_RE.match(src, i)
        if m:
            text_widget.tag_add("NUMBER", idx(i), idx(m.end()))
            i = m.end()
            continue
        i += 1


class DiagnosticEngine:
    """轻量静态诊断：返回 [(severity, message, line, col, end_col)]"""

    _OPEN_BRACKETS = {"(": ")", "[": "]", "{": "}"}

    @classmethod
    def check(cls, source):
        lines = source.split("\n")
        diags = []
        cls._quick_checks(source, lines, diags)
        cls._parser_check(source, lines, diags)
        return diags

    @classmethod
    def _quick_checks(cls, source, lines, diags):
        in_str = None
        str_start = (0, 0)
        stack = []
        for ln, line in enumerate(lines, start=1):
            stripped = line.rstrip("\r").rstrip()
            if stripped != line.rstrip("\r"):
                diags.append(("warning", "Trailing whitespace", ln,
                              len(stripped), len(line.rstrip("\r"))))
            indent = re.match(r"[ \t]*", line).group(0)
            if " " in indent and "\t" in indent:
                diags.append(("warning", "Mixed tabs and spaces in indent",
                              ln, 0, len(indent)))
            i = 0
            n = len(line)
            while i < n:
                ch = line[i]
                if in_str is not None:
                    if ch == "\\":
                        i += 2
                        continue
                    if ch == in_str:
                        in_str = None
                    i += 1
                    continue
                if ch == "#":
                    break
                if ch in ('"', "'"):
                    in_str = ch
                    str_start = (ln, i)
                    i += 1
                    continue
                if ch in cls._OPEN_BRACKETS:
                    stack.append((ch, ln, i))
                elif ch in ")]}":
                    if stack and cls._OPEN_BRACKETS[stack[-1][0]] == ch:
                        stack.pop()
                    else:
                        diags.append(("error",
                                      f"Unexpected '{ch}'", ln, i, i + 1))
                i += 1
        if in_str is not None:
            sline = lines[str_start[0] - 1]
            diags.append(("error", "Unterminated string literal",
                          str_start[0], str_start[1], len(sline)))
        for ch, ln, col in stack:
            diags.append(("error", f"Unclosed '{ch}'", ln, col, col + 1))

    @classmethod
    def _parser_check(cls, source, lines, diags):
        try:
            from foxange.lexer import Lexer
            from foxange.parser import Parser
            from foxange.error_utils import FoxangeError
            tokens = Lexer(source).tokenize()
            Parser(tokens, source).parse()
        except FoxangeError as e:
            cls._add_parser_error(diags, lines,
                                  e.exc_type or "SyntaxError",
                                  str(e.args[0] if e.args else ""),
                                  e.line, e.col)
        except SyntaxError as e:
            m = re.search(r"at line (\d+), col (\d+): (.*)", str(e))
            if m:
                msg = m.group(3)
                if "Unterminated string" in msg and any(
                        d[0] == "error"
                        and d[1] == "Unterminated string literal"
                        for d in diags):
                    return
                cls._add_parser_error(diags, lines, "SyntaxError",
                                      msg,
                                      int(m.group(1)), int(m.group(2)))
        except Exception:
            pass

    @staticmethod
    def _add_parser_error(diags, lines, exc_type, msg, line, col):
        diags[:] = [d for d in diags
                    if not (d[0] == "error"
                            and (d[1].startswith("Unclosed")
                                 or d[1].startswith("Unterminated string")
                                 or d[1].startswith("Unexpected '")))]
        if line < 1 or line > len(lines):
            line = max(1, min(len(lines), line)) if lines else 1
        if line <= len(lines):
            end_col = len(lines[line - 1].rstrip("\r"))
        else:
            end_col = col + 1
        if end_col <= col:
            end_col = col + 1
        diags.append(("error", f"{exc_type}: {msg}", line, col, end_col))


class LineNumberCanvas(tk.Canvas):
    def __init__(self, master, text_widget=None, **kw):
        kw.setdefault("width", 44)
        super().__init__(master, **kw)
        self.text = text_widget
        self.configure(background=COLORS["linenum_bg"],
                       borderwidth=0, highlightthickness=0)
        self._job = None
        self._font = (FONT_FAMILY, FONT_SIZE)

        if self.text is not None:
            self.text.bind("<<Change>>", self._schedule, add="+")
            self.text.bind("<Configure>", self._schedule, add="+")
            self.text.bind("<KeyRelease>", self._schedule, add="+")
            self.text.bind("<MouseWheel>", self._schedule, add="+")
            self.text.bind("<Button-1>", self._schedule, add="+")
            self.text.bind("<ButtonRelease>", self._schedule, add="+")
            self.text.bind("<Motion>", self._schedule, add="+")

    def attach(self, text_widget):
        self.text = text_widget
        self.text.bind("<<Change>>", self._schedule, add="+")
        self.text.bind("<<Modified>>", self._schedule, add="+")
        self.text.bind("<Configure>", self._schedule, add="+")
        self.text.bind("<KeyRelease>", self._schedule, add="+")
        self.text.bind("<MouseWheel>", self._schedule, add="+")
        self.text.bind("<Button-1>", self._schedule, add="+")
        self.text.bind("<ButtonRelease>", self._schedule, add="+")
        self.text.bind("<Motion>", self._schedule, add="+")
        self.text.bind("<Control-MouseWheel>", self._schedule, add="+")
        self._schedule()

    def _schedule(self, event=None):
        if self.text is None:
            return
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        self._job = self.after(30, self._redraw)

    def _redraw(self):
        self._job = None
        if self.text is None or not self.winfo_exists():
            return
        try:
            self.delete("all")
            self._update_width()
            i = self.text.index("@0,0")
            while True:
                dline = self.text.dlineinfo(i)
                if dline is None:
                    break
                y = dline[1]
                ln = str(i).split(".")[0]
                self.create_text(self.winfo_width() - 4, y, anchor="ne",
                                 text=ln, font=self._font,
                                 fill=COLORS["linenum_fg"])
                next_i = self.text.index(f"{i}+1line")
                if next_i == i:
                    break
                i = next_i
        except tk.TclError:
            pass

    def _update_width(self):
        if self.text is None:
            return
        try:
            total = int(self.text.index("end-1c").split(".")[0])
        except Exception:
            total = 1
        digits = max(2, len(str(total)))
        w = digits * 9 + 12
        self.configure(width=w)

    def set_font(self, font):
        self._font = font
        if self.text is not None:
            self._redraw()

    def apply_colors(self):
        self.configure(background=COLORS["linenum_bg"])
        if self.text is not None:
            self._redraw()

class CompletionPopup(tk.Toplevel):
    def __init__(self, editor, candidates, x, y):
        super().__init__(editor)
        self.editor = editor
        self.candidates = candidates
        self.overrideredirect(True)
        try:
            self.attributes("-topmost", True)
        except Exception:
            pass

        frame = tk.Frame(self, borderwidth=1, relief="solid")
        frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            frame,
            height=min(len(candidates), 8),
            activestyle="none",
            selectbackground="#0078d7",
            selectforeground="#ffffff",
            font=(FONT_FAMILY, FONT_SIZE),
            borderwidth=0,
            highlightthickness=0,
            exportselection=False,
        )
        for c in candidates:
            self.listbox.insert("end", c)
        self.listbox.pack(fill="both", expand=True)
        if candidates:
            self.listbox.selection_set(0)
            self.listbox.activate(0)

        longest = max((len(c) for c in candidates), default=8)
        w = min(320, longest * 9 + 24)
        h = min(len(candidates), 8) * 20 + 4
        self.geometry(f"{w}x{h}+{int(x)}+{int(y)}")

    def get_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return self.candidates[sel[0]]

    def move_selection(self, delta):
        sel = self.listbox.curselection()
        idx = sel[0] if sel else 0
        new_idx = max(0, min(len(self.candidates) - 1, idx + delta))
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(new_idx)
        self.listbox.activate(new_idx)
        self.listbox.see(new_idx)

    def apply(self, prefix):
        sel = self.get_selected()
        if sel is None:
            return False
        n = len(prefix)
        pos = self.editor.index("insert")
        start = f"{pos} - {n}c"
        self.editor.delete(start, pos)
        self.editor.insert(start, sel)
        return True

    def close(self):
        try:
            self.destroy()
        except Exception:
            pass


class FoxText(tk.Text):
    def __init__(self, master, **kw):
        kw.setdefault("undo", True)
        kw.setdefault("wrap", "none")
        kw.setdefault("tabs", ("4c",))
        super().__init__(master, **kw)
        self.configure(
            background=COLORS["bg"], foreground=COLORS["fg"],
            insertbackground=COLORS["fg"],
            selectbackground=COLORS["sel_bg"],
            font=(FONT_FAMILY, FONT_SIZE),
            borderwidth=0, highlightthickness=0,
        )
        apply_colors(self)

        self._hl_job = None
        self._diag_enabled = False
        self._last_diags = []
        self._diag_bands = []
        self._sq_job = None
        self._completion_provider = None
        self._completion_popup = None
        self._completion_prefix = ""
        self._completion_job = None

        self.bind("<<Modified>>", self._on_modified)
        self.bind("<Return>", self._on_return)
        self.bind("<Tab>", self._on_tab)
        self.bind("<Shift-Tab>", self._on_shift_tab)
        self.bind("<Control-MouseWheel>", self._on_wheel)
        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<Escape>", self._on_escape)
        self.bind("<Up>", self._on_up)
        self.bind("<Down>", self._on_down)
        self.bind("<FocusOut>", lambda e: self._close_completion())
        self.bind("<Button-1>", lambda e: self._close_completion())
        self.bind("<Configure>", self._schedule_squiggle, add="+")
        self.bind("<MouseWheel>", self._schedule_squiggle, add="+")
        self.bind("<KeyRelease>", self._schedule_squiggle, add="+")

    def _on_modified(self, event=None):
        if self.edit_modified():
            self.edit_modified(False)
            if self._hl_job:
                self.after_cancel(self._hl_job)
            self._hl_job = self.after(150, self._apply_highlight)

    def _apply_highlight(self):
        self._hl_job = None
        highlight(self)
        if self._diag_enabled:
            self._apply_diagnostics()

    def force_highlight(self):
        highlight(self)
        if self._diag_enabled:
            self._apply_diagnostics()

    def set_diagnostics_enabled(self, enabled):
        self._diag_enabled = bool(enabled)
        if self._diag_enabled:
            self._apply_diagnostics()
        else:
            self._clear_squiggles()

    def _apply_diagnostics(self):
        try:
            src = self.get("1.0", "end-1c")
            diags = DiagnosticEngine.check(src)
        except Exception:
            return
        items = []
        for sev, msg, line, col, end_col in diags:
            if end_col <= col:
                end_col = col + 1
            items.append((sev, line, col, end_col))
        self._last_diags = items
        self._redraw_squiggles()

    def _schedule_squiggle(self, event=None):
        if not self._diag_enabled:
            return
        if self._sq_job:
            try:
                self.after_cancel(self._sq_job)
            except Exception:
                pass
        self._sq_job = self.after(40, self._redraw_squiggles)

    def _clear_squiggles(self):
        for band in self._diag_bands:
            try:
                band.destroy()
            except Exception:
                pass
        self._diag_bands = []

    def _redraw_squiggles(self):
        self._sq_job = None
        self._clear_squiggles()
        if not self._diag_enabled:
            return
        try:
            for sev, line, col, end_col in self._last_diags:
                b1 = self.bbox(f"{line}.{col}")
                b2 = self.bbox(f"{line}.{end_col - 1}")
                if not b1 or not b2:
                    continue
                x = b1[0]
                w = (b2[0] + b2[2]) - x
                y = b1[1]
                h = b1[3]
                if w <= 0:
                    continue
                color = (COLORS["diag_error"] if sev == "error"
                         else COLORS["diag_warn"])
                band = tk.Canvas(self, height=5, width=w + 2,
                                 background=COLORS["bg"],
                                 highlightthickness=0, borderwidth=0,
                                 cursor="xterm", takefocus=0)
                pts = []
                for px in range(0, w + 2):
                    py = 2 + math.sin(px * math.pi * 2 / 4.0) * 1.2
                    pts.extend((px, py))
                band.create_line(*pts, fill=color, width=1)
                band.place(x=x, y=y + h - 2, width=w + 2, height=5)
                self._bind_band_events(band)
                self._diag_bands.append(band)
        except tk.TclError:
            pass

    def _bind_band_events(self, band):
        def forward(seq):
            def handler(event):
                try:
                    rx = band.winfo_rootx() - self.winfo_rootx()
                    ry = band.winfo_rooty() - self.winfo_rooty()
                    self.event_generate(seq, x=event.x + rx,
                                        y=event.y + ry,
                                        delta=getattr(event, "delta", 0))
                    if seq == "<Button-1>":
                        self.focus_set()
                except Exception:
                    pass
            return handler
        for seq in ("<Button-1>", "<B1-Motion>", "<ButtonRelease-1>",
                    "<Double-Button-1>", "<Triple-Button-1>",
                    "<MouseWheel>", "<Control-MouseWheel>"):
            band.bind(seq, forward(seq))

    def yview(self, *args):
        result = super().yview(*args)
        self._schedule_squiggle()
        return result

    def xview(self, *args):
        result = super().xview(*args)
        self._schedule_squiggle()
        return result

    def _on_return(self, event):
        if self._completion_popup is not None:
            if self._completion_popup.apply(self._completion_prefix):
                self._close_completion()
                return "break"
        line_idx = self.index("insert").split(".")[0]
        line = self.get(f"{line_idx}.0", f"{line_idx}.end")
        indent = re.match(r"[ \t]*", line).group(0)
        extra = line.rstrip().endswith(":") or line.rstrip().endswith("{")
        self.insert("insert", "\n" + indent + ("    " if extra else ""))
        self.see("insert")
        return "break"

    def _on_tab(self, event):
        if self._completion_popup is not None:
            if self._completion_popup.apply(self._completion_prefix):
                self._close_completion()
                return "break"
        try:
            first = self.index("sel.first")
            last = self.index("sel.last")
        except tk.TclError:
            self.insert("insert", "    ")
            return "break"
        self._indent_range(first, last, +1)
        return "break"

    def _on_shift_tab(self, event):
        try:
            first = self.index("sel.first")
            last = self.index("sel.last")
        except tk.TclError:
            return "break"
        self._indent_range(first, last, -1)
        return "break"

    def _indent_range(self, first, last, direction):
        l1 = int(first.split(".")[0])
        l2 = int(last.split(".")[0])
        for ln in range(l1, l2 + 1):
            if direction > 0:
                self.insert(f"{ln}.0", "    ")
            else:
                line = self.get(f"{ln}.0", f"{ln}.end")
                if line.startswith("    "):
                    self.delete(f"{ln}.0", f"{ln}.4")
                elif line.startswith("\t"):
                    self.delete(f"{ln}.0", f"{ln}.1")

    def toggle_comment(self, comment=True):
        try:
            first = self.index("sel.first")
            last = self.index("sel.last")
        except tk.TclError:
            first = last = self.index("insert")
        l1 = int(first.split(".")[0])
        l2 = int(last.split(".")[0])
        for ln in range(l1, l2 + 1):
            line = self.get(f"{ln}.0", f"{ln}.end")
            if comment and not line.lstrip().startswith("#"):
                self.insert(f"{ln}.0", "# ")
            elif not comment and line.lstrip().startswith("#"):
                stripped = line.lstrip()
                n = 2 if stripped.startswith("# ") else 1
                col = len(line) - len(stripped)
                self.delete(f"{ln}.{col}", f"{ln}.{col + n}")

    def _zoom(self, delta):
        global FONT_SIZE
        FONT_SIZE = max(8, min(36, FONT_SIZE + delta))
        self.configure(font=(FONT_FAMILY, FONT_SIZE))
        self.force_highlight()

    def _on_wheel(self, event):
        self._zoom(+1 if event.delta > 0 else -1)
        return "break"

    def _on_key_release(self, event):
        if event.keysym in ("Up", "Down", "Return", "Tab", "Escape",
                            "Shift_L", "Shift_R", "Control_L", "Control_R",
                            "Alt_L", "Alt_R", "Left", "Right", "Home", "End"):
            return
        if event.char and (event.char.isalnum() or event.char == "_"):
            if self._completion_job:
                self.after_cancel(self._completion_job)
            self._completion_job = self.after(80, self._try_show_completion)
        else:
            self._close_completion()

    def _on_escape(self, event):
        self._close_completion()
        return "break"

    def _on_up(self, event):
        if self._completion_popup is not None:
            self._completion_popup.move_selection(-1)
            return "break"

    def _on_down(self, event):
        if self._completion_popup is not None:
            self._completion_popup.move_selection(1)
            return "break"

    def _try_show_completion(self):
        self._completion_job = None
        if self._completion_provider is None:
            return
        if not self._completion_provider.enabled:
            return

        pos = self.index("insert")
        line_start = self.index(f"{pos} linestart")
        line_text = self.get(line_start, pos)
        text = self.get("1.0", "end-1c")

        mm = re.match(r"([A-Za-z_]\w*)\s*(<-|->|\.)\s*([A-Za-z_]\w*)$", line_text)
        if mm:
            obj, op, prefix = mm.group(1), mm.group(2), mm.group(3)
            candidates = self._completion_provider.get_member_candidates(text, obj, op, prefix)
            if not candidates:
                self._close_completion()
                return
            self._close_completion()
            bbox = self.bbox("insert")
            if bbox is None:
                return
            x = self.winfo_rootx() + bbox[0]
            y = self.winfo_rooty() + bbox[1] + bbox[3]
            try:
                self._completion_popup = CompletionPopup(self, candidates, x, y)
                self._completion_prefix = prefix
            except Exception:
                self._completion_popup = None
            return

        m = re.search(r"[A-Za-z_][A-Za-z0-9_]*$", line_text)
        if not m:
            self._close_completion()
            return
        prefix = m.group(0)
        if len(prefix) < 1:
            return

        candidates = self._completion_provider.get_candidates(text, prefix)
        if not candidates:
            self._close_completion()
            return

        self._close_completion()

        bbox = self.bbox("insert")
        if bbox is None:
            return
        x = self.winfo_rootx() + bbox[0]
        y = self.winfo_rooty() + bbox[1] + bbox[3]

        try:
            self._completion_popup = CompletionPopup(self, candidates, x, y)
            self._completion_prefix = prefix
        except Exception:
            self._completion_popup = None

    def _close_completion(self):
        if self._completion_job:
            try:
                self.after_cancel(self._completion_job)
            except Exception:
                pass
            self._completion_job = None
        if self._completion_popup is not None:
            self._completion_popup.close()
            self._completion_popup = None
        self._completion_prefix = ""

    def apply_completion_settings(self, provider):
        self._completion_provider = provider
        if not provider.enabled:
            self._close_completion()


class FoxShell(tk.Text):
    def __init__(self, master, runtime, **kw):
        kw.setdefault("wrap", "none")
        super().__init__(master, **kw)
        self.configure(
            background=COLORS["bg"], foreground=COLORS["fg"],
            insertbackground=COLORS["fg"],
            selectbackground=COLORS["sel_bg"],
            font=(FONT_FAMILY, FONT_SIZE),
            borderwidth=0, highlightthickness=0,
            state="normal",
        )
        apply_colors(self)

        self.runtime = runtime

        self.history = []
        self.hist_pointer = -1
        self.hist_prefix = ""

        self._pending = ""

        self.mark_set("iomark", "end-1c")
        self.mark_gravity("iomark", "left")
        self.iomark_locked = True

        self._input_var = None
        self._hl_job = None
        self._completion_provider = None
        self._completion_popup = None
        self._completion_prefix = ""
        self._completion_job = None

        self.bind("<Return>", self._on_return)
        self.bind("<Key>", self._on_key)
        self.bind("<Button-1>", self._on_click)
        self.bind("<<Modified>>", self._on_modified)
        self.bind("<Alt-p>", lambda e: self._history_fetch(True))
        self.bind("<Alt-n>", lambda e: self._history_fetch(False))
        self.bind("<Up>", self._on_up)
        self.bind("<Down>", self._on_down)
        self.bind("<Tab>", self._on_tab)
        self.bind("<Escape>", self._on_escape)
        self.bind("<KeyRelease>", self._on_key_release)

    def _on_tab(self, event):
        if self._completion_popup is not None:
            if self._completion_popup.apply(self._completion_prefix):
                self._close_completion()
                return "break"
        return None

    def _append(self, text, tag="INFO"):
        self.insert("end", text, tag)
        self.see("end")

    def banner(self):
        self._append("Foxange 1.0", "INFO")
        self._append(" - IDLE Shell\n", "INFO")
        self._append('Type "help" for more information.\n\n', "INFO")

    def set_prompt(self, cont=False):
        self.insert("end", "... " if cont else ">>> ", "PROMPT")
        self.mark_set("iomark", "end-1c")
        self.iomark_locked = False
        self.mark_set("insert", "end-1c")

    def _on_modified(self, event=None):
        if not self.edit_modified():
            return
        self.edit_modified(False)
        if self.iomark_locked or self._input_var is not None:
            return
        if self._hl_job:
            self.after_cancel(self._hl_job)
        self._hl_job = self.after(100, self._apply_highlight)

    def _apply_highlight(self):
        self._hl_job = None
        if self.iomark_locked or self._input_var is not None:
            return
        try:
            if self.compare("iomark", "<", "end-1c"):
                highlight(self, "iomark", "end-1c")
        except tk.TclError:
            pass

    def force_highlight(self):
        self._apply_highlight()

    def ask_input(self, prompt=""):
        var = tk.StringVar()
        self._input_var = var

        if prompt:
            self.insert("end", str(prompt), "INPUT")
        self.see("end")
        self.mark_set("iomark", "end-1c")
        self.iomark_locked = False
        self.mark_set("insert", "end-1c")
        self.focus_set()

        try:
            self.wait_variable(var)
        except tk.TclError:
            self._input_var = None
            return ""
        self._input_var = None
        return var.get()

    def _on_key(self, event):
        if self.iomark_locked:
            return "break"
        if self.compare("insert", "<", "iomark"):
            if event.keysym in ("BackSpace", "Delete"):
                return "break"
            if event.char and event.char.isprintable():
                self.mark_set("insert", "end-1c")
        return None

    def _on_click(self, event):
        self.after_idle(self._fix_insert)

    def _fix_insert(self):
        if self.iomark_locked:
            return
        if self.compare("insert", "<", "iomark"):
            self.mark_set("insert", "end-1c")

    def _on_return(self, event):
        if self._completion_popup is not None:
            if self._completion_popup.apply(self._completion_prefix):
                self._close_completion()
                return "break"

        if self._input_var is not None:
            value = self.get("iomark", "end-1c")
            self.insert("end", "\n")
            self.see("end")
            var = self._input_var
            self._input_var = None
            var.set(value)
            return "break"

        if self.iomark_locked:
            return "break"

        src = self.get("iomark", "end-1c")
        self.insert("end", "\n")
        self._pending += src + "\n"

        if not _needs_continuation(self._pending.rstrip("\n")):
            code = self._pending.strip("\n")
            self._pending = ""
            if code:
                self.history.append(code)
                self.hist_pointer = -1
                self.hist_prefix = ""
                if code.strip() in ("help", "help()"):
                    self._append(
                        "Foxange IDLE help\n"
                        "- this Foxange language is my first language!awa\n"
                        "- made by SLC_Extreme\n"
                        "- bugs and your idea : https://bugs-foxange.fwh.is\n"
                        "Made People:\n"
                        "- SLC_Extreme : The main developer of a programming language\n"
                        ""
                    )
                else:
                    self.current_file = None
                    self._execute(code)
            self.set_prompt(cont=False)
        else:
            self.set_prompt(cont=True)
        return "break"

    def _execute(self, code):
        buf = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = buf
        sys.stderr = buf
        try:
            result = self.runtime.run(code, file_path=self.current_file)
            if result is not None:
                print(repr(result))
        except SyntaxError as e:
            buf.write(f"SyntaxError: {e}\n")
        except Exception as e:
            try:
                from foxange.error_utils import FoxangeError, format_error
                if isinstance(e, FoxangeError):
                    buf.write(format_error(e, source_lines=code.split("\n")) + "\n")
                else:
                    buf.write(f"Traceback (most recent call last):\n  "
                              f"{type(e).__name__}: {e}\n")
            except Exception:
                buf.write(f"Traceback (most recent call last):\n  "
                          f"{type(e).__name__}: {e}\n")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        out = buf.getvalue()
        if out:
            err_markers = ("<file : ", "Traceback (most recent call last)", "SyntaxError:")
            split_idx = None
            for marker in err_markers:
                idx = out.find(marker)
                if idx != -1:
                    split_idx = idx if split_idx is None else min(split_idx, idx)
            if split_idx is None:
                self._append(out, "INFO")
                if not out.endswith("\n"):
                    self._append("\n", "INFO")
            else:
                head = out[:split_idx]
                tail = out[split_idx:]
                if head:
                    self._append(head, "INFO")
                    if not head.endswith("\n"):
                        self._append("\n", "INFO")
                self._append(tail, "ERROR")
                if not tail.endswith("\n"):
                    self._append("\n", "ERROR")

    def _history_fetch(self, reverse):
        if self._input_var is not None:
            return "break"
        if not self.history:
            return "break"
        if self.hist_pointer == -1:
            self.hist_prefix = self.get("iomark", "end-1c")
        n = len(self.history)
        ptr = self.hist_pointer if self.hist_pointer != -1 else n
        while True:
            ptr += -1 if reverse else 1
            if ptr < 0 or ptr >= n:
                self.bell()
                return "break"
            if self.history[ptr].startswith(self.hist_prefix):
                break
        self.delete("iomark", "end-1c")
        self.insert("iomark", self.history[ptr])
        self.hist_pointer = ptr
        return "break"

    def _on_key_release(self, event):
        if event.keysym in ("Up", "Down", "Return", "Tab", "Escape",
                            "Shift_L", "Shift_R", "Control_L", "Control_R",
                            "Alt_L", "Alt_R", "Left", "Right", "Home", "End"):
            return
        if self._input_var is not None:
            return
        if self.iomark_locked:
            return
        if event.char and (event.char.isalnum() or event.char == "_"):
            if self._completion_job:
                self.after_cancel(self._completion_job)
            self._completion_job = self.after(80, self._try_show_completion)
        else:
            self._close_completion()

    def _on_escape(self, event):
        self._close_completion()
        return "break"

    def _on_up(self, event):
        if self._completion_popup is not None:
            self._completion_popup.move_selection(-1)
            return "break"
        return self._history_fetch(True)

    def _on_down(self, event):
        if self._completion_popup is not None:
            self._completion_popup.move_selection(1)
            return "break"
        return self._history_fetch(False)

    def _try_show_completion(self):
        self._completion_job = None
        if self._completion_provider is None:
            return
        if not self._completion_provider.enabled:
            return
        if self.iomark_locked or self._input_var is not None:
            return

        pos = self.index("insert")
        line_start = self.index(f"{pos} linestart")
        if self.compare(line_start, "<", "iomark"):
            line_start = "iomark"
        line_text = self.get(line_start, pos)
        m = re.search(r"[A-Za-z_][A-Za-z0-9_]*$", line_text)
        if not m:
            self._close_completion()
            return
        prefix = m.group(0)
        if not prefix:
            return

        text = self.get("1.0", "end-1c")
        candidates = self._completion_provider.get_candidates(text, prefix)
        if not candidates:
            self._close_completion()
            return

        self._close_completion()

        bbox = self.bbox("insert")
        if bbox is None:
            return
        x = self.winfo_rootx() + bbox[0]
        y = self.winfo_rooty() + bbox[1] + bbox[3]

        try:
            self._completion_popup = CompletionPopup(self, candidates, x, y)
            self._completion_prefix = prefix
        except Exception:
            self._completion_popup = None

    def _close_completion(self):
        if self._completion_job:
            try:
                self.after_cancel(self._completion_job)
            except Exception:
                pass
            self._completion_job = None
        if self._completion_popup is not None:
            self._completion_popup.close()
            self._completion_popup = None
        self._completion_prefix = ""

    def apply_completion_settings(self, provider):
        self._completion_provider = provider
        if not provider.enabled:
            self._close_completion()


_BLOCK_KW = {"if", "elif", "else", "for", "while", "with",
             "def", "class", "try", "have", "except", "finally"}


def _needs_continuation(code):
    if not code.rstrip():
        return False
    stack = []
    in_s = in_d = in_t3s = in_t3d = False
    escape = False
    i, n = 0, len(code)
    while i < n:
        ch = code[i]
        if escape:
            escape = False
            i += 1
            continue
        if not in_s and not in_d:
            if code[i:i + 3] == '"""' and not in_t3s:
                in_t3d = not in_t3d
                i += 3
                continue
            if code[i:i + 3] == "'''" and not in_t3d:
                in_t3s = not in_t3s
                i += 3
                continue
        if in_t3s or in_t3d:
            if ch == "\\":
                escape = True
            i += 1
            continue
        if ch == "\\":
            escape = True
            i += 1
            continue
        if ch == '"' and not in_s:
            in_d = not in_d
        elif ch == "'" and not in_d:
            in_s = not in_s
        elif not in_s and not in_d:
            if ch in "([{":
                stack.append(ch)
            elif ch in ")]}":
                if not stack:
                    return True
                if (ch == ")" and stack[-1] == "(") or \
                   (ch == "]" and stack[-1] == "[") or \
                   (ch == "}" and stack[-1] == "{"):
                    stack.pop()
                else:
                    return True
        i += 1
    if in_s or in_d or in_t3s or in_t3d:
        return True
    if stack:
        return True
    last = code.rstrip().split("\n")[-1].strip()
    if not last:
        return False
    if last.endswith("\\"):
        return True
    if last.endswith(":"):
        head = last.split()[0].rstrip(":")
        if head in _BLOCK_KW:
            return True
    return False


class HighlightDialog(tk.Toplevel):
    TAG_INFO = [
        ("KEYWORD", "Keyword", "if  def  return"),
        ("BUILTIN", "Builtin", "print  input  len"),
        ("STRING", "String", '"hello"'),
        ("COMMENT", "Comment", "# this is a comment"),
        ("NUMBER", "Number", "123  4.56"),
        ("DEFINITION", "Definition", "my_func  self"),
    ]

    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.title("Highlight Colors")
        self.geometry(DIALOG_SIZE)
        self.minsize(480, 400)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._build()

    def _build(self):
        for child in self.winfo_children():
            child.destroy()

        bottom = ttk.Frame(self, padding=(14, 8, 14, 12))
        bottom.pack(side="bottom", fill="x")

        ttk.Button(bottom, text="Restore Defaults", width=18,
                   command=self._reset).pack(side="left")
        ttk.Button(bottom, text="Close", width=12,
                   command=self.destroy).pack(side="right")

        ttk.Label(self, text=f"Config saved to: {_HIGHLIGHT_FILE}",
                  font=("Segoe UI", 8), foreground="#888").pack(
            side="bottom", anchor="w", padx=14, pady=(0, 4))

        body = ttk.Frame(self, padding=(14, 14, 14, 8))
        body.pack(side="top", fill="both", expand=True)

        ttk.Label(body, text="Click a swatch to pick a color. Live preview.",
                  font=("Segoe UI", 9), foreground="#666").pack(
            anchor="w", pady=(0, 10))

        for tag, label, sample in self.TAG_INFO:
            row = ttk.Frame(body)
            row.pack(fill="x", pady=4)

            ttk.Label(row, text=label, width=10, anchor="w",
                      font=("Segoe UI", 9)).pack(side="left")

            key = tag.lower()
            color = COLORS.get(key, "#000000")

            swatch = tk.Button(row, width=4, height=1, bg=color,
                               relief="raised", bd=2, cursor="hand2",
                               activebackground=color,
                               command=lambda t=tag: self._pick(t))
            swatch.pack(side="left", padx=(6, 12))

            tk.Label(row, text=sample, fg=color, bg=COLORS["bg"],
                     font=(FONT_FAMILY, FONT_SIZE)).pack(side="left")

    def _pick(self, tag):
        key = tag.lower()
        current = COLORS.get(key, "#000000")
        rgb, hex_color = colorchooser.askcolor(color=current,
                                               parent=self,
                                               title=f"Pick color for {tag}")
        if not hex_color:
            return
        COLORS[key] = hex_color
        save_highlight_colors()

        for w in (self.app.editor.text if self.app.editor else None,
                  self.app.shell_text):
            if w is None:
                continue
            try:
                w.tag_configure(tag, foreground=hex_color)
            except Exception:
                pass

        if self.app.editor is not None and self.app.editor.linenum is not None:
            self.app.editor.linenum.apply_colors()

        self._build()

    def _reset(self):
        reset_highlight_colors()
        targets = [self.app.editor.text if self.app.editor else None,
                   self.app.shell_text]
        for w in targets:
            if w is None:
                continue
            apply_colors(w)
            try:
                highlight(w)
            except Exception:
                pass
        if self.app.editor is not None and self.app.editor.linenum is not None:
            self.app.editor.linenum.apply_colors()
        self._build()


class CompletionSettingsDialog(tk.Toplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.provider = app.completion_provider
        self.title("Completion Settings")
        self.geometry(COMPLETION_DIALOG_SIZE)
        self.minsize(360, 340)
        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.enabled_var = tk.BooleanVar(value=self.provider.enabled)
        self._build()

    def _build(self):
        for child in self.winfo_children():
            child.destroy()

        bottom = ttk.Frame(self, padding=(14, 8, 14, 12))
        bottom.pack(side="bottom", fill="x")

        ttk.Button(bottom, text="Restore Defaults", width=18,
                   command=self._reset).pack(side="left")
        ttk.Button(bottom, text="Apply", width=10,
                   command=self._apply).pack(side="right", padx=(4, 0))
        ttk.Button(bottom, text="Close", width=10,
                   command=self.destroy).pack(side="right")

        ttk.Label(self, text=f"Config saved to: {_COMPLETION_FILE}",
                  font=("Segoe UI", 8), foreground="#888").pack(
            side="bottom", anchor="w", padx=14, pady=(0, 4))

        body = ttk.Frame(self, padding=(14, 14, 14, 8))
        body.pack(side="top", fill="both", expand=True)

        ttk.Checkbutton(body, text="Enable code completion",
                        variable=self.enabled_var).pack(anchor="w", pady=(0, 10))

        ttk.Label(body, text="Candidate sources (top to bottom = priority):",
                  font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 6))

        list_frame = ttk.Frame(body)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(list_frame, height=6,
                                  activestyle="none",
                                  font=(FONT_FAMILY, FONT_SIZE),
                                  exportselection=False)
        for s in self.provider.sources:
            self.listbox.insert("end", s)
        if self.provider.sources:
            self.listbox.selection_set(0)
        self.listbox.pack(side="left", fill="both", expand=True)

        btns = ttk.Frame(list_frame)
        btns.pack(side="left", fill="y", padx=(8, 0))

        ttk.Button(btns, text="Move Up", width=10,
                   command=lambda: self._move(-1)).pack(pady=2)
        ttk.Button(btns, text="Move Down", width=10,
                   command=lambda: self._move(1)).pack(pady=2)

    def _move(self, delta):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= self.listbox.size():
            return
        val = self.listbox.get(idx)
        self.listbox.delete(idx)
        self.listbox.insert(new_idx, val)
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(new_idx)
        self.listbox.activate(new_idx)

    def _reset(self):
        self.enabled_var.set(False)
        self.listbox.delete(0, "end")
        for s in CompletionProvider.DEFAULT_SOURCES:
            self.listbox.insert("end", s)
        if self.listbox.size():
            self.listbox.selection_set(0)

    def _apply(self):
        self.provider.enabled = bool(self.enabled_var.get())
        new_sources = list(self.listbox.get(0, "end"))
        if new_sources:
            self.provider.sources = new_sources
        self.provider.save()
        self.app.refresh_completion_menu()
        self.app.apply_completion_settings()


class EditorWindow(tk.Toplevel):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.title("untitled - Foxange IDLE")
        self.geometry(MAIN_SIZE)
        self.filename = None
        self.modified = False
        self.linenum = None
        self._build_ui()
        self._build_menu()
        self._bind_keys()
        self._update_title()
        self.refresh_recent_menu()
        self.apply_line_number_setting()

    def _build_ui(self):
        self.status = tk.Label(self, anchor="w", padx=6, pady=1,
                               font=("Segoe UI", 9))
        self.status.pack(side="bottom", fill="x")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        self.text = FoxText(container)
        self.text.set_diagnostics_enabled(
            self.app.settings.get("show_diagnostics", False))
        self.linenum = LineNumberCanvas(container, self.text)

        yscroll = tk.Scrollbar(container, orient="vertical", command=self.text.yview)
        xscroll = tk.Scrollbar(container, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        self.linenum.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")
        yscroll.grid(row=0, column=2, sticky="ns")
        xscroll.grid(row=1, column=1, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)

        self.text.bind("<<Modified>>", lambda e: self._on_modified(), add="+")
        self.text.bind("<KeyRelease>", lambda e: self._update_status(), add="+")
        self.text.bind("<ButtonRelease>", lambda e: self._update_status(), add="+")

        self._update_status()

    def apply_line_number_setting(self):
        if self.app.settings.get("show_linenums", False):
            self.linenum.grid()
            self.linenum._redraw()
        else:
            self.linenum.grid_remove()

    def _build_menu(self):
        menubar = tk.Menu(self)

        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="New File", accelerator="Ctrl+N", command=self.new_file)
        m_file.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        self.m_recent = tk.Menu(m_file, tearoff=0)
        m_file.add_cascade(label="Recent Files", menu=self.m_recent)
        m_file.add_separator()
        m_file.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        m_file.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as)
        m_file.add_separator()
        m_file.add_command(label="Close", accelerator="Ctrl+W", command=self.destroy)
        menubar.add_cascade(label="File", menu=m_file)

        m_edit = tk.Menu(menubar, tearoff=0)
        m_edit.add_command(label="Undo", accelerator="Ctrl+Z",
                           command=lambda: self.text.event_generate("<<Undo>>"))
        m_edit.add_command(label="Redo", accelerator="Ctrl+Y",
                           command=lambda: self.text.event_generate("<<Redo>>"))
        m_edit.add_separator()
        m_edit.add_command(label="Cut", accelerator="Ctrl+X",
                           command=lambda: self.text.event_generate("<<Cut>>"))
        m_edit.add_command(label="Copy", accelerator="Ctrl+C",
                           command=lambda: self.text.event_generate("<<Copy>>"))
        m_edit.add_command(label="Paste", accelerator="Ctrl+V",
                           command=lambda: self.text.event_generate("<<Paste>>"))
        m_edit.add_separator()
        m_edit.add_command(label="Select All", accelerator="Ctrl+A",
                           command=lambda: self.text.tag_add("sel", "1.0", "end-1c"))
        menubar.add_cascade(label="Edit", menu=m_edit)

        m_format = tk.Menu(menubar, tearoff=0)
        m_format.add_command(label="Indent Region", accelerator="Tab",
                             command=lambda: self.text._on_tab(None))
        m_format.add_command(label="Dedent Region", accelerator="Shift+Tab",
                             command=lambda: self.text._on_shift_tab(None))
        m_format.add_separator()
        m_format.add_command(label="Comment Out Region", accelerator="Alt+3",
                             command=lambda: self.text.toggle_comment(True))
        m_format.add_command(label="Uncomment Region", accelerator="Alt+4",
                             command=lambda: self.text.toggle_comment(False))
        m_format.add_separator()
        m_format.add_command(label="Zoom In", command=lambda: self.text._zoom(+1))
        m_format.add_command(label="Zoom Out", command=lambda: self.text._zoom(-1))
        menubar.add_cascade(label="Format", menu=m_format)

        m_run = tk.Menu(menubar, tearoff=0)
        m_run.add_command(label="Run Module", accelerator="F5", command=self.run_module)
        m_run.add_separator()
        m_run.add_command(label="Shell", accelerator="Ctrl+6", command=self.app.show_shell)
        menubar.add_cascade(label="Run", menu=m_run)

        m_set = tk.Menu(menubar, tearoff=0)
        m_set.add_command(label="Highlight",
                          command=self.app.open_highlight_dialog)

        self.m_completion_var = tk.BooleanVar(
            value=self.app.completion_provider.enabled)
        m_set.add_checkbutton(label="Code Completion",
                              variable=self.m_completion_var,
                              command=self.app.toggle_completion)
        m_set.add_command(label="Completion Settings",
                          command=self.app.open_completion_settings)

        self.m_linenum_var = tk.BooleanVar(
            value=self.app.settings.get("show_linenums", False))
        m_set.add_checkbutton(label="Show Line Numbers",
                              variable=self.m_linenum_var,
                              command=self.app.toggle_line_numbers)

        self.m_diag_var = tk.BooleanVar(
            value=self.app.settings.get("show_diagnostics", False))
        m_set.add_checkbutton(label="Error & Warning Squiggles",
                              variable=self.m_diag_var,
                              command=self.app.toggle_diagnostics)

        menubar.add_cascade(label="Set", menu=m_set)

        m_help = tk.Menu(menubar, tearoff=0)
        m_help.add_command(label="About Foxange IDLE", command=self._about)
        menubar.add_cascade(label="Help", menu=m_help)

        self.config(menu=menubar)

    def refresh_completion_check(self):
        try:
            self.m_completion_var.set(self.app.completion_provider.enabled)
        except Exception:
            pass

    def refresh_linenum_check(self):
        try:
            self.m_linenum_var.set(
                self.app.settings.get("show_linenums", False))
        except Exception:
            pass

    def refresh_diag_check(self):
        try:
            self.m_diag_var.set(
                self.app.settings.get("show_diagnostics", False))
        except Exception:
            pass

    def refresh_recent_menu(self):
        m = self.m_recent
        m.delete(0, "end")
        files = self.app.recent_files
        if not files:
            m.add_command(label="(empty)", state="disabled")
            return
        for f in files:
            name = os.path.basename(f)
            if len(name) > 45:
                name = name[:42] + "..."
            m.add_command(label=name, command=lambda p=f: self.open_file(p))
        m.add_separator()
        m.add_command(label="Clear List", command=self.app.clear_recent_files)

    def _bind_keys(self):
        self.bind("<Control-n>", lambda e: self.new_file())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-S>", lambda e: self.save_as())
        self.bind("<Control-w>", lambda e: self.destroy())
        self.bind("<F5>", lambda e: self.run_module())
        self.bind("<Control-Key-6>", lambda e: self.app.show_shell())
        self.bind("<Alt-Key-3>", lambda e: self.text.toggle_comment(True))
        self.bind("<Alt-Key-4>", lambda e: self.text.toggle_comment(False))

    def _update_status(self):
        idx = self.text.index("insert")
        line, col = idx.split(".")
        self.status.configure(text=f"Ln: {line}  Col: {col}")

    def _on_modified(self):
        if self.text.edit_modified():
            self.text.edit_modified(False)
            if not self.modified:
                self.modified = True
                self._update_title()

    def _update_title(self):
        name = os.path.basename(self.filename) if self.filename else "untitled"
        self.title(f"{'*' if self.modified else ''}{name} - Foxange IDLE")

    def new_file(self):
        if not self._maybe_save():
            return
        self.text.delete("1.0", "end")
        self.filename = None
        self.modified = False
        self._update_title()

    def open_file(self, path=None):
        if not self._maybe_save():
            return

        if path is None:
            path = filedialog.askopenfilename(
                parent=self, title="Open",
                filetypes=[("Foxange Script", "*.fx"), ("Python Script", "*.py"), ("All Files", "*.*")])
            if not path:
                return

        if not os.path.exists(path):
            messagebox.showerror("Error", f"File not found:\n{path}", parent=self)
            self.app.remove_recent_file(path)
            self.refresh_recent_menu()
            return

        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Cannot read file: {e}", parent=self)
            return

        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.filename = path
        self.modified = False
        self.text.force_highlight()
        self._update_title()

        self.app.add_recent_file(path)
        self.refresh_recent_menu()

    def save_file(self):
        if not self.filename:
            return self.save_as()
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", "end-1c"))
        except Exception as e:
            messagebox.showerror("Error", f"Cannot write file: {e}", parent=self)
            return False
        self.modified = False
        self._update_title()
        return True

    def save_as(self):
        path = filedialog.asksaveasfilename(
            parent=self, title="Save As", defaultextension=".fx",
            filetypes=[("Foxange Script", "*.fx")])
        if not path:
            return False
        self.filename = path
        ok = self.save_file()
        if ok:
            self.app.add_recent_file(path)
            self.refresh_recent_menu()
        return ok

    def _maybe_save(self):
        if not self.modified:
            return True
        ans = messagebox.askyesnocancel(
            "Foxange IDLE", "Save the current file?", parent=self)
        if ans is None:
            return False
        if ans:
            return self.save_file()
        return True

    def run_module(self):
        if self.modified and self.filename:
            self.save_file()
        code = self.text.get("1.0", "end-1c")
        self.app.run_code(code, self.filename or "<untitled>")

    def _about(self):
        messagebox.showinfo(
            "About Foxange IDLE",
            "Foxange IDLE\n\n"
            "made by SLC\n"
            "bugs and your idea : https://bugs-foxange.fwh.is",
            parent=self)


class FoxIdleApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Foxange IDLE")

        self.runtime = FxRuntime()
        self.shell_win = None
        self.shell_text = None
        self.editor = None
        self._highlight_dialog = None
        self._completion_dialog = None

        self.completion_provider = CompletionProvider()
        self.settings = load_settings()

        self.recent_files = load_recent_files()

        self.runtime.install_input(self._inline_input)

        self.editor = EditorWindow(self.root, self)
        self.editor.protocol("WM_DELETE_WINDOW", self._on_editor_close)
        self.editor.text.apply_completion_settings(self.completion_provider)

    def add_recent_file(self, path):
        push_recent_file(self.recent_files, path)
        save_recent_files(self.recent_files)

    def remove_recent_file(self, path):
        try:
            path = os.path.abspath(path)
            if path in self.recent_files:
                self.recent_files.remove(path)
                save_recent_files(self.recent_files)
        except Exception:
            pass

    def clear_recent_files(self):
        self.recent_files.clear()
        save_recent_files(self.recent_files)
        if self.editor:
            self.editor.refresh_recent_menu()

    def toggle_completion(self):
        self.completion_provider.enabled = not self.completion_provider.enabled
        self.completion_provider.save()
        self.refresh_completion_menu()
        self.apply_completion_settings()

    def refresh_completion_menu(self):
        if self.editor:
            self.editor.refresh_completion_check()

    def apply_completion_settings(self):
        if self.editor is not None and self.editor.text is not None:
            self.editor.text.apply_completion_settings(self.completion_provider)
        if self.shell_text is not None:
            try:
                self.shell_text.apply_completion_settings(self.completion_provider)
            except Exception:
                pass

    def open_completion_settings(self):
        if self._completion_dialog is not None \
                and self._completion_dialog.winfo_exists():
            self._completion_dialog.lift()
            self._completion_dialog.focus_set()
            return
        self._completion_dialog = CompletionSettingsDialog(self.editor, self)

    def toggle_line_numbers(self):
        current = self.settings.get("show_linenums", False)
        self.settings["show_linenums"] = not current
        save_settings(self.settings)
        if self.editor:
            self.editor.apply_line_number_setting()
            self.editor.refresh_linenum_check()

    def toggle_diagnostics(self):
        current = self.settings.get("show_diagnostics", False)
        self.settings["show_diagnostics"] = not current
        save_settings(self.settings)
        if self.editor:
            self.editor.text.set_diagnostics_enabled(
                self.settings["show_diagnostics"])
            self.editor.text.force_highlight()
            self.editor.refresh_diag_check()

    def _inline_input(self, prompt=""):
        if self.shell_text is not None and self.shell_win is not None \
                and self.shell_win.winfo_exists():
            return self.shell_text.ask_input(prompt)
        from tkinter import simpledialog
        res = simpledialog.askstring("Input", prompt or "Enter value:",
                                     parent=self.root)
        return res if res is not None else ""

    def show_shell(self):
        if self.shell_win is None or not self.shell_win.winfo_exists():
            self._create_shell()
        self.shell_win.deiconify()
        self.shell_win.lift()
        self.shell_text.focus_set()

    def _create_shell(self):
        self.shell_win = tk.Toplevel(self.root)
        self.shell_win.title("*Foxange IDLE Shell*")
        self.shell_win.geometry(SHELL_SIZE)
        self.shell_win.protocol("WM_DELETE_WINDOW", self._on_shell_close)

        status = tk.Label(self.shell_win, anchor="w", padx=6, pady=1,
                          font=("Segoe UI", 9))
        status.pack(side="bottom", fill="x")

        container = tk.Frame(self.shell_win)
        container.pack(side="top", fill="both", expand=True)

        self.shell_text = FoxShell(container, self.runtime)
        self.shell_text.apply_completion_settings(self.completion_provider)
        yscroll = tk.Scrollbar(container, orient="vertical",
                               command=self.shell_text.yview)
        self.shell_text.configure(yscrollcommand=yscroll.set)
        self.shell_text.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        def update_status(e=None):
            idx = self.shell_text.index("insert")
            line, col = idx.split(".")
            status.configure(text=f"Ln: {line}  Col: {col}")

        self.shell_text.bind("<KeyRelease>", update_status, add="+")
        self.shell_text.bind("<ButtonRelease>", update_status, add="+")

        self.shell_text.banner()
        self.shell_text.set_prompt(cont=False)
        self.shell_text.focus_set()

    def _on_shell_close(self):
        sh = self.shell_text
        if sh is not None and sh._input_var is not None:
            var = sh._input_var
            sh._input_var = None
            try:
                var.set("")
            except Exception:
                pass
        self.shell_win.withdraw()

    def run_code(self, code, filename):
        if self.shell_win is None or not self.shell_win.winfo_exists():
            self._create_shell()
        self.shell_win.deiconify()
        self.shell_win.lift()

        self.runtime.reset()

        sh = self.shell_text
        sh.delete("1.0", "end")
        sh._pending = ""
        sh._input_var = None
        sh.iomark_locked = True
        sh.mark_set("iomark", "end-1c")

        sh.banner()
        sh._append(f"= RESTART: {filename}\n", "RESTART")

        if code.strip():
            sh.current_file = filename
            sh._execute(code)

        sh.set_prompt(cont=False)
        sh.focus_set()

    def open_highlight_dialog(self):
        if self._highlight_dialog is not None \
                and self._highlight_dialog.winfo_exists():
            self._highlight_dialog.lift()
            self._highlight_dialog.focus_set()
            return
        self._highlight_dialog = HighlightDialog(self.editor, self)

    def _on_editor_close(self):
        self.root.quit()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    FoxIdleApp().run()


if __name__ == "__main__":
    main()
