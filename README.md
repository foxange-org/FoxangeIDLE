Foxange 语言教程
一、Hello World
---------------

    print("Hello, Foxange!")


二、变量与类型
---------------

Foxange 使用 let 声明变量，可显式指定类型：

    let int x = 10
    let str name = "Foxange"
    let bool flag = True
    let float pi = 3.14

类型推导（省略类型标注时由初始值推断）：

    let x = 42              # int
    let msg = "hello"       # str


三、基本数据类型
-----------------

    int       整数，如 1, -5, 100
    float     浮点数，如 3.14, -0.5
    str       字符串，用 " 或 ' 包裹
    bool      布尔值 True / False

字符串拼接：

    let greeting = "Hello" + " " + "World"
    print(greeting)   # Hello World


四、容器类型
-------------

4.1 列表 list<T>

    let list<int> nums = [1, 2, 3, 4, 5]
    print(nums)                # [1, 2, 3, 4, 5]
    print(len(nums))           # 5

4.2 映射 map<K, V>

    let map<str, int> ages = {"Alice": 25, "Bob": 30}
    print(ages["Alice"])       # 25

4.3 集合 set<T>

    let set<int> s = {1, 2, 3}

4.4 队列 queue<T>

    let queue<int> q = [1, 2, 3]
    q.push(4)
    print(q.pop())             # 1

4.5 栈 stack<T>

    let stack<int> st = [1, 2, 3]
    st.push(4)
    print(st.pop())            # 4

4.6 对 pair<A, B>

    let pair<int, str> p = (42, "answer")


五、控制流
-----------

5.1 if / elif / else

    let x = 10
    if x > 5 :
        print("big")
    elif x > 0 :
        print("small")
    else :
        print("zero")

注意：条件后必须有冒号 :

5.2 for 循环

    for item in [1, 2, 3] :
        print(item, end=" ")

    let list<int> arr = [10, 20, 30]
    for v in arr :
        print(v)

5.3 while 循环

    let int i = 1
    while i <= 5 :
        print(i, end=" ")
        i = i + 1
    print()

5.4 break / continue

    for i in [1, 2, 3, 4, 5] :
        if i == 3 :
            continue
        if i == 5 :
            break
        print(i)


六、输出与输入
---------------

6.1 print

    print("hello")                    # 换行
    print("a", "b", "c")             # a b c
    print("x", end="!")              # x!
    print("y", "z", end="")          # y z

6.2 input

    let name = input("你的名字: ")
    print("你好,", name)

6.3 run_to_python —— 运行 Python 代码 / 文件

直接执行 Python 代码字符串：

    run_to_python("print('hello from python')")
    run_to_python("import math\nprint(math.sqrt(16))")   # 4.0

执行 Python 脚本文件（后续参数原样透传给脚本）：

    run_to_python("D:/scripts/test.py")                 # 等价 python test.py
    run_to_python("D:/scripts/test.py", "awa")          # 等价 python test.py awa

规则：
  - 第一个参数是字符串、且该路径是存在的文件 → 按文件模式运行（返回进程退出码）
  - 否则按 Python 代码字符串执行（返回 None）


七、函数
---------

7.1 定义函数

    def greet(name) :
        print("Hello,", name)

    greet("World")            # Hello, World

7.2 返回值

    def add(a, b) :
        return a + b

    print(add(3, 5))          # 8

7.3 func 别名

得益于 @appendToken（见第十章节），可以用 func 代替 def：

    @appendToken def func

    func double(x) :
        return x * 2

7.4 函数重载（按形参类型）

同名函数允许按形参类型不同多次定义，调用时按实参类型自动选择最匹配的版本：

    def a(int awa) :
        return "整数"
    def a(float awa) :
        return "小数"

    print(a(123))          # 整数
    print(a(123.123))      # 小数

    def a(str awa) :
        return "字符串"
    print(a("hi"))         # 字符串

规则：
  - 签名由形参类型序列决定；形参类型完全相同的新定义会覆盖旧定义
  - 调用时按实参类型精确匹配，位置参数与关键字参数均可参与分发
  - 无类型标注的形参是通配，作为兜底；带类型的重载优先级高于通配
  - 泛型标注按主类型匹配，如 list<int> 可匹配任意 list
  - 没有任何签名匹配时抛出 TypeError

7.5 inline —— 覆盖内置函数

inline 把函数直接写入全局环境，可覆盖 len / int / open 等内置函数：

    inline func len(x) :
        return 42
    print(len([1, 2, 3]))     # 42（覆盖了内置 len）

    inline def int(x) :
        return 999
    print(int("42"))          # 999（覆盖了内置 int）

注意：
  - print / input 是语句级语法，不走函数调用，无法用 inline 覆盖
  - 普通 def 在全局作用域同样会覆盖同名内置函数；inline 的意义在于任意作用域（含函数内部）都能强制写入全局环境

7.6 inline struct / inline class —— 覆盖类型与类

inline 同样可用于 struct / class 定义，把类型直接写入全局环境，
可覆盖内置容器类型（List / Map / Set / Queue / Stack / Pair）或已有类：

    inline struct List :
        let kind = "mylist"
        def show(self) :
            print("custom list", self.kind)

    let l = List()          # 覆盖了内置 List
    print(l.kind)           # mylist

    inline class Map :
        def __init__(self) :
            self.tag = "mymap"
        def get_tag(self) :
            print("custom map", self.tag)

    let m = Map()           # 覆盖了内置 Map
    m.get_tag()             # custom map mymap

