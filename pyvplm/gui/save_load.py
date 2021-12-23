import numpy as np
import pandas as pd

from pyvplm.core.definition import PositiveParameter, PositiveParameterSet


def open_file(f_name):
    """
    :param f_name: name of the file
    :return: a new file with as many (1) as needed to not already exist
    """
    try:
        f = open(f_name, "x")
        return f, f_name
    except IOError:
        return open_file(f_name[:-4] + "(1)" + f_name[-4:])


def parameter_to_str(param: PositiveParameter):
    """
    Parameters
    ----------
    param PositiveParameter

    Returns A string representation
    -------

    """
    bounds = "#"
    if param.defined_bounds:
        bounds = str(param.defined_bounds)[1:-1]
    value = "#"
    if param.value:
        value = str(param.value[0])
    return param.name + "|" + param.description + "|" + param.defined_units + "|" + bounds + "|" + value


def parameter_set_to_str(param_set: PositiveParameterSet):
    """
    Parameters
    ----------
    param_set PositiveParameterSet

    Returns A string representation
    -------

    """
    if param_set is None:
        return "None"
    rtn = ""
    for param_name in param_set.dictionary:
        rtn += parameter_to_str(param_set.dictionary[param_name]) + "\n"
    return rtn


def pi_list_to_str(pi_list):
    """
    Parameters
    ----------
    pi_list List of pi expression

    Returns A string representation
    -------

    """
    wrt = ""
    if len(pi_list) > 0:
        for eq in pi_list:
            wrt += eq + "\n"
        return wrt[:-1]
    return "None"


def str_to_pi_list(inp):
    """

    Parameters
    ----------
    inp Input string

    Returns A list of pi expressions
    -------

    """
    lines = inp.strip().splitlines()
    lis = []
    for line in lines:
        if line == "None":
            return []
        lis.append(line)
    return lis


def str_to_parameter(line):
    """
    Parameters
    ----------
    line String

    Returns PositiveParameter
    -------

    """
    spt = line.split('|')
    if spt[3] == "#":
        if spt[4] == "#":
            raise ValueError('No defined_bounds or value')
        else:
            bounds = [float(spt[4])]
    else:
        bounds = spt[3].split(',')
    param = PositiveParameter(spt[0], bounds, spt[2], spt[1])
    return param


def str_to_parameter_set(inp):
    """
    Parameters
    ----------
    inp Input string

    Returns A PositiveParameterSet or None if the string is ""
    -------

    """
    if inp.strip() == "None":
        return None
    lines = inp.strip().splitlines()
    param_list = []
    for line in lines:
        param_list.append(str_to_parameter(line))
    return PositiveParameterSet(*param_list)


def nested_list_to_list(n_lis):
    """
    Parameters
    ----------
    n_lis Nested list

    Returns A list with only elements (that are not lists themselves)
    -------

    """
    lis = []
    for item in n_lis:
        lis.append(item[0])
    return lis


def str_to_list(string):
    """
    Parameters
    ----------
    string String representation of a list

    Returns A List
    -------

    """
    if "[" and "]" in string:
        string = string[1:-1]
        spt = string.split(",")
        lis = []
        for f in spt:
            lis.append(float(f))
        return lis
    return []


