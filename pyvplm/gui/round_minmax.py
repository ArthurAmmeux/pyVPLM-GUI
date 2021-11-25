from math import floor, ceil


def round_min(tr_min):
    tr_min = round(tr_min, 4)
    p = 0
    if tr_min == 0:
        return 0
    elif 100 <= abs(tr_min) < 1000:
        return floor(tr_min)
    elif abs(tr_min) >= 1000:
        while abs(tr_min) >= 1000:
            tr_min = tr_min/10
            p += 1
        return floor(tr_min)*10**p
    elif abs(tr_min) < 100:
        while abs(tr_min) < 100:
            tr_min = tr_min*10
            p -= 1
        return floor(tr_min)*10**p


def round_max(tr_max):
    tr_max = round(tr_max, 4)
    p = 0
    if tr_max == 0:
        return 0
    elif 100 <= abs(tr_max) < 1000:
        return ceil(tr_max)
    elif abs(tr_max) >= 1000:
        while abs(tr_max) >= 1000:
            tr_max = tr_max/10
            p += 1
        return ceil(tr_max)*10**p
    elif abs(tr_max) < 100:
        while abs(tr_max) < 100:
            tr_max = tr_max*10
            p -= 1
        return ceil(tr_max)*10**p


if __name__ == '__main__':
    print("Round min:")
    print(round_min(184.56))
    print(round_min(18557.36))
    print(round_min(1.8653))
    print("expected: 184, 18500, 1.86")
    print("Round max:")
    print(round_max(184.56))
    print(round_max(18557.36))
    print(round_max(1.8653))
    print("expected: 185, 18600, 1.87")
