from foxange.interpreter import run
import os

code = ""
while True:
    code_file_live = input("请输入文件路径:").strip().strip('"')
    if not code_file_live.endswith(".fx"):
        print("错误：仅支持 .fx 文件！")
        continue
    try:
        with open(code_file_live, "r", encoding="utf-8") as f:
            code += f.read()
            code += "\n"
        run(code)
    except SyntaxError as e:
        print(f"语法错误：{e}")
    except RuntimeError as e:
        print(f"运行错误：{e}")
    except Exception as e:
        print(f"错误：{e}")