def save(file_name, items, buck_area, force_area, auto_items, tab2_state, physical_params, pi_sets, chosen_pi_set,
         pi_lists, chosen_pi_list, phy_const, pi_const, doe_params, doe, result, dep_slider, dep_check_state,
         reg_pi_list, reg_state, models):
    """
    Parameters
    ----------
    file_name: File path
    items: Physical parameters DataTable items
    buck_area: Content of simple Buckingham area
    force_area: Content of force Buckingham area
    auto_items: Content of automatic Buckingham DataTable
    tab2_state: State of Buckingham Theorem tab
    physical_params: Defined physical parameters
    pi_sets: List of all generated pi sets
    chosen_pi_set: The current chosen pi set
    pi_lists: List of all pi lists
    chosen_pi_list: The current chosen pi list
    phy_const: Content of physical parameter constraints area
    pi_const: Content of pi constraints area
    doe_params: Parameters to generate a DOE
    doe: The last generated DOE
    result: The last imported result
    dep_slider: R^2 threshold slider state
    dep_check_state: Dependency analysis tab checkboxes state
    reg_pi_list: Effective pi list for regression
    reg_state: State of the regression tab
    models: Computed regression models

    Returns Saves all this data in a .txt at the file name path
    -------

    """
    f = open_file(file_name)[0]
    wrt = ""
    # Physical parameters [0]
    for item in items:
        wrt += item["name"] + "|" + item["description"] + "|" + item["unit"] + "|"
        wrt += str(item["lower bound"]) + "|" + str(item["upper bound"]) + "|" + item["in/out"] + "\n"
    wrt += "---\n"  # Buckingham TextArea content [1]
    wrt += buck_area
    wrt += "\n---\n"  # Force Buckingham TextArea content [2]
    wrt += force_area
    wrt += "\n---\n"  # Automatic Buckingham DataTable content [3]
    wrt_items = ""
    for item in auto_items:
        wrt_items += item["expressions"] + "\n"
    if len(wrt_items) > 1:
        wrt += wrt_items[:-1]
    wrt += "\n---\n"  # State of the checkboxes of the Buckingham tab [4]
    wrt_ts = ""
    for ts in tab2_state:
        wrt_ts += str(ts) + "#"
    wrt += wrt_ts[:-1]
    wrt += "\n---\n"  # Physical parameters in a PositiveParameterSet type [5]
    wrt += parameter_set_to_str(physical_params)
    wrt += "\n---\n"  # Pi sets calculated in the buckingham tab in a PositiveParameterSet type [6]
    if pi_sets != [None, None, []]:
        wrt += parameter_set_to_str(pi_sets[0]) + "\n+++\n"
        wrt += parameter_set_to_str(pi_sets[1]) + "\n+++\n"
        for pi_set in pi_sets[2]:
            wrt += parameter_set_to_str(pi_set) + "\n+++\n"
        wrt = wrt[:-5]
    else:
        wrt += "None\n+++\nNone"
    wrt += "\n---\n"  # Pi set chosen in the Buckingham tab [7]
    if chosen_pi_set is not None:
        wrt += parameter_set_to_str(chosen_pi_set)
    else:
        wrt += "None"
    wrt += "\n---\n"  # Pi sets calculated in the buckingham tab in a list of expressions form [8]
    if pi_lists != [[], [], []]:
        wrt += pi_list_to_str(pi_lists[0]) + "\n+++\n"
        wrt += pi_list_to_str(pi_lists[1]) + "\n+++\n"
        for lis in pi_lists[2]:
            wrt += pi_list_to_str(lis) + "\n+++\n"
        wrt = wrt[:-5]
    else:
        wrt += "None\n+++\nNone"
    wrt += "\n---\n"  # Pi list chosen in the Buckingham tab [9]
    if len(chosen_pi_list) > 0:
        wrt += pi_list_to_str(chosen_pi_list)
    else:
        wrt += "None"
    wrt += "\n---\n"  # Constraints defined in the DOE tab (physical and pi constraint TextArea content) [10]
    wrt += phy_const + "\n+++\n" + pi_const
    wrt += "\n---\n"  # States of the input widgets between constraints definition and DOE calculation [11]
    wrt += doe_params[0]
    wrt += "\n+++\n"
    wrt += doe_params[1]
    wrt += "\n+++\n"
    wrt += str(doe_params[2])
    wrt += "\n---\n"  # Intermediate DOEs (in pi space) to be shown by the plots in the DOE tab [12]
    first = True
    for spe_doe in doe:
        if first:
            first = False
        else:
            wrt += "\n+++\n"
        for i in range(spe_doe.shape[0]):
            wrt += str(spe_doe[i, :]) + "\n"
    wrt += "\n---\n"  # Imported result in the Result Import tab [13]
    if result[1]:
        wrt += str(result[0])
        wrt += "\n+++\n"
        for item in result[1]:
            wrt += str(item["Measure"])
            for key in item:
                if key != "Measure":
                    wrt += '|'
                    wrt += str(item[key])
            wrt += "\n"
    else:
        wrt += "None\n+++\nNone"
    wrt += "\n---\n"  # State of the checkboxes and slider in the Dependency tab [14]
    dcs = ""
    for boo in dep_check_state:
        dcs += str(boo) + "|"
    if len(dcs) > 0:
        dcs = dcs[:-1]
    wrt += dcs
    wrt += "\n+++\n"
    wrt += str(dep_slider)
    wrt += "\n---\n"  # Relevant pi list for the regression tab [15]
    rpl = ""
    for pi in reg_pi_list:
        rpl += str(pi) + "|"
    if len(rpl) > 0:
        rpl = rpl[:-1]
    wrt += rpl
    wrt += "\n---\n"  # State of the widgets in the regression tab [16]
    wrt += reg_state[0] + "|" + reg_state[1] + "|" + str(reg_state[2]) + "|" + str(reg_state[3]) + "|" + \
        str(reg_state[4])
    wrt += "\n---\n"  # Regression models [17]
    str_models = ""
    if models:
        for i in range(1, len(models) - 3):
            model_i_2 = str(nested_list_to_list(models[i][2].values.tolist()))
            model_i_3 = str(nested_list_to_list(models[i][3].values.tolist()))

            str_models += str(models[i][0]) + "\n" + str(list(models[i][1])) + "\n" + \
                          model_i_2 + "\n" + model_i_3 + "\n|||\n"
        str_models = str_models[:-5] + "\n+++\n"
        str_models += str(models["max |e|"][0]) + "\n+++\n" + str(models["max |e|"][1]) + "\n+++\n"
        str_models += str(models["ave. |e|"][0]) + "\n+++\n" + str(models["ave. |e|"][1]) + "\n+++\n"
        str_models += str(models["ave. e"][0]) + "\n+++\n" + str(models["ave. e"][1]) + "\n+++\n"
        str_models += str(models["sigma e"][0]) + "\n+++\n" + str(models["sigma e"][1])
    wrt += str_models
    wrt += "\n---\n"
    f.write(wrt)
    f.close()


