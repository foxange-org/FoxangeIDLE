_input_func = input

class FoxangeList:

    def __init__(self, elements=None):
        self._data = list(elements) if elements else []

    def size(self):
        return len(self._data)

    def empty(self):
        return len(self._data) == 0

    def append(self, value):
        self._data.append(value)

    def pop(self, index=-1):
        if isinstance(index, int):
            return self._data.pop(index)
        else:
            self._data.remove(index)

    def front(self):
        if not self._data:
            raise IndexError("front from empty list")
        return self._data[0]

    def back(self):
        if not self._data:
            raise IndexError("back from empty list")
        return self._data[-1]

    def insert(self, index, value):
        self._data.insert(index, value)

    def remove(self, value):
        self._data.remove(value)

    def count(self, value):
        return self._data.count(value)

    def index(self, value):
        return self._data.index(value)

    def clear(self):
        self._data.clear()

    def extend(self, items):
        self._data.extend(items)

    def reverse(self):
        self._data.reverse()

    def sort(self, reverse=False):
        self._data.sort(reverse=reverse)

    def copy(self):
        return FoxangeList(self._data)

    def __getitem__(self, index):
        return self._data[index]

    def __setitem__(self, index, value):
        self._data[index] = value

    def __delitem__(self, index):
        del self._data[index]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, item):
        return item in self._data

    def __repr__(self):
        return f"[{', '.join(repr(x) for x in self._data)}]"

    def __str__(self):
        return self.__repr__()

class FoxangeMap:

    def __init__(self, data=None):
        self._data = dict(data) if data else {}

    def size(self):
        return len(self._data)

    def empty(self):
        return len(self._data) == 0

    def keys(self):
        return FoxangeList(self._data.keys())

    def values(self):
        return FoxangeList(self._data.values())

    def pop(self, key):
        return self._data.pop(key, None)

    def put(self, key, value):
        self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)

    def setdefault(self, key, default=None):
        return self._data.setdefault(key, default)

    def popitem(self):
        if not self._data:
            raise KeyError("popitem from empty map")
        k, v = self._data.popitem()
        return FoxangePair(k, v)

    def items(self):
        return FoxangeList([FoxangePair(k, v) for k, v in self._data.items()])

    def update(self, other):
        if isinstance(other, FoxangeMap):
            self._data.update(other._data)
        else:
            self._data.update(other)

    def clear(self):
        self._data.clear()

    def copy(self):
        return FoxangeMap(self._data)

    def has(self, key):
        return key in self._data

    def __getitem__(self, key):
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __contains__(self, key):
        return key in self._data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        items = ", ".join(f"{k!r}: {v!r}" for k, v in self._data.items())
        return "{" + items + "}"

    def __str__(self):
        return self.__repr__()

class FoxangeSet:

    def __init__(self, elements=None):
        self._data = set(elements) if elements else set()

    def size(self):
        return len(self._data)

    def empty(self):
        return len(self._data) == 0

    def add(self, value):
        self._data.add(value)

    def remove(self, value):
        self._data.discard(value)

    def pop(self):
        return self._data.pop()

    def discard(self, value):
        self._data.discard(value)

    def clear(self):
        self._data.clear()

    def union(self, other):
        o = other._data if isinstance(other, FoxangeSet) else other
        return FoxangeSet(self._data.union(o))

    def intersection(self, other):
        o = other._data if isinstance(other, FoxangeSet) else other
        return FoxangeSet(self._data.intersection(o))

    def difference(self, other):
        o = other._data if isinstance(other, FoxangeSet) else other
        return FoxangeSet(self._data.difference(o))

    def symmetric_difference(self, other):
        o = other._data if isinstance(other, FoxangeSet) else other
        return FoxangeSet(self._data.symmetric_difference(o))

    def update(self, other):
        o = other._data if isinstance(other, FoxangeSet) else other
        self._data.update(o)

    def copy(self):
        return FoxangeSet(self._data)

    def is_subset(self, other):
        o = other._data if isinstance(other, FoxangeSet) else other
        return self._data.issubset(o)

    def is_superset(self, other):
        o = other._data if isinstance(other, FoxangeSet) else other
        return self._data.issuperset(o)

    def __contains__(self, item):
        return item in self._data

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        if not self._data:
            return "set()"
        return "{" + ", ".join(repr(x) for x in self._data) + "}"

    def __str__(self):
        return self.__repr__()

class FoxangeQueue:

    def __init__(self, elements=None):
        from collections import deque
        self._data = deque(elements) if elements else deque()

    def size(self):
        return len(self._data)

    def empty(self):
        return len(self._data) == 0

    def append(self, value):
        self._data.append(value)

    def enqueue(self, value):
        self._data.append(value)

    def pop(self):
        return self._data.popleft()

    def dequeue(self):
        return self._data.popleft()

    def front(self):
        return self._data[0] if self._data else None

    def back(self):
        return self._data[-1] if self._data else None

    def peek(self):
        return self._data[0] if self._data else None

    def clear(self):
        self._data.clear()

    def copy(self):
        return FoxangeQueue(self._data)

    def __contains__(self, item):
        return item in self._data

    def __getitem__(self, index):
        return self._data[index]

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        return "(" + ", ".join(repr(x) for x in self._data) + ")"

    def __str__(self):
        return self.__repr__()

