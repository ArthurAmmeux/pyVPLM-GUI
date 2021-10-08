def format_pi_set(pi_set):
    lines = pi_set.splitlines()
    new_pi_set = ""
    for i in range(len(lines)):
        if '=' not in lines[i]:
            spt = lines[i].split("], ")
        else:
            spt = lines[i].split("=")
        if len(spt) == 2:
            new_pi_set += f"Pi{i+1} = {spt[1]}\n"
    return new_pi_set


def format_input(inp, index):
    return f"Pi{index} = {inp}"


def get_pi_index(pi_set):
    if pi_set is not None:
        return len(pi_set.splitlines()) + 1
    else:
        return 1


def format_area(area):
    lines = area.splitlies()
    lis = []
    for line in lines:
        spt = line.split("= ")
        if len(spt) == 2:
            lis.append(spt[1])
    return tuple(lis)
