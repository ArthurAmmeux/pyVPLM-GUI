def format_pi_set(pi_set):
    lines = pi_set.splitlines()
    new_pi_set = ""
    for i in range(len(lines)):
        if '=' not in lines[i]:
            spt = lines[i].split("], ")
        else:
            if "]" not in lines[i]:
                spt = lines[i].split(",")
            else:
                spt = lines[i].split("=")
        if len(spt) == 2:
            new_pi_set += f"pi{i+1} = {spt[1]}\n"
    return new_pi_set


def pi_list_to_str(pi_list):
    out_set = ""
    if len(pi_list) > 0:
        for i in range(len(pi_list)):
            if pi_list[i] is not None:
                out_set += f"pi{i + 1} = {pi_list[i]} | "
        if len(out_set) > 2:
            out_set = out_set[:-2]
    return out_set


def pi_sub_list_to_str(pi_list, index):
    out_set = ""
    if len(pi_list) > 0:
        for i in range(len(pi_list)):
            out_set += f"pi{index[i]+1} = {pi_list[i]} | "
        out_set = out_set[:-2]
    return out_set


def format_auto_pi_set(pi_set):
    spt = pi_set.split('|')
    f_pi_set = ""
    for ps in spt:
        ps = ps.strip()
        ps = ps.replace('=', ' = ')
        f_pi_set += ps + "\n"
    return f_pi_set


def format_input(inp, index):
    return f"Pi{index} = {inp}"


def format_force_area(text):
    if text is None:
        raise SyntaxError("No pi number defined")
    lines = text.splitlines()
    if len(lines) == 0:
        raise SyntaxError("No pi number defined")
    pi_list = []
    if '|' in text:
        try:
            spt = text.split('|')
            for exp in spt:
                pi_list.append(exp.split('=')[1].strip())
        except Exception:
            raise SyntaxError('Invalid syntax')
    else:
        for line in lines:
            if '=' in line:
                spt = line.split('=')
                if len(spt) != 2:
                    raise SyntaxError("Invalid syntax")
                pi_list.append(spt[1].strip())
            else:
                pi_list.append(line.strip())
    return pi_list


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


def check_outputs(pi_list, parameter_set, outputs):
    parameter_list = []
    for param_name in parameter_set.dictionary:
        parameter_list.append(param_name)
    param_out = parameter_list[-outputs:]
    for p in param_out:
        n = 0
        for pi_exp in pi_list:
            if is_in_pi(p, pi_exp):
                n += 1
        if n > 1:
            return True
    return False


def output_pi_index(pi_list, parameter_set, outputs):
    if pi_list:
        output_index = []
        parameter_list = []
        for param_name in parameter_set.dictionary:
            parameter_list.append(param_name)
        param_out = parameter_list[-outputs:]
        for i in range(len(pi_list)):
            for p in param_out:
                if is_in_pi(p, pi_list[i]):
                    output_index.append(i)
        return output_index
    raise ValueError('Pi list empty')


def is_in_pi(param_name, pi_exp):
    _vars = pi_exp.split('*')
    raw_vars = []
    for _var in _vars:
        raw_vars += _var.split('/')
    vars = []
    for raw_var in raw_vars:
        var = raw_var.strip()
        var = var.replace('(', '')
        var = var.replace(')', '')
        vars.append(var)
    for var in vars:
        if var == param_name:
            return True
    return False
