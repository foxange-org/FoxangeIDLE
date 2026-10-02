class FoxangeError(Exception):

    def __init__(self, message, exc_type=None,
                 file_path=None, line=None, col=None,
                 source_line=None):
        super().__init__(message)
        self.exc_type = exc_type or "Error"
        self.file_path = file_path
        self.line = line if line is not None else 0
        self.col = col if col is not None else 0
        self.source_line = source_line

def format_error(exc, source_lines=None):
    if not isinstance(exc, FoxangeError):
        return str(exc)

    parts = []

    if exc.file_path:
        parts.append(f"<file : {exc.file_path}> <line: {exc.line}>")
    else:
        parts.append(f"<line: {exc.line}>")

    sl = exc.source_line
    if sl is None and source_lines is not None:
        if isinstance(source_lines, dict) and exc.file_path:
            lines = source_lines.get(exc.file_path, [])
        elif isinstance(source_lines, list):
            lines = source_lines
        else:
            lines = []
        idx = exc.line - 1
        if 0 <= idx < len(lines):
            sl = lines[idx].rstrip("\n").rstrip("\r")

    if sl is not None:
        parts.append(f"    {sl}")
        indent = "    "
        marker = indent + " " * (exc.col) + "^"
        parts.append(marker)

    parts.append(f"{exc.exc_type}: {exc.args[0] if exc.args else ''}")

    return "\n".join(parts)