class FoxangeStack:

    def __init__(self, elements=None):
        self._data = list(elements) if elements else []

    def empty(self):
        return len(self._data) == 0

    def size(self):
        return len(self._data)

    def append(self, value):
        self._data.append(value)

    def pop(self):
        return self._data.pop()

    def push(self, value):
        self._data.append(value)

    def peek(self):
        return self._data[-1] if self._data else None

    def clear(self):
        self._data.clear()

    def copy(self):
        return FoxangeStack(self._data)

    def __contains__(self, item):
        return item in self._data

    def top(self):
        return self._data[-1] if self._data else None

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return "Stack(" + repr(self._data) + ")"

    def __str__(self):
        return self.__repr__()

class FoxangePair:

    def __init__(self, first, second):
        self._first = first
        self._second = second

    def first(self):
        return self._first

    def second(self):
        return self._second

    def swap(self):
        self._first, self._second = self._second, self._first

    def set_first(self, value):
        self._first = value

    def set_second(self, value):
        self._second = value

    def to_list(self):
        return FoxangeList([self._first, self._second])

    def __getitem__(self, key):
        if key == "first":
            return self._first
        elif key == "second":
            return self._second
        raise KeyError(key)

    def __repr__(self):
        return f'{{"first": {self._first!r}, "second": {self._second!r}}}'

    def __str__(self):
        return self.__repr__()

class BuiltinEnvironment:
    @staticmethod
    def builtin_print(*args, **kwargs):
        values = list(args)
        end = kwargs.get("end", "\n")
        space = kwargs.get("space", "")
        file = kwargs.get("file", "")
        output = space.join(str(v) for v in values) + end
        if file:
            with open(file, "a", encoding="utf-8") as f:
                f.write(output)
        else:
            print(output, end="")
        return None

    @staticmethod
    def builtin_input(prompt=""):
        if prompt:
            return _input_func(str(prompt))
        return _input_func()

    @staticmethod
    def builtin_len(obj):
        return len(obj)

    @staticmethod
    def builtin_del(obj):
        pass

    @staticmethod
    def builtin_open(filename, mode="r"):
        return open(filename, mode, encoding="utf-8")

    @staticmethod
    def builtin_int(value, base=10):
        if isinstance(value, str):
            return int(value, base)
        return int(value)

    @staticmethod
    def builtin_float(value):
        return float(value)

    @staticmethod
    def builtin_str(value):
        return str(value)

    @staticmethod
    def builtin_bool(value):
        if isinstance(value, str):
            return value.lower() not in ("", "0", "false", "none")
        return bool(value)

    @staticmethod
    def builtin_char(value):
        s = str(value)
        return s[0] if s else ""

    @staticmethod
    def builtin_type(value):
        return FoxangeType(value)

    @staticmethod
    def builtin_run_to_python(*args):
        if not args:
            return None
        import os
        import subprocess
        import sys
        target = args[0]
        extra = [str(a) for a in args[1:]]
        if isinstance(target, str) and os.path.isfile(target):
            result = subprocess.run([sys.executable, target] + extra)
            return result.returncode
        exec(compile(str(target), "<run_to_python>", "exec"), {"__name__": "__main__", "__builtins__": __builtins__})
        return None

class FoxangeType:

    def __init__(self, obj):
        if isinstance(obj, FoxangeType):
            self._type = obj._type
            self._is_all_error = obj._is_all_error
        elif obj == "AllError" or (isinstance(obj, str) and obj == "AllError"):
            self._type = None
            self._is_all_error = True
        elif isinstance(obj, type):
            self._type = obj
            self._is_all_error = False
        else:
            self._type = type(obj)
            self._is_all_error = False

    @property
    def name(self):
        if self._is_all_error:
            return "AllError"
        return self._type.__name__ if self._type else "AllError"

    def __eq__(self, other):
        if isinstance(other, FoxangeType):
            if self._is_all_error and other._is_all_error:
                return True
            return self._type is not None and self._type == other._type
        if isinstance(other, type):
            return not self._is_all_error and self._type == other
        if self._is_all_error and other == "AllError":
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        if self._is_all_error:
            return hash("AllError")
        return hash(self._type) if self._type else hash("AllError")

    def __repr__(self):
        return f"<type '{self.name}'>"

    def __str__(self):
        return self.name

    def __call__(self, *args):
        if self._is_all_error:
            raise TypeError("Cannot instantiate AllError")
        return self._type(*args)

class TypesNamespace:

    def _get_map(self):
        return {
            "int": int, "float": float, "str": str, "bool": bool,
            "char": str, "void": type(None), "any": object,
            "list": FoxangeList, "map": FoxangeMap, "set": FoxangeSet,
            "queue": FoxangeQueue, "stack": FoxangeStack, "pair": FoxangePair,
        }

    def __call__(self, name):
        cls = self._get_map().get(name)
        if cls is not None:
            return FoxangeType(cls)
        raise NameError(f"Unknown type: {name}")

class ErrorsNamespace:

    def _get_map(self):
        return {
            "AllError": "AllError",
            "Error": Exception,
            "Warning": Warning,
            "NameError": NameError,
            "TypeError": TypeError,
            "ValueError": ValueError,
            "RuntimeError": RuntimeError,
            "AttributeError": AttributeError,
            "ImportError": ImportError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "ZeroDivisionError": ZeroDivisionError,
            "FileNotFoundError": FileNotFoundError,
            "IOError": IOError,
            "OSError": OSError,
        }

    def __call__(self, name):
        entry = self._get_map().get(name)
        if entry is not None:
            return FoxangeType(entry)
        raise NameError(f"Unknown error type: {name}")