def load(f_name):
    """
    Parameters
    ----------
    f_name File path

    Returns Loads all the parameters saved by the saved function
    -------

    """
    try:
        f = open(f_name, "r")
    except FileNotFoundError:
        try:
            f_name = f_name.replace("\\\\", "\\")
            f = open(f_name, "r")
        except FileNotFoundError as e:
            raise FileNotFoundError(e)
    data = []
    read_save = f.read()
    spt_save = read_save.split("---")
    lines = spt_save[0].splitlines()  # Physical parameters [0]
    outputs = 0

    for line in lines:
        line = line.strip()
        if line != "":
            dic = {}
            items = line.split('|')
            dic["name"] = items[0]
            dic["description"] = items[1]
            dic["unit"] = items[2]
            if items[3] == "None" or items[3] == "":
                dic["lower bound"] = ""
            else:
                dic["lower bound"] = float(items[3])
            dic["upper bound"] = float(items[4])
            dic["in/out"] = items[5]
            if items[5] == "Output":
                outputs += 1
            data.append(dic)

    buck_area = spt_save[1].strip()  # Buckingham TextArea content [1]

    force_area = spt_save[2].strip()  # Force Buckingham TextArea content [2]

    expressions = spt_save[3].strip().splitlines()  # Automatic Buckingham DataTable content [3]
    items = []
    for i in range(len(expressions)):
        items.append({"pi set number": i + 1, "expressions": expressions[i]})

    tab2_state_spt = spt_save[4].strip().split("#")  # State of the checkboxes of the Buckingham tab [4]
    if len(tab2_state_spt) != 5:
        raise ValueError
    tab2_state = []
    for i in range(4):
        tab2_state.append(tab2_state_spt[i] == "True")
    tab2_state.append(int(tab2_state_spt[4]))

    physical_params = str_to_parameter_set(spt_save[5])  # Physical parameters in a PositiveParameterSet type [5]

    pi_sets = [None, None, []]
    spt_sets = spt_save[6].split('+++')  # Pi sets calculated in the buckingham tab in a PositiveParameterSet type [6]
    pi_sets[0] = str_to_parameter_set(spt_sets[0])
    pi_sets[1] = str_to_parameter_set(spt_sets[1])
    for i in range(2, len(spt_sets)):
        pi_sets[2].append(str_to_parameter_set(spt_sets[i]))

    chosen_pi_set = str_to_parameter_set(spt_save[7])  # Pi set chosen in the Buckingham tab [7]

    pi_lists = [[], [], []]
    spt_lists = spt_save[8].split('+++')  # Pi sets calculated in the buckingham tab in a list of expressions form [8]
    pi_lists[0] = str_to_pi_list(spt_lists[0])
    pi_lists[1] = str_to_pi_list(spt_lists[1])
    for i in range(2, len(spt_lists)):
        pi_lists[2].append(str_to_pi_list(spt_lists[i]))

    chosen_pi_list = str_to_pi_list(spt_save[9])  # Pi list chosen in the Buckingham tab [9]

    constraints = spt_save[10].split("+++")  # Constraints defined in the DOE tab (physical and pi constraints) [10]
    constraints[0] = constraints[0].strip()
    constraints[1] = constraints[1].strip()

    doe_params = spt_save[11].split("+++")  # States of the widgets between constraints and DOE calculation [11]
    doe_params[0] = doe_params[0].strip()
    doe_params[1] = doe_params[1].strip()
    doe_params[2] = int(doe_params[2].strip())

    spt_doe = spt_save[12].split('+++')  # Intermediate DOEs (in pi space) to be shown by the plots in the DOE tab [12]
    doe = []
    for spe_doe in spt_doe:
        doe_to_add = []
        lines = spe_doe.split("]\n[")
        for line in lines:
            strip_line = line.strip()
            if strip_line:
                f_inp = strip_line.replace("[", "")
                f_inp = f_inp.replace("]", "")
                row = f_inp.split()
                doe_to_add.append(row)
        if not doe_to_add:
            doe = []
            break
        doe.append(np.array(doe_to_add, dtype=float))

    spt_result = spt_save[13].split('+++')  # Imported result in the Result Import tab [13]
    if spt_result[0].strip() == "None":
        result_headers = [{'text': 'Measure', 'sortable': True, 'value': 'Measure'},
                          {'text': 'Parameters', 'sortable': True, 'value': 'Parameters'}]
        result_items = []
    else:
        result_headers = spt_result[0].strip()[1:-1].split(",")
        for i in range(len(result_headers)):
            result_headers[i] = result_headers[i].replace("'", "").strip()
        lines = spt_result[1].splitlines()
        result_items = []
        for line in lines:
            if line.strip() != "":
                values = line.strip().split('|')
                item = {}
                for i in range(len(result_headers)):
                    item[result_headers[i]] = values[i]
                result_items.append(item)
    result = [result_headers, result_items]
    spt_dep_check_state = spt_save[14].strip().split("+++")  # State of the checkboxes and slider in Dependency tab [14]
    dep_check_state = []
    dep_slider = 0.9
    if spt_dep_check_state:
        for val in spt_dep_check_state[0].strip().split('|'):
            if val == "True":
                dep_check_state.append(True)
            else:
                dep_check_state.append(False)
        dep_slider = float(spt_dep_check_state[1].strip())

    spt_rpl = spt_save[15].strip().split("|")  # Relevant pi list for the regression tab [15]
    regression_pi_list = []
    for pi in spt_rpl:
        if pi == "None":
            regression_pi_list.append(None)
        else:
            regression_pi_list.append(pi)
    reg_state = spt_save[16].strip().split("|")  # State of the widgets in the regression tab [16]
    models = {}
    spt_models = spt_save[17].strip().split("\n+++\n")  # Regression models [17]
    if spt_models and spt_models[0]:
        spt_expr = spt_models[0].split("\n|||\n")
        for i in range(len(spt_expr)):
            lines = spt_expr[i].splitlines()
            expression = lines[0]
            coeff = str_to_list(lines[1])
            error_train = str_to_list(lines[2])
            error_train = np.array(error_train)
            error_train = pd.DataFrame(error_train, index=["max |e|", "ave. |e|", "ave. e", "sigma e"])
            error_test = str_to_list(lines[3])
            error_test = np.array(error_test)
            error_test = pd.DataFrame(error_test, index=["max |e|", "ave. |e|", "ave. e", "sigma e"])
            models[i + 1] = (expression, coeff, error_train, error_test)
        abs_error_max_train = str_to_list(spt_models[1])
        abs_error_max_test = str_to_list(spt_models[2])
        abs_error_average_train = str_to_list(spt_models[3])
        abs_error_average_test = str_to_list(spt_models[4])
        error_average_train = str_to_list(spt_models[5])
        error_average_test = str_to_list(spt_models[6])
        error_sigma_train = str_to_list(spt_models[7])
        error_sigma_test = str_to_list(spt_models[8])

        models["max |e|"] = [abs_error_max_train, abs_error_max_test]
        models["ave. |e|"] = [abs_error_average_train, abs_error_average_test]
        models["ave. e"] = [error_average_train, error_average_test]
        models["sigma e"] = [error_sigma_train, error_sigma_test]

    f.close()
    return data, buck_area, force_area, items, tab2_state, physical_params, outputs, pi_sets, chosen_pi_set, pi_lists, \
        chosen_pi_list, constraints, doe_params, doe, result, dep_slider, dep_check_state, regression_pi_list,\
        reg_state, models
