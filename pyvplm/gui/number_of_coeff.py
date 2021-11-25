def terms_of_order_n(n, p):
    if n == 0:
        return 1
    if p == 1:
        return 1
    else:
        w = 0
        for i in range(0, n+1):
            w += terms_of_order_n(i, p-1)
        return w


def coefficient_nb(N, p, approx=False):
    w = 0
    if not approx:
        if N > 20 and p > 2:
            return 9999999999999
        else:
            for n in range(N + 1):
                w += terms_of_order_n(n, p)
    else:
        try:
            for n in range(N + 1):
                w += app(n, p)
        except Exception:
            w = 9999999999999
    return w


def fact(n):
    if n == 0:
        return 1
    else:
        f = 1
        for i in range(1, n + 1):
            f *= i
        return f


def app(n, p):
    c = -0.0027*p + 0.147
    return int(p**n/(fact(n) + 1))
