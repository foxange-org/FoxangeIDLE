import warnings

from .tokens import TokenType
from .ast_nodes import *
from .builtins import BuiltinEnvironment, FoxangeList, FoxangeMap, FoxangeSet, \
    FoxangeQueue, FoxangeStack, FoxangePair, FoxangeType, TypesNamespace, ErrorsNamespace
from .error_utils import FoxangeError

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass

class Environment:

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent
        self.hidden = set()
        self.private = set()
        self.imported_modules = {}
        self.return_type = None
        self.in_function = False
        self.in_loop = False

    def define(self, name, value, is_hidden=False, is_private=False):
        if is_private:
            self.private.add(name)
        elif is_hidden:
            self.hidden.add(name)
        self.vars[name] = value

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            val = self.parent.get(name)
            return val
        raise NameError(f"Name '{name}' is not defined")

    def assign(self, name, value):
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise NameError(f"Cannot assign to undefined name '{name}'")

    def has(self, name):
        if name in self.vars:
            return True
        if self.parent:
            return self.parent.has(name)
        return False

class FoxangeInterpreter:
    def __init__(self):
        self.global_env = Environment()
        self.current_env = self.global_env
        self.builtins = BuiltinEnvironment()
        self.current_file_dir = None
        self.current_file_path = None
        self._imported_modules_by_path = {}
        self._operator_kernels = self._build_operator_kernels()
        self._operator_overloads = {}
        self._error_types = {}
        self.annotations = []
        self._register_builtins()

    def _build_operator_kernels(self):
        k = {}

        def binary(fn):
            return lambda vals: fn(vals[0], vals[1])

        k[("+",)] = binary(lambda a, b: a + b)
        k[("-",)] = binary(lambda a, b: a - b)
        k[("*",)] = binary(lambda a, b: a * b)
        k[("/",)] = binary(lambda a, b: a / b)
        k[("//",)] = binary(lambda a, b: a // b)
        k[("%",)] = binary(lambda a, b: a % b)
        k[("**",)] = binary(lambda a, b: a ** b)
        k[("&",)] = binary(lambda a, b: int(a) & int(b))
        k[("|",)] = binary(lambda a, b: int(a) | int(b))
        k[("^",)] = binary(lambda a, b: int(a) ^ int(b))
        k[(">>",)] = binary(lambda a, b: int(a) >> int(b))
        k[("<<",)] = binary(lambda a, b: int(a) << int(b))
        k[("==",)] = binary(lambda a, b: a == b)
        k[("!=",)] = binary(lambda a, b: a != b)
        k[(">",)] = binary(lambda a, b: a > b)
        k[("<",)] = binary(lambda a, b: a < b)
        k[(">=",)] = binary(lambda a, b: a >= b)
        k[("<=",)] = binary(lambda a, b: a <= b)
        k[("is",)] = binary(lambda a, b: a is b)
        k[("in",)] = binary(lambda a, b: a in b)
        k[("and",)] = binary(lambda a, b: a and b)
        k[("or",)] = binary(lambda a, b: a or b)
        k[("mod",)] = binary(lambda a, b: a % b)
        k[("xor",)] = binary(lambda a, b: int(a) ^ int(b))
        k[("pow",)] = binary(lambda a, b: a ** b)
        k[("?", ":")] = lambda vals: vals[1] if vals[0] else vals[2]
        return k

    def _register_builtins(self):
        self.global_env.define("print", self.builtins.builtin_print)
        self.global_env.define("input", self.builtins.builtin_input)
        self.global_env.define("len", self.builtins.builtin_len)
        self.global_env.define("del", self.builtins.builtin_del)
        self.global_env.define("open", self.builtins.builtin_open)
        self.global_env.define("int", self.builtins.builtin_int)
        self.global_env.define("float", self.builtins.builtin_float)
        self.global_env.define("str", self.builtins.builtin_str)
        self.global_env.define("bool", self.builtins.builtin_bool)
        self.global_env.define("char", self.builtins.builtin_char)
        self.global_env.define("List", FoxangeList)
        self.global_env.define("Map", FoxangeMap)
        self.global_env.define("Set", FoxangeSet)
        self.global_env.define("Queue", FoxangeQueue)
        self.global_env.define("Stack", FoxangeStack)
        self.global_env.define("Pair", FoxangePair)
        self.global_env.define("types", TypesNamespace())
        self.global_env.define("errors", ErrorsNamespace())
        self.global_env.define("type", self.builtins.builtin_type)
        self.global_env.define("run_to_python", self.builtins.builtin_run_to_python)

    def interpret(self, node, env=None):
        if env is None:
            env = self.current_env

        if isinstance(node, Program):
            result = None
            for stmt in node.statements:
                result = self.eval(stmt, env)
            return result
        return self.eval(node, env)

    def eval(self, node, env):
        if node is None:
            return None

        line = node.line
        col = node.col
        if line == 0:
            line, col = self._get_child_position(node)

        try:
            method_name = f"_eval_{type(node).__name__}"
            method = getattr(self, method_name, None)
            if method:
                return method(node, env)
            raise NotImplementedError(f"No evaluator for {type(node).__name__}")
        except FoxangeError:
            raise
        except (ReturnException, BreakException, ContinueException):
            raise
        except SyntaxError as e:
            raise FoxangeError(
                str(e), exc_type="SyntaxError",
                file_path=self.current_file_path,
                line=line, col=col
            ) from e
        except Exception as e:
            raise FoxangeError(
                str(e), exc_type=type(e).__name__,
                file_path=self.current_file_path,
                line=line, col=col
            ) from e

    def _get_child_position(self, node):
        attrs = ('expr', 'target', 'value', 'condition', 'body',
                  'then_branch', 'else_branch', 'left', 'callee',
                  'object', 'obj', 'statements', 'elements', 'function',
                  'arguments', 'iterator', 'iterable', 'initializer',
                  'increment')
        for attr in attrs:
            child = getattr(node, attr, None)
            if child is None:
                continue
            if isinstance(child, list):
                for c in child:
                    if hasattr(c, 'line') and c.line > 0:
                        return c.line, c.col
                    l, co = self._get_child_position(c)
                    if l > 0:
                        return l, co
            elif hasattr(child, 'line') and child.line > 0:
                return child.line, child.col
            else:
                l, co = self._get_child_position(child)
                if l > 0:
                    return l, co
        return 0, 0

    def _eval_NumberLiteral(self, node, env):
        return node.value

    def _eval_StringLiteral(self, node, env):
        return node.value

    def _eval_CharLiteral(self, node, env):
        return node.value

    def _eval_BoolLiteral(self, node, env):
        return node.value

    def _eval_Identifier(self, node, env):
        try:
            return env.get(node.name)
        except NameError:
            self_obj = env.vars.get("self")
            if isinstance(self_obj, FoxangeInstance):
                try:
                    return self_obj.get(node.name)
                except AttributeError:
                    pass
            raise

    def _eval_OperatorFuncDef(self, node, env):
        key = tuple(node.op_tokens)
        name = "<operator %s>" % " ".join(key)
        func_node = FuncDef(
            name=name,
            params=node.params,
            return_type=node.return_type,
            body=node.body,
            varargs=node.varargs,
            kwargs=node.kwargs,
            is_hidden=node.is_hidden,
            is_private=node.is_private,
        )
        closure = self.global_env if node.is_inline else env
        func = FoxangeFunction(func_node, closure)
        overload = self._operator_overloads.get(key)
        if overload is None:
            overload = FoxangeOverload(name)
            self._operator_overloads[key] = overload
        overload.add(func)
        return func

    def _eval_OperatorDef(self, node, env):
        return None

    def _eval_OperatorExpr(self, node, env):
        vals = [self.eval(op, env) for op in node.operands]
        key = tuple(node.op_tokens)
        if isinstance(vals[0], FoxangeInstance):
            opm = getattr(vals[0].cls, "operator_methods", {}).get(key)
            if opm is not None:
                bound = FoxangeBoundMethod(opm, vals[0])
                return bound.call(self, vals[1:], {})
        overload = self._operator_overloads.get(key)
        if overload is not None and overload._select(vals, {}) is not None:
            return overload.call(self, vals)
        kernel = self._operator_kernels.get(key)
        if kernel is None:
            raise RuntimeError(
                f"Operator '{' '.join(key)}' has no evaluation kernel; "
                f"available kernels: "
                f"{', '.join(' '.join(kk) for kk in sorted(self._operator_kernels))}"
            )
        return kernel(vals)

    def _eval_UnaryOp(self, node, env):
        val = self.eval(node.operand, env)
        if node.op == "-":
            return -val
        elif node.op == "~":
            return ~int(val)
        elif node.op == "not":
            return not val
        warnings.warn(f"Unknown unary operator: {node.op}")
        raise RuntimeError(f"Unknown unary operator: {node.op}")

    def _eval_BinaryOp(self, node, env):
        if node.op in ("and", "&&"):
            left = self.eval(node.left, env)
            if not left:
                return left
            return self.eval(node.right, env)
        if node.op in ("or", "||"):
            left = self.eval(node.left, env)
            if left:
                return left
            return self.eval(node.right, env)

        left = self.eval(node.left, env)
        right = self.eval(node.right, env)

        op = node.op
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if isinstance(left, int) and isinstance(right, int):
                return left / right
            return left / right
        if op == "//":
            return left // right
        if op == "%":
            return left % right
        if op == "**":
            return left ** right

        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
        if op == "is":
            return left is right
        if op == "in":
            return left in right

        if op == "&":
            return int(left) & int(right)
        if op == "|":
            return int(left) | int(right)
        if op == "^":
            return int(left) ^ int(right)
        if op == ">>":
            return int(left) >> int(right)
        if op == "<<":
            return int(left) << int(right)

        warnings.warn(f"Unknown binary operator: {op}")
        raise RuntimeError(f"Unknown binary operator: {op}")

    def _eval_TernaryExpr(self, node, env):
        if node.style == "c":
            cond = self.eval(node.condition, env)
            return self.eval(node.true_expr if cond else node.false_expr, env)
        else:
            cond = self.eval(node.condition, env)
            return self.eval(node.true_expr if cond else node.false_expr, env)

    def _eval_Assign(self, node, env):
        value = self.eval(node.value, env)

        if node.op != "=":
            target_val = self._get_target_value(node.target, env)
            op_char = node.op.rstrip("=")
            if op_char == "+":
                value = target_val + value
            elif op_char == "-":
                value = target_val - value
            elif op_char == "*":
                value = target_val * value
            elif op_char == "/":
                value = target_val / value
            elif op_char == "//":
                value = target_val // value
            elif op_char == "%":
                value = target_val % value
            elif op_char == "**":
                value = target_val ** value
            elif op_char == "&":
                value = int(target_val) & int(value)
            elif op_char == "|":
                value = int(target_val) | int(value)
            elif op_char == "^":
                value = int(target_val) ^ int(value)
            elif op_char == ">>":
                value = int(target_val) >> int(value)
            elif op_char == "<<":
                value = int(target_val) << int(value)
            elif op_char == "~":
                value = ~int(value)

        self._assign_target(node.target, value, env)
        return value

    def _get_target_value(self, target, env):
        if isinstance(target, Identifier):
            return env.get(target.name)
        elif isinstance(target, IndexAccess):
            obj = self.eval(target.obj, env)
            idx = self.eval(target.index, env)
            return obj[idx]
        elif isinstance(target, MemberAccess):
            obj = self.eval(target.obj, env)
            return getattr(obj, target.member)
        return self.eval(target, env)

    def _assign_target(self, target, value, env):
        if isinstance(target, Identifier):
            if env.has(target.name):
                env.assign(target.name, value)
            else:
                env.define(target.name, value)
        elif isinstance(target, IndexAccess):
            obj = self.eval(target.obj, env)
            idx = self.eval(target.index, env)
            obj[idx] = value
        elif isinstance(target, MemberAccess):
            obj = self.eval(target.obj, env)
            setattr(obj, target.member, value)
        else:
            raise RuntimeError(f"Cannot assign to {type(target).__name__}")

    def _default_for_type(self, type_name, env):
        if not type_name:
            return None
        t = type_name.strip()
        if t.startswith("["):
            return FoxangeList([])
        main = t.split("<")[0].strip()
        if main == "list":
            return FoxangeList([])
        if main == "map":
            return FoxangeMap({})
        if main == "set":
            return FoxangeSet([])
        if main == "queue":
            return FoxangeQueue([])
        if main == "stack":
            return FoxangeStack([])
        if main == "pair":
            return FoxangePair(None, None)
        if main == "int":
            return 0
        if main == "float":
            return 0.0
        if main in ("string", "str"):
            return ""
        if main == "bool":
            return False
        if main in ("any", "var", "void"):
            return None
        try:
            target = env.get(main)
        except NameError:
            return None
        if isinstance(target, (FoxangeClass, FoxangeStruct)):
            return target.instantiate(self, [])
        return None

    def _eval_VarDecl(self, node, env):
        value = self.eval(node.value, env) if node.value else self._default_for_type(node.type_name, env)
        is_hidden = node.name.startswith("__")
        is_private = not is_hidden and node.name.startswith("_")
        self_obj = env.vars.get("self")
        if isinstance(self_obj, FoxangeInstance) and node.name in self_obj._init_members:
            self_obj.set(node.name, value)
        env.define(node.name, value, is_hidden, is_private)
        return value

    def _eval_ExpressionStmt(self, node, env):
        return self.eval(node.expr, env)

    def _eval_CompoundStatement(self, node, env):
        result = None
        for stmt in node.statements:
            result = self.eval(stmt, env)
        return result

    def _eval_IfStmt(self, node, env):
        cond = self.eval(node.condition, env)
        if cond:
            return self.eval(node.then_branch, env)
        for elif_cond, elif_body in node.elif_branches:
            if self.eval(elif_cond, env):
                return self.eval(elif_body, env)
        if node.else_branch:
            return self.eval(node.else_branch, env)
        return None

    def _eval_ForLoop(self, node, env):
        iterable = self.eval(node.iterable, env)
        result = None
        old_loop = env.in_loop
        env.in_loop = True
        for item in iterable:
            try:
                if isinstance(node.var, Identifier):
                    env.define(node.var.name, item)
                result = self.eval(node.body, env)
            except BreakException:
                break
            except ContinueException:
                continue
        env.in_loop = old_loop
        return result

    def _eval_WhileLoop(self, node, env):
        result = None
        old_loop = env.in_loop
        env.in_loop = True
        while self.eval(node.condition, env):
            try:
                result = self.eval(node.body, env)
            except BreakException:
                break
            except ContinueException:
                continue
        env.in_loop = old_loop
        return result

    def _eval_WithStmt(self, node, env):
        val = self.eval(node.expr, env)
        if node.alias:
            env.define(node.alias, val)
        if hasattr(val, "__enter__"):
            val.__enter__()
        if isinstance(val, FoxangeInstance) and "__input__" in val.cls.methods:
            self._call_instance_method(val, "__input__", [])
        result = self.eval(node.body, env)
        if hasattr(val, "__exit__"):
            val.__exit__(None, None, None)
        if isinstance(val, FoxangeInstance) and "__output__" in val.cls.methods:
            self._call_instance_method(val, "__output__", [])
        return result

    def _call_instance_method(self, instance, method_name, args):
        method = instance.cls.methods[method_name]
        bound = FoxangeBoundMethod(method, instance)
        bound.call(self, args)

    def _eval_TryStmt(self, node, env):
        ERROR_TYPE_MAP = {
            "AllError": None,
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
        try:
            return self.eval(node.try_body, env)
        except (ReturnException, BreakException, ContinueException):
            raise
        except Exception as exc:
            for clause in node.have_clauses:
                error_types = clause.error_types or []
                alias = clause.alias
                if not error_types or "AllError" in error_types:
                    if alias:
                        env.define(alias, str(exc))
                    return self.eval(clause.body, env)
                for error_name in error_types:
                    if self._matches_error(exc, error_name, ERROR_TYPE_MAP):
                        if alias:
                            env.define(alias, str(exc))
                        return self.eval(clause.body, env)
            raise

    def _matches_error(self, exc, error_name, error_type_map):
        if error_name == "AllError":
            return True
        if isinstance(exc, FoxangeError) and exc.exc_type == error_name:
            return True
        target_cls = error_type_map.get(error_name)
        if error_name == "Error":
            matched = isinstance(exc, Exception) and not isinstance(exc, Warning)
            if isinstance(exc, FoxangeError):
                matched = matched and exc.exc_type != "Warning" \
                    and self._error_types.get(exc.exc_type) != "warning"
            return matched
        if error_name == "Warning":
            if isinstance(exc, Warning):
                return True
            if isinstance(exc, FoxangeError):
                return exc.exc_type == "Warning" \
                    or self._error_types.get(exc.exc_type) == "warning"
            return False
        if target_cls is not None:
            if isinstance(exc, target_cls):
                return True
            if isinstance(exc, FoxangeError):
                if exc.exc_type == error_name:
                    return True
                if exc.__cause__ is not None and isinstance(exc.__cause__, target_cls):
                    return True
        return False

    def _eval_RaiseStmt(self, node, env):
        expr = node.expr
        if expr is None:
            raise FoxangeError(
                "raise requires an exception expression",
                exc_type="RuntimeError",
                file_path=self.current_file_path,
                line=node.line, col=node.col,
            )
        if isinstance(expr, Call) and isinstance(expr.callee, Identifier):
            name = expr.callee.name
            if name in self._error_types:
                args = [self.eval(a, env) for a in expr.arguments]
                msg = args[0] if args else ""
                raise FoxangeError(
                    msg, exc_type=name,
                    file_path=self.current_file_path,
                    line=node.line, col=node.col,
                )
        value = self.eval(expr, env)
        if isinstance(value, BaseException):
            raise value
        if isinstance(value, FoxangeClass):
            if value.name in self._error_types:
                raise FoxangeError(
                    "", exc_type=value.name,
                    file_path=self.current_file_path,
                    line=node.line, col=node.col,
                )
            raise FoxangeError(
                f"Cannot raise class '{value.name}'",
                exc_type="TypeError",
                file_path=self.current_file_path,
                line=node.line, col=node.col,
            )
        if isinstance(value, FoxangeInstance):
            if value.cls.name in self._error_types:
                raise FoxangeError(
                    "", exc_type=value.cls.name,
                    file_path=self.current_file_path,
                    line=node.line, col=node.col,
                )
            raise FoxangeError(
                f"Cannot raise instance of '{value.cls.name}'",
                exc_type="TypeError",
                file_path=self.current_file_path,
                line=node.line, col=node.col,
            )
        if isinstance(value, FoxangeType):
            raise FoxangeError(
                "", exc_type=value.name,
                file_path=self.current_file_path,
                line=node.line, col=node.col,
            )
        raise FoxangeError(
            f"Cannot raise '{value}'", exc_type="TypeError",
            file_path=self.current_file_path,
            line=node.line, col=node.col,
        )

    def _eval_FuncDef(self, node, env):
        func = FoxangeFunction(node, env)
        if node.is_inline:
            env = self.global_env
            env.define(node.name, func, node.is_hidden, node.is_private)
            return func
        existing = env.vars.get(node.name)
        if isinstance(existing, FoxangeOverload):
            existing.add(func)
        elif isinstance(existing, FoxangeFunction):
            if FoxangeOverload._signature(existing.node) == FoxangeOverload._signature(node):
                env.define(node.name, func, node.is_hidden, node.is_private)
            else:
                overload = FoxangeOverload(node.name, [existing, func])
                env.define(node.name, overload, node.is_hidden, node.is_private)
        else:
            env.define(node.name, func, node.is_hidden, node.is_private)
        return func

    def _eval_LambdaExpr(self, node, env):
        func_node = FuncDef(
            name="<lambda>",
            params=node.params,
            return_type=None,
            body=CompoundStatement([ReturnStmt(node.body)]),
            varargs=node.varargs,
            kwargs=node.kwargs,
            is_hidden=False,
            is_private=False
        )
        return FoxangeFunction(func_node, env)

    def _eval_Call(self, node, env):
        callee = self.eval(node.callee, env)

        pos_args = [self.eval(a, env) for a in node.arguments]

        if node.star_arg is not None:
            star_val = self.eval(node.star_arg, env)
            if isinstance(star_val, FoxangeList):
                pos_args.extend(star_val._data)
            elif hasattr(star_val, '__iter__') and not isinstance(star_val, (str, FoxangeMap)):
                pos_args.extend(list(star_val))
            else:
                raise TypeError(f"* argument must be iterable, not {type(star_val).__name__}")

        kw_args = {}
        if node.star_star_arg is not None:
            ss_val = self.eval(node.star_star_arg, env)
            if isinstance(ss_val, FoxangeMap):
                kw_args.update(ss_val._data)
            elif isinstance(ss_val, dict):
                kw_args.update(ss_val)
            else:
                raise TypeError(f"** argument must be a mapping, not {type(ss_val).__name__}")

        if isinstance(callee, FoxangeOverload):
            return callee.call(self, pos_args, kw_args if kw_args else None)
        if isinstance(callee, FoxangeFunction):
            return callee.call(self, pos_args, kw_args if kw_args else None)
        elif isinstance(callee, FoxangeBoundMethod):
            return callee.call(self, pos_args, kw_args if kw_args else None)
        elif isinstance(callee, FoxangeClass):
            return callee.instantiate(self, pos_args)
        elif isinstance(callee, FoxangeStruct):
            return callee.instantiate(self, pos_args)
        elif callable(callee):
            if kw_args:
                return callee(*pos_args, **kw_args)
            return callee(*pos_args)
        raise NameError(f"'{callee}' is not callable")

    def _eval_MemberAccess(self, node, env):
        obj = self.eval(node.obj, env)
        member = node.member
        if isinstance(obj, FoxangeInstance):
            return obj.get(member)
        if isinstance(obj, (FoxangeList, FoxangeMap, FoxangeSet,
                            FoxangeQueue, FoxangeStack, FoxangePair)):
            if hasattr(obj, member):
                return getattr(obj, member)
        if hasattr(obj, member):
            return getattr(obj, member)
        raise AttributeError(f"'{type(obj).__name__}' has no attribute '{member}'")

    def _eval_ReturnStmt(self, node, env):
        value = self.eval(node.value, env) if node.value else None
        raise ReturnException(value)

    def _eval_BreakStmt(self, node, env):
        raise BreakException()

    def _eval_ContinueStmt(self, node, env):
        raise ContinueException()

    def _eval_DeleteStmt(self, node, env):
        target = node.target
        if isinstance(target, Identifier):
            if target.name in env.vars:
                del env.vars[target.name]
        elif isinstance(target, IndexAccess):
            obj = self.eval(target.obj, env)
            idx = self.eval(target.index, env)
            del obj[idx]
        return None

    def _eval_WalrusExpr(self, node, env):
        value = self.eval(node.value, env)
        self._assign_target(node.target, value, env)
        return value

    def _eval_PrintStmt(self, node, env):
        values = [self._to_print_str(self.eval(v, env)) for v in node.values]
        space = node.space
        end = node.end
        output = space.join(values) + end
        if node.file:
            with open(node.file, "a", encoding="utf-8") as f:
                f.write(output)
        else:
            print(output, end="")
        return None

    def _to_print_str(self, val):
        if val is None:
            return "None"
        if isinstance(val, bool):
            return "True" if val else "False"
        return str(val)

    def _eval_InputStmt(self, node, env):
        from .builtins import _input_func
        prompt_val = self.eval(node.prompt, env) if node.prompt else ""
        if prompt_val:
            return _input_func(str(prompt_val))
        return _input_func()

    def _eval_ListLiteral(self, node, env):
        elements = [self.eval(e, env) for e in node.elements]
        return FoxangeList(elements)

    def _eval_MapLiteral(self, node, env):
        entries = {}
        for k, v in node.entries:
            key = self.eval(k, env)
            val = self.eval(v, env)
            entries[key] = val
        return FoxangeMap(entries)

    def _eval_SetLiteral(self, node, env):
        elements = [self.eval(e, env) for e in node.elements]
        return FoxangeSet(elements)

    def _eval_QueueLiteral(self, node, env):
        elements = [self.eval(e, env) for e in node.elements]
        return FoxangeQueue(elements)

    def _eval_PairLiteral(self, node, env):
        first = self.eval(node.first, env)
        second = self.eval(node.second, env)
        return FoxangePair(first, second)

    def _eval_IndexAccess(self, node, env):
        obj = self.eval(node.obj, env)
        index = self.eval(node.index, env)
        if isinstance(obj, FoxangeInstance):
            opm = getattr(obj.cls, "operator_methods", {}).get(("[", "]"))
            if opm is not None:
                bound = FoxangeBoundMethod(opm, obj)
                return bound.call(self, [index], {})
        return obj[index]

    def _eval_ClassDef(self, node, env):
        cls = FoxangeClass(node.name, node.type_params, node.bases, node.body, env)
        if node.is_inline:
            env = self.global_env
        env.define(node.name, cls, node.is_hidden, node.is_private)
        if "Error" in node.bases or "Warning" in node.bases:
            kind = "warning" if "Warning" in node.bases else "error"
            self._error_types[node.name] = kind
        return cls

    def _eval_StructDef(self, node, env):
        struct = FoxangeStruct(node.name, node.body, env)
        if node.is_inline:
            env = self.global_env
        env.define(node.name, struct, node.is_hidden, node.is_private)
        return struct

    def _eval_ImportStmt(self, node, env):
        module_name = node.module
        if module_name in env.imported_modules:
            mod = env.imported_modules[module_name]
        else:
            mod = self._load_module(module_name)
            env.imported_modules[module_name] = mod
        alias = node.alias or module_name
        env.define(alias, mod)
        if isinstance(mod, FoxangeModule):
            for name, val in mod._env.vars.items():
                if isinstance(val, (FoxangeClass, FoxangeStruct)) and not name.startswith("_"):
                    env.define(name, val)
        return mod

    def _eval_FromImportStmt(self, node, env):
        module_name = node.module
        mod = self._load_module(module_name)
        for name, alias in node.names:
            if name == "*":
                for attr_name in dir(mod):
                    if not attr_name.startswith("_"):
                        env.define(attr_name, getattr(mod, attr_name))
            else:
                val = getattr(mod, name)
                env.define(alias or name, val)
        return mod

    def _load_module(self, module_name):
        import importlib
        import sys
        import os
        import json

        search_paths = []

        if self.current_file_dir:
            search_paths.append(os.path.join(self.current_file_dir, module_name + ".fx"))

        repo_json = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "lib", "built_library", "repository_address.json"
        )
        if os.path.exists(repo_json):
            try:
                with open(repo_json, "r", encoding="utf-8-sig") as f:
                    repo = json.load(f)
                if module_name in repo:
                    repo_path = repo[module_name]
                    if os.path.isabs(repo_path):
                        search_paths.append(repo_path)
                    else:
                        base_dir = self.current_file_dir or os.path.dirname(os.path.abspath(__file__))
                        search_paths.append(os.path.join(base_dir, repo_path))
            except (json.JSONDecodeError, IOError):
                pass

        search_paths.append(os.path.join(os.getcwd(), module_name + ".fx"))
        search_paths.append(module_name + ".fx")

        for path in search_paths:
            if os.path.exists(path):
                abs_path = os.path.normcase(os.path.abspath(path))
                if abs_path in self._imported_modules_by_path:
                    mod = self._imported_modules_by_path[abs_path]
                    if mod is None:
                        return FoxangeModule(module_name, Environment(self.global_env))
                    return mod
                self._imported_modules_by_path[abs_path] = None
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        source = f.read()
                    pp = Preprocessor()
                    source = pp.process(source)
                    from .lexer import Lexer
                    from .parser import Parser
                    lexer = Lexer(source)
                    tokens = lexer.tokenize()
                    tokens = pp.apply_force_annotations(tokens)
                    parser = Parser(tokens, source=source)
                    ast = parser.parse()
                    mod_env = Environment(self.global_env)

                    old_dir = self.current_file_dir
                    old_path = self.current_file_path
                    self.current_file_dir = os.path.dirname(abs_path)
                    self.current_file_path = abs_path
                    try:
                        self.interpret(ast, mod_env)
                    finally:
                        self.current_file_dir = old_dir
                        self.current_file_path = old_path
                except Exception:
                    del self._imported_modules_by_path[abs_path]
                    raise

                mod = FoxangeModule(module_name, mod_env)
                self._imported_modules_by_path[abs_path] = mod
                return mod

        try:
            return importlib.import_module(module_name)
        except ImportError:
            pass
        raise ImportError(f"Cannot import module '{module_name}'")

class FoxangeFunction:
    def __init__(self, node, closure):
        self.node = node
        self.closure = closure
        self.name = node.name

    def call(self, interpreter, args, kwargs=None, implicit_self=None):
        func_env = Environment(self.closure)
        if implicit_self is not None:
            func_env.define("self", implicit_self)

        params = self.node.params
        varargs = self.node.varargs
        var_kwargs = self.node.kwargs

        total_params = len(params)

        bound_params = set()
        kw_consumed = set()
        remaining_kw = {}

        if kwargs:
            param_index = {pname: i for i, (pname, ptype, pdefault) in enumerate(params)}

            for k, v in kwargs.items():
                if k in param_index:
                    idx = param_index[k]
                    func_env.define(k, v)
                    bound_params.add(idx)
                    kw_consumed.add(k)
                else:
                    remaining_kw[k] = v

        if varargs:
            varargs_extra = []
            for i, val in enumerate(args):
                if i < total_params:
                    if i not in bound_params:
                        pass
                else:
                    varargs_extra.append(val)
            func_env.define(varargs, FoxangeList(varargs_extra))

        if var_kwargs:
            kw_dict = dict(remaining_kw)
            func_env.define(var_kwargs, FoxangeMap(kw_dict))
        elif remaining_kw:
            first_unknown = next(iter(remaining_kw))
            raise TypeError(
                f"Function '{self.name}' got unexpected keyword argument '{first_unknown}'"
            )

        unbound = [(i, pname, ptype, pdefault)
                   for i, (pname, ptype, pdefault) in enumerate(params)
                   if i not in bound_params]

        norm_args = [val for i, val in enumerate(args)
                     if i < total_params and i not in bound_params]

        if len(norm_args) == len(unbound):
            for idx, (i, pname, ptype, pdefault) in enumerate(unbound):
                func_env.define(pname, norm_args[idx])
        else:
            required = [(i, pname, ptype, pdefault) for i, pname, ptype, pdefault in unbound if pdefault is None]
            optional = [(i, pname, ptype, pdefault) for i, pname, ptype, pdefault in unbound if pdefault is not None]

            n_required = len(required)
            n_optional = len(optional)

            if n_required > len(norm_args):
                missing = required[len(norm_args)][1]
                raise TypeError(
                    f"Function '{self.name}' missing required argument: {missing}"
                )

            req_args = norm_args[-n_required:] if n_required > 0 else []
            remaining = norm_args[:-n_required] if n_required > 0 else norm_args

            for idx, (i, pname, ptype, pdefault) in enumerate(required):
                func_env.define(pname, req_args[idx])

            for idx, (i, pname, ptype, pdefault) in enumerate(optional):
                if idx < len(remaining):
                    func_env.define(pname, remaining[idx])
                else:
                    func_env.define(pname, interpreter.eval(pdefault, self.closure))

            if len(remaining) > n_optional:
                raise TypeError(
                    f"Function '{self.name}' takes at most {len(unbound)} positional arguments but {len(norm_args)} were given"
                )

        old_env = interpreter.current_env
        interpreter.current_env = func_env
        func_env.in_function = True

        try:
            result = interpreter.eval(self.node.body, func_env)
            return result
        except ReturnException as ret:
            return ret.value
        finally:
            interpreter.current_env = old_env

    def __repr__(self):
        return f"<function {self.name}>"


def _type_of(value):
    """返回 Foxange 层面的实参类型名，用于重载匹配。"""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, FoxangeList):
        return "list"
    if isinstance(value, FoxangeMap):
        return "map"
    if isinstance(value, FoxangeSet):
        return "set"
    if isinstance(value, FoxangeQueue):
        return "queue"
    if isinstance(value, FoxangeStack):
        return "stack"
    if isinstance(value, FoxangePair):
        return "pair"
    if value is None:
        return "void"
    return "any"


