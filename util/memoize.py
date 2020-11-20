"""
Cache results of a function, without needing custom code each time.
https://dbader.org/blog/python-memoization

See usage in Agent.py
"""
    
def memoize(func):
    cache = dict()

    def memoized_func(*args):
        if args in cache:
            return cache[args]
        result = func(*args)
        cache[args] = result
        return result

    return memoized_func
