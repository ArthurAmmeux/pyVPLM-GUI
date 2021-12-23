def terms_of_order_n(n, p):
    """
    Parameters
    ----------
    n Order
    p Dimension of the problem (number of input pi number in the pyVPLM case)

    Returns The number of terms specifically at order n (not counting the ones below n)
    -------

    """
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
    """
    Parameters
    ----------
    n Order
    p Dimension of the problem (number of input pi number in the pyVPLM case)

    Returns The total number of terms up the order n
    -------

    """
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
    """
    Parameters
    ----------
    n input

    Returns n!
    -------

    """
    if n == 0:
        return 1
    else:
        f = 1
        for i in range(1, n + 1):
            f *= i
        return f


def app(n, p):
    """
    Parameters
    ----------
    n Order
    p Dimension of the problem (number of input pi number in the pyVPLM case)

    Returns Approximates the solution for big n and p
    -------

    """
    #  c = -0.0027*p + 0.147
    return int(p**n/(fact(n) + 1))


# For testing purposes only
if __name__ == '__main__':
    print(coefficient_nb(3, 4))
