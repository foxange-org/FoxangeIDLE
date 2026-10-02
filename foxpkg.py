import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from foxange.pkg import install, uninstall, list_packages, info, init_package


HELP = """Foxange 包管理器 (foxpkg)

命令:
  install  <路径>    从本地目录安装包
  uninstall <名称>   卸载包
  list               列出已安装的包
  info    <名称>     查看包详情
  init    <名称>     在当前目录初始化新包
"""


def main():
    args = sys.argv[1:]

    if not args:
        print(HELP)
        return

    cmd = args[0].lower()

    try:
        if cmd == "install":
            if len(args) < 2:
                print("用法: foxpkg install <包目录路径>")
                return
            install(args[1])

        elif cmd == "uninstall":
            if len(args) < 2:
                print("用法: foxpkg uninstall <包名>")
                return
            uninstall(args[1])

        elif cmd == "list":
            list_packages()

        elif cmd == "info":
            if len(args) < 2:
                print("用法: foxpkg info <包名>")
                return
            info(args[1])

        elif cmd == "init":
            if len(args) < 2:
                print("用法: foxpkg init <包名>")
                return
            init_package(os.getcwd(), args[1])

        elif cmd in ("help", "-h", "--help"):
            print(HELP)

        else:
            print(f"未知命令: {cmd}")
            print(HELP)

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
