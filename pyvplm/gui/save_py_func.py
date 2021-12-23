import os.path
from datetime import datetime


def open_py_file(f_name):
    """
    :param f_name: name of the .py file (with extension)
    :return: a new file with as many (1) as needed to not already exist
    """
    try:
        f = open(f_name, "x")
        return f, f_name
    except IOError:
        return open_py_file(f_name[:-3] + "(1)" + f_name[-3:])


def save_py_func(model, input_pi_names, workdir, chosen_pi_set, physical_params):
    """
    Parameters
    ----------
    model: Current regression model (full expression as a string)
    input_pi_names: Names of the input pi
    workdir: Current work directory
    chosen_pi_set: Current chosen pi set (PositiveParameterSet)
    physical_params: Defined physical parameters (PositiveParameterSet)

    Returns
    -------

    """
    now = datetime.now()
    dt_string = now.strftime("_%d%m%y_%H%M%S")
    name_date = "pyvplm_model" + dt_string + ".py"
    f, f_name = open_py_file(os.path.join(workdir, name_date))
    f_str = '"""\n' + str(physical_params) + "\n" + str(chosen_pi_set) + '\n"""\n\n'
    parameters = []
    for inp in input_pi_names:
        if inp in model:
            parameters.append(inp)
    if "log(" in model:
        f_str += "from numpy import log10 as log\n\n"
        add_str, parameters = add_constants(parameters, chosen_pi_set)
        f_str += add_str
        param_str = ""
        if parameters:
            for param in parameters:
                param_str += param + ", "
            param_str = param_str[:-2]
        f_str += f"def pyvplm_model({param_str}):\n"
        f_str += warning_constraints(parameters, chosen_pi_set)
        output = model.split('=')[0].strip()
        output = output.replace("log(", "")
        output = output.replace(")", "")
        f_str += f"    log10_{output} = {model.split('=')[1]}\n"
        f_str += f"    {output} = 10**log10_{output}\n"
        f_str += f"    return {output}\n"
        f.write(f_str)
        f.close()
        os.system(f"black {f_name}")
    else:
        add_str, parameters = add_constants(parameters, chosen_pi_set)
        f_str += add_str
        param_str = ""
        if parameters:
            for param in parameters:
                param_str += param + ", "
            param_str = param_str[:-2]
        f_str += f"def pyvplm_model({param_str}):\n"
        f_str += warning_constraints(parameters, chosen_pi_set)
        f_str += f"    {model}\n"
        f_str += f"    return {model.split('=')[0].strip()}\n"
        f.write(f_str)
        f.close()
        os.system(f"black {f_name}")
    return f_name


def warning_constraints(parameters, chosen_pi_set):
    """
    Parameters
    ----------
    parameters: Names of the input pi numbers used in the py function
    chosen_pi_set: Current chosen pi set (PositiveParameterSet)

    Returns Adds warnings if the input pi numbers are out of bounds
    -------

    """
    f_str = ""
    for name in parameters:
        pi = chosen_pi_set[name]
        bounds = pi.defined_bounds
        if len(bounds) == 2:
            f_str += f"    if {bounds[0]} > {name} or {name} > {bounds[1]}:\n" \
                     f"        print('Warning: {name} out of bounds, model is out of its validity domain')\n"
    return f_str


def add_constants(parameters, chosen_pi_set):
    """
    Parameters
    ----------
    parameters: Names of the input pi numbers used in the py function
    chosen_pi_set: Current chosen pi set (PositiveParameterSet)

    Returns Function to support constant pi numbers
    -------

    """
    f_str = "#  Constant(s):\n\n"
    const = False
    new_parameters = parameters
    for name in parameters:
        pi = chosen_pi_set[name]
        bounds = pi.defined_bounds
        value = pi.value
        if len(bounds) != 2:
            f_str += f"{name} = {value[0]}\n"
            new_parameters.remove(name)
            const = True
    if const:
        return f_str, new_parameters
    else:
        return "", new_parameters
