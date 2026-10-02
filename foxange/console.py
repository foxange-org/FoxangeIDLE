import sys
import traceback

_NEED_CONTINUATION_KEYWORDS = {
    "if", "elif", "else", "for", "while", "with",
    "def", "class", "try", "have", "except", "finally",
}

def _needs_continuation(line: str) -> bool:
    stripped = line.rstrip()
    if not stripped:
        return False

    stack = []
    in_single_quote = False
    in_double_quote = False
    in_triple_single = False
    in_triple_double = False
    escape = False

    i = 0
    while i < len(stripped):
        ch = stripped[i]

        if escape:
            escape = False
            i += 1
            continue

        if not in_single_quote and not in_double_quote:
            if stripped[i:i + 3] == '"""' and not in_triple_single:
                in_triple_double = not in_triple_double
                i += 3
                continue
            if stripped[i:i + 3] == "'''" and not in_triple_double:
                in_triple_single = not in_triple_single
                i += 3
                continue

        if in_triple_single or in_triple_double:
            if ch == "\\":
                escape = True
            i += 1
            continue

        if ch == "\\":
            escape = True
            i += 1
            continue

        if ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif ch == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif not in_single_quote and not in_double_quote:
            if ch in "([{":
                stack.append(ch)
            elif ch in ")]}":
                if not stack:
                    return True
                last = stack[-1]
                if (ch == ")" and last == "(") or \
                   (ch == "]" and last == "[") or \
                   (ch == "}" and last == "{"):
                    stack.pop()
                else:
                    return True
        i += 1

    if in_single_quote or in_double_quote or in_triple_single or in_triple_double:
        return True

    if stack:
        return True

    if stripped.endswith("\\"):
        return True

    first_word = stripped.split()[0] if stripped.split() else ""
    first_word = first_word.rstrip(":")
    if first_word in _NEED_CONTINUATION_KEYWORDS and stripped.endswith(":"):
        return True

    return False

def repl():
    print("Foxange v1.0.0  (Python 实现)")
    print("兼具 Python 的优雅与 C 的控制和速度")
    print('输入 ":quit" 或 ":exit" 退出')
    print()

    try:
        from .interpreter import run
    except ImportError:
        import os as _os
        sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
        from foxange.interpreter import run

    while True:
        buffer = ""
        try:
            line = input("fox> ")
            if not line:
                continue

            line_stripped = line.strip()

            if line_stripped in (":quit", ":exit"):
                break

            buffer = line + "\n"

            while _needs_continuation(line_stripped):
                try:
                    line = input("... ")
                    if not line:
                        break
                    line_stripped = line.strip()
                    if line_stripped in (":quit", ":exit"):
                        print("(使用空行退出多行模式后再输入 :quit)")
                        continue
                    buffer += line + "\n"
                except KeyboardInterrupt:
                    print()
                    buffer = ""
                    break
                except EOFError:
                    print()
                    break

            if not buffer:
                continue

            try:
                result = run(buffer.strip())
                if result is not None:
                    print(repr(result))
            except SyntaxError as e:
                if "EOF" in str(e) or "Expected" in str(e):
                    print(f"SyntaxError: {e}")
                else:
                    print(f"SyntaxError: {e}")
            except Exception as e:
                print(f"{type(e).__name__}: {e}")

        except KeyboardInterrupt:
            print("\nKeyboardInterrupt")
            continue
        except EOFError:
            print()
            break

    print("再见!")

def main():
    repl()

if __name__ == "__main__":
    main()