def _ptype_matches(ptype, value):
    """形参类型标注是否接受该实参。ptype 如 int / float / list<int> / [str] / any。"""
    if ptype is None:
        return True
    p = ptype.strip()
    main = p.split("<")[0].strip().strip("[]")
    if main in ("any", "var"):
        return True
    if main == "void":
        return _type_of(value) == "void"
    if main in ("func", "function", "callable"):
        return callable(value)
    return main == _type_of(value)


class FoxangeOverload:
    """同名函数重载集：保存多个签名不同的 FoxangeFunction，调用时按实参类型分发。"""

    def __init__(self, name, funcs=None):
        self.name = name
        self.funcs = funcs if funcs is not None else []

    @staticmethod
    def _signature(node):
        return (tuple(ptype or "" for _, ptype, _ in node.params),
                bool(node.varargs), bool(node.kwargs))

    def add(self, func):
        sig = self._signature(func.node)
        for i, f in enumerate(self.funcs):
            if self._signature(f.node) == sig:
                self.funcs[i] = func   # 同签名后定义覆盖前定义
                return
        self.funcs.append(func)

    def _sig_desc(self, func):
        params = func.node.params
        return ", ".join((ptype or "any") for _, ptype, _ in params)

    @staticmethod
    def _match_score(node, args, kwargs):
        params = node.params
        total_params = len(params)
        varargs = node.varargs
        var_kwargs = node.kwargs
        param_names = {pname for pname, _, _ in params}

        for k in kwargs:
            if k not in param_names and not var_kwargs:
                return None

        n_args = len(args)
        required = sum(1 for _, _, pd in params if pd is None)
        if n_args + len(kwargs) < required:
            return None
        if n_args > total_params and not varargs:
            return None

        score = 0
        for i, val in enumerate(args):
            if i >= total_params:
                if varargs:
                    continue
                return None
            pname, ptype, _ = params[i]
            if ptype is None:
                continue
            if not _ptype_matches(ptype, val):
                return None
            score += 1

        for k, v in kwargs.items():
            if k in param_names:
                for pname, ptype, _ in params:
                    if pname == k:
                        if ptype is not None:
                            if not _ptype_matches(ptype, v):
                                return None
                            score += 1
                        break
        return score

    def _select(self, args, kwargs):
        best = None
        best_score = -1
        for func in self.funcs:
            score = self._match_score(func.node, args, kwargs)
            if score is not None and score > best_score:
                best_score = score
                best = func
        return best

    def call(self, interpreter, args, kwargs=None):
        kwargs = kwargs or {}
        func = self._select(args, kwargs)
        if func is None:
            sigs = " / ".join(self._sig_desc(f) for f in self.funcs)
            arg_types = ", ".join(_type_of(a) for a in args)
            raise TypeError(
                f"No overload for function '{self.name}' matches arguments ({arg_types}). "
                f"Available signatures: ({sigs})"
            )
        return func.call(interpreter, args, kwargs if kwargs else None)

    def __repr__(self):
        return f"<overload {self.name} ({len(self.funcs)} signatures)>"