与 inline 函数一致：在任意作用域（含函数内部）定义都会强制写入全局环境。


八、类
-------

8.1 基本类定义

    class Person :
        def __init__(self, name, age) :
            self.name = name
            self.age = age

        def greet(self) :
            print("I am", self.name, "age", self.age)

    let p = Person("Alice", 25)
    p.greet()                   # I am Alice age 25

8.2 泛型类

    class Box<T> :
        def __init__(self, value) :
            self.value = value

        def get(self) :
            return self.value

    let Box<int> b = Box<int>(42)
    print(b.get())              # 42

8.3 多类型参数

    class Pair<A, B> :
        def __init__(self, first, second) :
            self.first = first
            self.second = second

    let p = Pair<int, str>(1, "one")


九、模块导入
-------------

9.1 导入 Foxange 模块（.fx 文件）

    import Test              # 导入 Test.fx
    Test.test_print()        # 调用模块内函数

9.2 导入 Python 内置模块

    import math
    print(math.sqrt(16))     # 4.0

    import random
    print(random.randint(1, 100))

    import json
    let data = {"a": 1, "b": 2}
    print(json.dumps(data))


十、预处理器指令（@define / @appendToken）
------------------------------------------

10.1 @define —— 文本宏替换

对象宏：

    @define PI 3.14
    @define MSG "hello"

    print(PI)                # 3.14
    print(MSG)               # hello

函数宏：

    @define MAX(a, b) (a > b) ? a : b
    @define SQUARE(x) x * x

    print(MAX(3, 8))         # 8
    print(SQUARE(5))         # 25

注意：@define 仅当前文件可见，不会跨 import 泄漏。

10.2 @appendToken —— 扩展关键字表

    @appendToken def fn     # fn 变成 def 的同义词

    fn say(msg) :
        print(msg)

    say("it works!")


十一、三元表达式
-----------------

    let result = (x > 0) ? "positive" : "non-positive"


十二、类型系统（Types 命名空间）
--------------------------------

    print(Types.is_int(42))          # True
    print(Types.is_str("hello"))     # True
    print(Types.is_list([1,2,3]))   # True

    let int x = Types.cast_to_int("42")
    print(x)                         # 42


十三、错误命名空间（Errors）
------------------------------

Foxange 提供标准异常类型：

    Errors.ValueError      # 值错误
    Errors.TypeError       # 类型错误
    Errors.IndexError      # 索引错误
    Errors.KeyError        # 键错误
    Errors.ImportError     # 导入错误

示例用法：

    let list<int> arr = [1, 2, 3]
    if len(arr) > 5 :
        raise Errors.ValueError("too many elements")


十四、REPL 交互模式
--------------------

启动交互模式：

    python foxange_repl.py

交互模式下支持：
  - 逐行输入 Foxange 代码
  - 以冒号或左花括号 { 结尾自动进入多行续写（按空行结束）
  - .exit 退出
  - 支持 @define 和 @appendToken（REPL 会话内累积生效）


十五、多行表达式
------------------

以冒号结尾的行会自动进入续行模式：

    if True :               ← 按回车
    ...     print("yes")   ← 续写
    ...                     ← 空行提交

以左花括号 { 结尾同样会自动进入续行模式（花括号块，见第十六章）：

    if True {               ← 按回车
    ...     print("yes")   ← 续写
    ...     }               ← 闭合花括号
    ...                     ← 空行提交


十六、花括号块语法
---------------------

if / elif / else、for、while、def / func、class、struct、try 等块语句，
除了原「冒号 + 缩进」与「冒号 + 单行体」写法外，还支持花括号写法：

    if x > 5 {
        print("big")
    } elif x > 0 {
        print("small")
    } else {
        print("zero")
    }

    for i in [1, 2, 3] {
        print(i)
    }

    while i < 10 {
        i = i + 1
    }

    def add(a, b) {
        return a + b
    }

    class Point {
        def __init__(self, x) {
            self.x = x
        }
    }

    struct Pair {
        let a = 1
        let b = 2
    }

    try {
        let x = y + 1          # 触发未定义变量错误
    } have Error as e {
        print(e)               # 捕获并输出错误信息
    }

也支持「冒号 + 花括号」混合写法：

    if x > 5 : {
        print("big")
    }

规则：
  - 花括号块必须完整闭合（每层 { 对应 }）；空块 {} 合法
  - 花括号写法与冒号缩进写法可混用、可嵌套
  - 单行花括号块合法：if x > 5 { print("big") }
  - inline struct / inline class 同样支持花括号写法
  - map 字面量、lambda、三元表达式等不受影响


十七、结构体 struct
---------------------

struct 用于定义结构体类型，成员可以是变量（字段）和函数（方法）。

    struct Point :
        let x = 1
        let y = 2
        def show(self) :
            print("point", self.x, self.y)

    let p = Point()
    print(p.x, p.y)         # 1 2
    p.x = 10
    p.show()                # point 10 2

成员函数需显式声明 self 参数（与类一致）。结构体也支持 __init__ 构造：

    struct Person :
        let name = "?"
        def __init__(self, n) :
            self.name = n
        def say(self) :
            print("hi", self.name)

    let a = Person("tom")
    a.say()                 # hi tom


附录：运算符速查
------------------

    算术：  +  -  *  /  %
    比较：  ==  !=  <  >  <=  >=
    逻辑：  and  or  not
    位运算： &  |  ^  ~  <<  >>
    三元：  (条件) ? 值1 : 值2
    成员：  in  not in
