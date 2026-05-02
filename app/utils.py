import string

BASE62 = string.digits + string.ascii_letters  # 0-9, a-z, A-Z


def encode(num: int) -> str:
    return _to_base62(num)

def _to_base62(num: int) -> str:
    """Converts an integer to a Base62 string."""
    BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if num == 0:
        return BASE62[0]
        
    arr = []
    base = len(BASE62)
    while num:
        num, rem = divmod(num, base)
        arr.append(BASE62[rem])
        
    arr.reverse()
    return "".join(arr)