class FoxangeStruct:
    def __init__(self, name, body, env):
        self.name = name
        self.body = body
        self.env = env
        self.fields = {}
        self.methods = {}
        self._init_members()

    def _init_members(self):
        for stmt in self.body:
            if isinstance(stmt, VarDecl):
                self.fields[stmt.name] = stmt
            elif isinstance(stmt, FuncDef):
                self.methods[stmt.name] = FoxangeFunction(stmt, self.env)

    def instantiate(self, interpreter, args):
        instance = FoxangeInstance(self)
        for fname, fstmt in self.fields.items():
            value = interpreter.eval(fstmt.value, self.env) if fstmt.value else None
            instance.set(fname, value)
        init_method = None
        if "__init__" in self.methods:
            init_method = self.methods["__init__"]
        elif "__main__" in self.methods:
            init_method = self.methods["__main__"]
        if init_method is not None:
            init_args = [instance] + args
            func_env = Environment(init_method.closure)
            params = init_method.node.params
            for i, (pname, ptype, pdefault) in enumerate(params):
                if i < len(init_args):
                    func_env.define(pname, init_args[i])
                elif pdefault:
                    func_env.define(pname, interpreter.eval(pdefault, init_method.closure))
            old_env = interpreter.current_env
            interpreter.current_env = func_env
            try:
                interpreter.eval(init_method.node.body, func_env)
            except ReturnException:
                pass
            finally:
                interpreter.current_env = old_env
        return instance

    def __call__(self, *args):
        return FoxangeInstance(self)

    def __repr__(self):
        return f"<struct {self.name}>"

