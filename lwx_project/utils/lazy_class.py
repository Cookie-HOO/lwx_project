import functools


class LazyDeco:
    """
    懒加载的装饰器
    class A:
        def __init__(self):
            self.result = []

        @LazyDeco("A").transformer
        def add(self, num1, num2):
            self.result.append(num1+num2)
            return self

        @LazyDeco("A").action
        def get_result(self):
            print(self.result)

    a = A()
    r = a.add(1,2)  # 此时代码不执行
    a.get_result()  # 此时执行
    """
    def __init__(self, *args, **kwargs):
        self.queue = []

    def transformer(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.queue.append((func, args, kwargs))
            return args[0]
        return wrapper

    def action(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            while self.queue:
                f, _args, _kwargs = self.queue.pop(0)
                f(*_args, **_kwargs)
            return func(*args, **kwargs)
        return wrapper


lazy = LazyDeco()
