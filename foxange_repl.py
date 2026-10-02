import sys, os, json, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)

from foxange.interpreter import FoxangeInterpreter, _repl_preprocessor
from foxange.lexer import Lexer
from foxange.parser import Parser
from foxange.ast_nodes import ExpressionStmt, InputStmt
from foxange.error_utils import FoxangeError, format_error

REPL_FILES_PATH = os.path.join(SCRIPT_DIR, "foxange", "lib", "repl", "repl_files.json")

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_repl_files():
    if not os.path.exists(REPL_FILES_PATH):
        print(f"警告：找不到 {REPL_FILES_PATH}，无自动加载文件")
        return []
    with open(REPL_FILES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("警告：repl_files.json 格式错误（应为一个数组）")
        return []
    return data


if __name__ == "__main__":
    interpreter = FoxangeInterpreter()
    interpreter.current_file_dir = SCRIPT_DIR

    files_to_load = load_repl_files()
    code = ""

    if not files_to_load:
        print("没有配置自动加载的 .fx 文件，直接进入交互模式")
    else:
        for fx_file in files_to_load:
            if os.path.isabs(fx_file):
                fx_path = fx_file
            else:
                fx_path = os.path.normpath(os.path.join(SCRIPT_DIR, fx_file))
            if not os.path.exists(fx_path):
                print(f"警告：找不到 {fx_path}，跳过")
                continue
            print(f"已加载: {fx_file}")
            try:
                file_code = load_file(fx_path)
                code += file_code + "\n"
            except Exception as e:
                print(f"读取失败 {fx_file}：{e}")
                continue

        if code:
            try:
                interpreter.current_file_path = None
                code = _repl_preprocessor.process(code)
                lexer = Lexer(code)
                tokens = lexer.tokenize()
                tokens = _repl_preprocessor.apply_force_annotations(tokens)
                parser = Parser(tokens, source=code)
                ast = parser.parse()
                interpreter.interpret(ast)
            except FoxangeError as e:
                print(format_error(e, source_lines=code.split('\n')))
                sys.exit(1)
            except SyntaxError as e:
                print(str(e))
                sys.exit(1)

    print()
    print("进入交互模式 (输入 .exit 退出)")
    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n已退出")
            break

        if not line:
            continue
        if line == ".exit":
            print("已退出")
            break

        if line.rstrip().endswith(":") or line.rstrip().endswith("{"):
            lines = [line]
            while True:
                try:
                    cont = input("... ")
                except (EOFError, KeyboardInterrupt):
                    print("\n已退出")
                    break
                if cont == "":
                    break
                lines.append(cont)
            source = "\n".join(lines)
        else:
            source = line

        try:
            interpreter.current_file_path = "<REPL>"
            source = _repl_preprocessor.process(source)
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens, source=source, file_path="<REPL>")
            ast = parser.parse()
            result = interpreter.interpret(ast)
            if ast.statements and isinstance(ast.statements[-1], (ExpressionStmt, InputStmt)):
                if result is not None:
                    print(repr(result))
        except FoxangeError as e:
            print(format_error(e, source_lines=source.split('\n')))
        except SyntaxError as e:
            m = re.match(r"Lexer Error at line (\d+), col (\d+): (.*)", str(e))
            if m:
                src_lines = source.split("\n")
                line = int(m.group(1))
                fe = FoxangeError(m.group(3), exc_type="SyntaxError",
                                  file_path="<REPL>", line=line, col=int(m.group(2)),
                                  source_line=src_lines[line-1] if 0 < line <= len(src_lines) else None)
                print(format_error(fe))
            else:
                print(str(e))