class FoxangeClass:
    def __init__(self, name, type_params, bases, body, env):
        self.name = name
        self.type_params = type_params
        self.bases = bases
        self.body = body
        self.env = env
        self.methods = {}
        self._init_methods()

    def _init_methods(self):
        self.fields = {}
        self.operator_methods = {}
        for stmt in self.body:
            if isinstance(stmt, VarDecl):
                self.fields[stmt.name] = stmt
            elif isinstance(stmt, FuncDef):
                func = FoxangeFunction(stmt, self.env)
                self.methods[stmt.name] = func
            elif isinstance(stmt, OperatorFuncDef):
                key = tuple(stmt.op_tokens)
                name = "<operator %s>" % " ".join(key)
                func_node = FuncDef(name=name, params=stmt.params, return_type=stmt.return_type, body=stmt.body, varargs=stmt.varargs, kwargs=stmt.kwargs, is_hidden=stmt.is_hidden, is_private=stmt.is_private)
                self.operator_methods[key] = FoxangeFunction(func_node, self.env)

    def instantiate(self, interpreter, args):
        instance = FoxangeInstance(self)
        for fname, fstmt in self.fields.items():
            value = interpreter.eval(fstmt.value, self.env) if fstmt.value else interpreter._default_for_type(fstmt.type_name, self.env)
            instance.set(fname, value)
        init_method = None
        if "__init__" in self.methods:
            init_method = self.methods["__init__"]
        elif "__main__" in self.methods:
            init_method = self.methods["__main__"]
        if init_method is not None:
            if isinstance(init_method.node.body, CompoundStatement):
                for stmt in init_method.node.body.statements:
                    if isinstance(stmt, VarDecl) and stmt.type_name:
                        instance._init_members.add(stmt.name)
                        if stmt.value is None:
                            instance.set(stmt.name, interpreter._default_for_type(stmt.type_name, self.env))
            init_args = [instance] + args
            func_env = Environment(init_method.closure)
            params = init_method.node.params
            for i, (pname, ptype, pdefault) in enumerate(params):
                if i < len(init_args):
                    func_env.define(pname, init_args[i])
                elif pdefault:
                    func_env.define(pname, interpreter.eval(pdefault, init_method.closure))
            old_env = interpreter.current_env
            interpreter.current_env = func_env
            try:
                interpreter.eval(init_method.node.body, func_env)
            except ReturnException:
                pass
            finally:
                interpreter.current_env = old_env
        return instance

    def __call__(self, *args):
        return FoxangeInstance(self)

    def __repr__(self):
        if self.type_params:
            params_str = ", ".join(self.type_params)
            return f"<class {self.name}<{params_str}>>"
        return f"<class {self.name}>"

