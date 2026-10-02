import sys
import os


def main():
    if len(sys.argv) < 2:
        _start_gui()
        return

    cmd = sys.argv[1]

    if cmd == "gui":
        _start_gui()
    elif cmd == "console":
        _start_console()
    elif cmd == "run":
        if len(sys.argv) < 3:
            print("Usage: python -m foxange run <file.fx>")
            sys.exit(1)
        filepath = sys.argv[2]
        _run_file(filepath)
    elif cmd in ("-h", "--help", "help"):
        print(__doc__)
    else:
        filepath = cmd
        _run_file(filepath)


def _start_gui():
    from .gui import main as gui_main
    gui_main()


def _start_console():
    from .console import main as console_main
    console_main()


def _run_file(filepath):
    if not os.path.exists(filepath):
        print(f"Error: file '{filepath}' not found.")
        sys.exit(1)
    from .interpreter import run_file
    run_file(filepath)


if __name__ == "__main__":
    main()