class FoxangeInstance:
    def __init__(self, cls):
        object.__setattr__(self, 'cls', cls)
        object.__setattr__(self, 'fields', {})
        object.__setattr__(self, '_init_members', set())

    def __setattr__(self, name, value):
        self.fields[name] = value

    def get(self, name):
        if name in self.fields:
            return self.fields[name]
        if name in self.cls.methods:
            method = self.cls.methods[name]
            return FoxangeBoundMethod(method, self)
        raise AttributeError(f"'{self.cls.name}' instance has no attribute '{name}'")

    def set(self, name, value):
        self.fields[name] = value

    def __repr__(self):
        return f"<{self.cls.name} instance>"

class FoxangeBoundMethod:
    def __init__(self, func, instance):
        self.func = func
        self.instance = instance

    def call(self, interpreter, args, kwargs=None):
        params = self.func.node.params
        if params and params[0][0] == "self":
            return self.func.call(interpreter, [self.instance] + args, kwargs)
        return self.func.call(interpreter, args, kwargs, implicit_self=self.instance)

    def __repr__(self):
        return f"<bound method {self.func.name}>"

class FoxangeModule:
    def __init__(self, name, env):
        self.name = name
        self._env = env

    def __getattr__(self, name):
        if name in self._env.vars:
            return self._env.vars[name]
        raise AttributeError(f"Module '{self.name}' has no attribute '{name}'")

from .preprocessor import Preprocessor

_repl_preprocessor = Preprocessor()

def run_file(filepath):
    import os
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    pp = Preprocessor()
    source = pp.process(source)
    interpreter = FoxangeInterpreter()
    interpreter.current_file_dir = os.path.dirname(os.path.abspath(filepath))
    interpreter.current_file_path = os.path.abspath(filepath)
    interpreter.annotations = list(pp.annotations)
    from .lexer import Lexer
    from .parser import Parser
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    tokens = pp.apply_force_annotations(tokens)
    parser = Parser(tokens)
    ast = parser.parse()
    return interpreter.interpret(ast)

def run(source, file_dir=None):
    from .lexer import Lexer
    from .parser import Parser

    processed = _repl_preprocessor.process(source)
    lexer = Lexer(processed)
    tokens = lexer.tokenize()
    tokens = _repl_preprocessor.apply_force_annotations(tokens)
    parser = Parser(tokens)
    ast = parser.parse()
    interpreter = FoxangeInterpreter()
    interpreter.annotations = list(_repl_preprocessor.annotations)
    if file_dir:
        interpreter.current_file_dir = file_dir
    return interpreter.interpret(ast)
