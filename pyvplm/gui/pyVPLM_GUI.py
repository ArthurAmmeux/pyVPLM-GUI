# Import pyVPLM packages
import matplotlib

from pyvplm.core.definition import PositiveParameter, PositiveParameterSet
from pyvplm.addon import variablepowerlaw as vpl
from pyvplm.addon import pixdoe as doe
from pint import UnitRegistry
import save_load as sl
import pi_format as pif
import csv_export as csv
import constraint_format as csf
import round_minmax as rmm
import constant_pi as cpi
import number_of_coeff as noc
import dependency_plot as dpp
import save_plots as spl

# Import libs
import copy
import os
import pandas as pd
from pandas.plotting import scatter_matrix
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
import webbrowser
import ipyfilechooser as ipf
import time
from datetime import datetime
import ipywidgets as widgets
import ipyvuetify as v
from IPython.display import display, clear_output
import warnings
import seaborn as sns
from win32gui import GetWindowRect, GetForegroundWindow
# ------------Constants------------------------
from text_list import TEXT_LIST as TL

FORBIDDEN_CHARACTERS = [' ', '|', '*', '/', '-', '+', ',', "#", "!", "$", "£", "%", "^", "#", "&", "?", ";", "ù", "é",
                        "@", "¤", "µ", "è", "°", "\\"]
FORBIDDEN_PARAMS = ['I', 'gamma', 'beta', 're', 'ln', 'sqrt', 'arg']
DOE_MULTIPLIER = 10

# ------------Global variables-----------------
WORKDIR = os.path.abspath(os.getcwd())
OUTPUTS = 0
PHYSICAL_PARAMS = None
OLD_PHYSICAL_PARAMS = None
CHOSEN_PI_SET = None
PI_SETS = [None, None, []]
CHOSEN_PI_LIST = []
PI_LISTS = [[], [], []]
DOE_PI_LIST = []
DOE = []
TOTAL_DOE = pd.DataFrame()
FIG = plt.Figure()
AX = FIG.add_subplot(111)
RESULT_DF = pd.DataFrame()
OLD_RESULT = pd.DataFrame()
OLD_PI_SET = []
RESULT_PI = np.array([])
DEPENDENCY_CHECK_STATE = []
OLD_DEPENDENCY_CHECK_STATE = []
REGRESSION_PI_LIST = []
MODELS = {}
REGRESSIONS = []
PI0_PI_LIST = []


# -----------Functions--------------------------
def check_name(name):
    """
    Parameters
    ----------
    name String in name TextField

    Returns Boolean : True if the name is valid
    -------

    """
    if name == '':
        name_entry.error_messages = TL[0]
        return False
    for for_char in FORBIDDEN_CHARACTERS:
        if for_char in name:
            name_entry.error_messages = f"{TL[1]}: {for_char}"
            return False
    for for_param in FORBIDDEN_PARAMS:
        if name == for_param:
            name_entry.error_messages = f"{TL[51]}: {for_param}"
            return False
    for item in sheet.items:
        if item['name'] == name or item['name'].lower() == name:
            name_entry.error_messages = TL[2]
            return False
    return True


def check_desc(desc):
    """
    Parameters
    ----------
    desc String in description TextField

    Returns Boolean : True if the description is valid
    -------

    """
    if '|' in desc:
        desc_entry.error_messages = TL[3]
        return False
    return True


def check_unit(unit):
    """
    Parameters
    ----------
    unit String in unit TextField

    Returns Boolean : True if the unit is recognized by pint
    -------

    """
    if unit == '':
        unit_entry.error_messages = TL[4]
        return False
    base_registry = UnitRegistry()
    if unit not in base_registry:
        unit_entry.error_messages = TL[5]
        return False
    return True


def check_bounds():
    """
    Returns Boolean : True if the bounds in the lower bound and upper bound TextFields are valid
    -------

    """
    lb = lb_entry.v_model
    ub = ub_entry.v_model
    lbool = lb is None or lb == ""
    ubool = ub is None or ub == ""
    if ubool:
        ub_entry.error_messages = TL[6]
        return False
    err_mess = TL[7]
    if lbool:
        try:
            float(ub)
            return True
        except ValueError:
            ub_entry.error_messages = err_mess
            return False
    else:
        brk = False
        try:
            ub = float(ub)
        except ValueError:
            ub_entry.error_messages = err_mess
            brk = True
        try:
            lb = float(lb)
        except ValueError:
            lb_entry.error_messages = err_mess
            brk = True
        if brk:
            return False
        if 0 < lb < ub:
            return True
        else:
            neg = False
            err_mess = TL[8]
            if lb <= 0:
                neg = True
                lb_entry.error_messages = err_mess
            if ub <= 0:
                neg = True
                ub_entry.error_messages = err_mess
            if neg:
                return False
            else:
                err_mess = TL[9]
                lb_entry.error_messages = err_mess
                ub_entry.error_messages = err_mess
            return False


def add_item(widget, event, data):
    """
    Returns Adds parameter specified by the user in the sheet DataTable, if one of the attributes is invalid, shows the
    user an error under the TextField
    -------

    """
    name_entry.error_messages = ''
    desc_entry.error_messages = ''
    unit_entry.error_messages = ''
    lb_entry.error_messages = ''
    ub_entry.error_messages = ''
    if check_name(name_entry.v_model) and check_desc(desc_entry.v_model) and check_unit(
            unit_entry.v_model) and check_bounds():
        name = name_entry.v_model
        description = desc_entry.v_model
        unit = unit_entry.v_model
        lb = lb_entry.v_model
        if lb:
            lower_bound = float(lb_entry.v_model)
        else:
            lower_bound = None
            name = name.upper()
        upper_bound = float(ub_entry.v_model)
        name_entry.v_model = ''
        desc_entry.v_model = ''
        unit_entry.v_model = ''
        lb_entry.v_model = None
        ub_entry.v_model = None
        sheet.items = sheet.items + [{"name": name,
                                      "description": description,
                                      "unit": unit,
                                      "lower bound": lower_bound,
                                      "upper bound": upper_bound,
                                      "in/out": "Input"}]


def order_items():
    """
    Leaves output physical parameters at the end of the set (least priority to be repetitive)
    Returns ordered physical parameters
    -------

    """
    data = sheet.items
    inputs = []
    outputs = []
    for item in data:
        if item["in/out"] == TL[10]:
            outputs.append(item)
        else:
            inputs.append(item)
    return inputs + outputs


def gen_parameter_set():
    """
    Returns Generates a PositiveParameterSet from the physical parameters in the sheet DataTable, if there are none,
    returns None
    -------

    """
    data = order_items()
    if len(data) > 0:
        first = True
        param_set = {}
        for item in data:
            if item['lower bound'] is None or item['lower bound'] == "":
                bounds = [item['upper bound']]
                item['name'] = item['name'].upper()
            else:
                bounds = [item['lower bound'], item['upper bound']]
            param = PositiveParameter(item['name'], bounds, item['unit'], item['description'])
            param_set[item['name']] = param
            if first:
                param_set = PositiveParameterSet(param)
                first = False
        return param_set
    return None


def get_outputs():
    """
    Returns int : The number of output parameters specified
    -------

    """
    global OUTPUTS
    n = 0
    for item in sheet.items:
        if item['in/out'] == TL[10]:
            n += 1
    OUTPUTS = n


def buckingham():
    """
    Returns Shows the set in buck_area and modifies current_set
    -------

    """
    global PHYSICAL_PARAMS, PI_LISTS, PI_SETS
    if PHYSICAL_PARAMS is not None:
        # noinspection PyTypeChecker
        PI_SETS[0], PI_LISTS[0] = vpl.buckingham_theorem(PHYSICAL_PARAMS, True)
        pi_set_str = str(PI_SETS[0])
        formatted_pi_set = pif.format_pi_set(pi_set_str)
        buck_area.v_model = formatted_pi_set
        if force_area.v_model is None or force_area.v_model == "":
            force_area.v_model = formatted_pi_set
        if check1.v_model:
            global CHOSEN_PI_SET, CHOSEN_PI_LIST
            CHOSEN_PI_SET = PI_SETS[0]
            CHOSEN_PI_LIST = PI_LISTS[0]
            update_current_set()
    if PI_LISTS[0]:
        return True
    return False


def force_buckingham(widget, event, data):
    """
    Parameters
    ----------
    widget force_buck_btn : button to check pi set

    Returns Enables selection of the specified pi set if it is valid
    -------

    """
    widget.disabled = True
    widget.loading = True
    if force_buck_btn.children == [TL[11]]:
        param_set = gen_parameter_set()
        global OUTPUTS
        out_n = OUTPUTS
        try:
            global PI_LISTS
            PI_LISTS[1] = pif.format_force_area(force_area.v_model)
            global PI_SETS
            PI_SETS[1] = vpl.force_buckingham(param_set, *PI_LISTS[1])
            if pif.check_outputs(PI_LISTS[1], param_set, out_n):
                raise ValueError(TL[12])
            force_area.error_messages = ""
            force_area.success_messages = TL[13]
            check2.disabled = False
            force_area.readonly = True
            force_area.clearable = False
            if ' | ' in force_area.v_model:
                force_area.v_model = force_area.v_model.replace(' | ', '\n')
            force_area.background_color = "grey lighten-3"
            force_eq.disabled = True
            force_eq.v_model = ""
            force_eq.background_color = "grey lighten-3"
            add_pi_btn.disabled = True
            force_copy_btn.disabled = True
            force_buck_btn.children = [TL[14]]
        except Exception as e:
            force_area.success_messages = ""
            force_area.error_messages = TL[15] + str(e)
    else:
        force_area.success_messages = ""
        check2.disabled = True
        check2.v_model = False
        global CHOSEN_PI_SET, CHOSEN_PI_LIST
        CHOSEN_PI_SET = None
        CHOSEN_PI_LIST = []
        update_current_set()
        force_area.readonly = False
        force_area.clearable = True
        force_area.background_color = "white"
        force_eq.disabled = False
        force_eq.background_color = "white"
        add_pi_btn.disabled = False
        if auto_buck_table.v_model:
            force_copy_btn.disabled = False
        force_area.messages = ""
        force_buck_btn.children = [TL[11]]
    widget.loading = False
    widget.disabled = False


def automatic_buckingham(widget, event, data):
    """
    Parameters
    ----------
    widget auto_buck_btn : button to perform automatic Buckingham analysis

    Returns Fills auto_buck_table with the resulting pi sets
    -------

    """
    widget.disabled = True
    widget.loading = True
    param_set = gen_parameter_set()
    combinator_pi_set, alternative_set_dict = vpl.automatic_buckingham(param_set, True)
    global PI_SETS, PI_LISTS, PHYSICAL_PARAMS, OUTPUTS
    for n in combinator_pi_set:
        PI_SETS[2].append(combinator_pi_set[n][0])
        PI_LISTS[2].append(list(combinator_pi_set[n][1]))
    items = []
    i = 0
    j = 1
    del_index = []
    for exp in alternative_set_dict:
        if not pif.check_outputs(PI_LISTS[2][i], PHYSICAL_PARAMS, OUTPUTS):
            items.append({"pi set number": j, "expressions": exp})
            j += 1
        else:
            del_index.append(i)
        i += 1
    del_index.reverse()
    for i in del_index:
        PI_SETS[2].pop(i)
        PI_LISTS[2].pop(i)
    auto_buck_table.items = items
    if force_buck_btn.children == [TL[11]]:
        force_copy_btn.disabled = False
    check3.disabled = False
    widget.loading = False
    widget.disabled = False


def force_copy(widget, event, data):
    """
    Returns Copies the selected pi set from auto_buck_table to force_area
    -------

    """
    l = len(auto_buck_table.items)
    if auto_buck_table.v_model:
        pi_set_nb = auto_buck_table.v_model[0]['pi set number']
        for i in range(0, l):
            if auto_buck_table.items[i]['pi set number'] == pi_set_nb:
                force_area.v_model = pif.format_auto_pi_set(auto_buck_table.v_model[0]['expressions'])
                break


def check1_change(widget, event, data):
    """
    Parameters
    ----------
    event Boolean : state of the checkbox

    Returns Modifies current_set with the pi set in buck_area
    -------

    """
    global CHOSEN_PI_SET, CHOSEN_PI_LIST
    if data:
        check2.v_model = False
        check3.v_model = False
        CHOSEN_PI_SET = PI_SETS[0]
        CHOSEN_PI_LIST = PI_LISTS[0]
        update_current_set()
    else:
        CHOSEN_PI_SET = None
        CHOSEN_PI_LIST = []
        update_current_set()


def check2_change(widget, event, data):
    """
    Parameters
    ----------
    event Boolean : state of the checkbox

    Returns Modifies current_set with the pi set in force_area
    -------

    """
    global CHOSEN_PI_SET, CHOSEN_PI_LIST
    if data:
        check1.v_model = False
        check3.v_model = False
        CHOSEN_PI_SET = PI_SETS[1]
        CHOSEN_PI_LIST = PI_LISTS[1]
        update_current_set()
    else:
        CHOSEN_PI_SET = None
        CHOSEN_PI_LIST = []
        update_current_set()


def check3_change(widget, event, data):
    """
    Parameters
    ----------
    event Boolean : state of the checkbox

    Returns Modifies current_set with the selected pi set in auto_buck_table
    -------

    """
    global CHOSEN_PI_SET, CHOSEN_PI_LIST
    if data:
        check1.v_model = False
        check2.v_model = False
        l = len(auto_buck_table.items)
        if auto_buck_table.v_model:
            if auto_buck_table.v_model[0]['pi set number'] is None:
                CHOSEN_PI_SET = None
                CHOSEN_PI_LIST = []
                update_current_set()
            else:
                pi_set_nb = auto_buck_table.v_model[0]['pi set number']
                CHOSEN_PI_SET = PI_SETS[2][pi_set_nb - 1]
                CHOSEN_PI_LIST = PI_LISTS[2][pi_set_nb - 1]
                for i in range(0, l):
                    if auto_buck_table.items[i]['pi set number'] == pi_set_nb:
                        update_current_set()
                        break
    else:
        CHOSEN_PI_SET = None
        CHOSEN_PI_LIST = []
        update_current_set()


def select_auto_pi_set(widget, event, data):
    """
    Parameters
    ----------
    data dict: Contains the pi set number of the selected pi set in the automatic buckingham data table

    Returns Modifies current set accordingly
    -------

    """
    global CHOSEN_PI_SET, CHOSEN_PI_LIST
    if check3.v_model:
        if data['value']:
            pi_set_nb = data['item']['pi set number']
            CHOSEN_PI_SET = PI_SETS[2][pi_set_nb - 1]
            CHOSEN_PI_LIST = PI_LISTS[2][pi_set_nb - 1]
            update_current_set()
        else:
            CHOSEN_PI_SET = None
            CHOSEN_PI_LIST = []
            update_current_set()


def pi_set_html(pi_set):
    """
    Parameters
    ----------
    pi_set: Pi set in a string form (with " | " separators between pi numbers)

    Returns A list of v.HTML widgets that are to be used as children of a v.CardText
    -------

    """
    pi_set = pi_set.replace("**", "°°")
    pi_set = pi_set.replace("*", " * ")
    pi_set = pi_set.replace("°°", "**")
    spt_pi_set = pi_set.split("| ")
    card_text_children = []
    for pi in spt_pi_set:
        card_text_children.append(v.Html(tag='div', children=[pi]))
    return card_text_children


def update_current_set():
    """
    Returns Shows the current selected pi set to the user in current_set Card
    -------

    """
    global CHOSEN_PI_LIST
    out_set = pif.pi_list_to_str(CHOSEN_PI_LIST)
    if out_set:
        current_set.children[0].children = [TL[52]]
        current_set.color = "green lighten-3"
    else:
        current_set.children[0].children = [TL[53]]
        current_set.color = "grey lighten-3"
    current_set.children[1].children = pi_set_html(out_set)


def del_item(widget, event, data):
    """
    Returns Deletes the selected parameter from the sheet data table
    -------

    """
    if sheet.v_model:
        item_name = sheet.v_model[0]['name']
        for i in range(len(sheet.items)):
            if sheet.items[i]['name'] == item_name:
                if i == len(sheet.items):
                    sheet.items = sheet.items[:-1]
                else:
                    sheet.items = sheet.items[0:i] + sheet.items[i + 1:]
                break


def del_all(widget, event, data):
    """
    Returns Deletes all parameters from the sheet data table
    -------

    """
    sheet.items = []


def up_item(widget, event, data):
    """
    Returns Moves up the selected parameter in the sheet data table
    -------

    """
    l = len(sheet.items)
    if l >= 2 and sheet.v_model:
        item_name = sheet.v_model[0]['name']
        for i in range(1, l):
            if sheet.items[i]['name'] == item_name:
                if i == l:
                    sheet.items = sheet.items[0:i - 1] + [sheet.items[i]] + [sheet.items[i - 1]]
                else:
                    sheet.items = sheet.items[0:i - 1] + [sheet.items[i]] + [sheet.items[i - 1]] + sheet.items[i + 1:]
                break


def down_item(widget, event, data):
    """
    Returns Moves down the selected parameter in the sheet data table
    -------

    """
    l = len(sheet.items)
    if l >= 2 and sheet.v_model:
        item_name = sheet.v_model[0]['name']
        for i in range(0, l - 1):
            if sheet.items[i]['name'] == item_name:
                if i == l - 1:
                    sheet.items = sheet.items[0:i] + [sheet.items[i + 1]] + [sheet.items[i]]
                else:
                    sheet.items = sheet.items[0:i] + [sheet.items[i + 1]] + [sheet.items[i]] + sheet.items[i + 2:]
                break


def set_as_out(widget, event, data):
    """
    Returns Sets the selected parameter as output in the sheet data table
    -------

    """
    l = len(sheet.items)
    if l > 0 and sheet.v_model:
        item_name = sheet.v_model[0]['name']
        for i in range(0, l):
            if sheet.items[i]['name'] == item_name:
                if sheet.items[i]['in/out'] == 'Input':
                    if sheet.items[i]['lower bound'] is None or sheet.items[i]['lower bound'] == "":
                        const_alert.value = True
                    else:
                        sheet.items = sheet.items[0:i] + [{"name": sheet.items[i]["name"],
                                                           "description": sheet.items[i]["description"],
                                                           "unit": sheet.items[i]["unit"],
                                                           "upper bound": sheet.items[i]["upper bound"],
                                                           "lower bound": sheet.items[i]["lower bound"],
                                                           'in/out': 'Output'}] + sheet.items[i + 1:]
                else:
                    sheet.items = sheet.items[0:i] + [{"name": sheet.items[i]["name"],
                                                       "description": sheet.items[i]["description"],
                                                       "unit": sheet.items[i]["unit"],
                                                       "upper bound": sheet.items[i]["upper bound"],
                                                       "lower bound": sheet.items[i]["lower bound"],
                                                       'in/out': 'Input'}] + sheet.items[i + 1:]
                break


def error_end(widget, event, data):
    """
    Parameters
    ----------
    widget Current widget

    Returns Hides the error messages on the current widget
    -------

    """
    widget.error_messages = ""


def pint_link(widget, event, data):
    """

    Returns Opens browser to a page with all pint base units
    -------

    """
    webbrowser.open_new(r"https://raw.githubusercontent.com/hgrecco/pint/master/pint/default_en.txt")


def new_log(log, success: bool):
    if success:
        logs_card.class_ = logs_card.class_ + "; green--text"
        logs_card.children = [v.Html(tag='div', children=[log], class_="text-left py-2 px-2")]
    else:
        logs_card.class_ = logs_card.class_ + "; red--text"
        logs_card.children = [v.Html(tag='div', children=[log], class_="text-left py-2 px-2")]


def choose_dir(widget, event, data):
    global WORKDIR
    dialog_dir.children[0].children[1].children = ["Current work directory: " + WORKDIR]
    dialog_dir.v_model = True


def hide_dir(chooser):
    global WORKDIR
    old_workdir = WORKDIR
    spl.add_temp(old_workdir)
    WORKDIR = fc_dir.selected
    spl.move_temp(old_workdir, WORKDIR)
    dialog_dir.v_model = False
    new_log(f"Work directory: {WORKDIR}", True)
    dir_btn.color = "green"
    time.sleep(0.5)
    dir_btn.color = "default"


def save(widget, event, data):
    widget.disabled = True
    global WORKDIR
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%y_%H-%M-%S")
    file_path = WORKDIR + "\pyVPLM_" + dt_string + ".txt"
    widget.disabled = True
    widget.loading = True
    if auto_buck_table.v_model and auto_buck_table.v_model[0]['pi set number'] is not None:
        pi_set_nb = auto_buck_table.v_model[0]['pi set number']
    else:
        pi_set_nb = 0
    force_state = force_buck_btn.children == [TL[11]]
    tab2_state = [check1.v_model, check2.v_model, check3.v_model, force_state, pi_set_nb]
    result = [[header["text"] for header in result_data.headers], result_data.items]
    doe_params = [select_DOE.v_model, select_log.v_model, anticipated_mo_entry.v_model]
    reg_state = [select_pi0.v_model, select_reg_criteria.v_model, model_order_entry.v_model,
                 nb_terms_slider.v_model]
    sl.save(file_path, sheet.items, buck_area.v_model, force_area.v_model, auto_buck_table.items, tab2_state,
            PHYSICAL_PARAMS, PI_SETS, CHOSEN_PI_SET, PI_LISTS, CHOSEN_PI_LIST, phy_const_area.v_model,
            pi_const_area.v_model, doe_params, DOE, result, threshold_slider.v_model, DEPENDENCY_CHECK_STATE,
            REGRESSION_PI_LIST, reg_state, MODELS)
    widget.disabled = False
    new_log(f"Saved at: {file_path}", True)
    widget.color = "green"
    time.sleep(0.5)
    widget.color = "default"


def save_as(widget, event, data):
    """
    Returns Shows the save dialog
    -------

    """
    global WORKDIR
    dialog.children[0].children[1].children = ["Current work directory: " + WORKDIR]
    dialog.v_model = True


def hide_save_as(widget, event, data):
    """
    Parameters
    ----------
    widget The OK button in the save dialog

    Returns Saves a .txt file with all current user input to the specified path and hides the save dialog
    -------

    """
    global WORKDIR
    save_as_tf.error_messages = ""
    if save_as_tf.v_model.strip():
        file_path = WORKDIR + "\\" + save_as_tf.v_model + ".txt"
        widget.disabled = True
        widget.loading = True
        if auto_buck_table.v_model and auto_buck_table.v_model[0]['pi set number'] is not None:
            pi_set_nb = auto_buck_table.v_model[0]['pi set number']
        else:
            pi_set_nb = 0
        force_state = force_buck_btn.children == [TL[11]]
        tab2_state = [check1.v_model, check2.v_model, check3.v_model, force_state, pi_set_nb]
        result = [[header["text"] for header in result_data.headers], result_data.items]
        doe_params = [select_DOE.v_model, select_log.v_model, anticipated_mo_entry.v_model]
        reg_state = [select_pi0.v_model, select_reg_criteria.v_model, model_order_entry.v_model,
                     nb_terms_slider.v_model]

        sl.save(file_path, sheet.items, buck_area.v_model, force_area.v_model, auto_buck_table.items, tab2_state,
                PHYSICAL_PARAMS, PI_SETS, CHOSEN_PI_SET, PI_LISTS, CHOSEN_PI_LIST, phy_const_area.v_model,
                pi_const_area.v_model, doe_params, DOE, result, threshold_slider.v_model, DEPENDENCY_CHECK_STATE,
                REGRESSION_PI_LIST, reg_state, MODELS)
        dialog.v_model = False
        widget.disabled = False
        widget.loading = False
        new_log(f"Saved at: {file_path}", True)
        save_as_btn.color = "green"
        time.sleep(0.5)
        save_as_btn.color = "default"
    else:
        save_as_tf.error_messages = "please specify a file name"


def save_plots(widget, event, data):
    try:
        spl.save_all_plots(WORKDIR)
        new_log(f"All plots saved at: {WORKDIR}", True)
        widget.color = "green"
        time.sleep(1)
        widget.color = "default"
    except FileNotFoundError:
        new_log(f"No plots to save", False)
        widget.color = "red"
        time.sleep(1)
        widget.color = "default"


def load(widget, event, data):
    """
    Returns Shows the load dialog
    -------

    """
    global WORKDIR
    fc_load.default_path = WORKDIR
    dialog2.v_model = True


def hide_ld(chooser):
    """
    Parameters
    ----------
    widget The OK button in the save dialog

    Returns Loads a .txt file and modifies the state of all widgets accordingly, hides the load dialog
    -------

    """
    file_path = fc_load.selected
    if file_path:
        global OLD_PHYSICAL_PARAMS, PHYSICAL_PARAMS, OUTPUTS, PI_SETS, CHOSEN_PI_SET, PI_LISTS, CHOSEN_PI_LIST,\
            RESULT_DF, RESULT_PI, DEPENDENCY_CHECK_STATE, REGRESSION_PI_LIST, MODELS

        try:
            load_tuple = sl.load(file_path)
        except FileNotFoundError:
            fc_load.reset()
            dialog2.v_model = False
            new_log(f"Failed to load, file does not exist", False)
            load_btn.color = "red"
            time.sleep(0.5)
            load_btn.color = "default"
            return -1
        if len(load_tuple) != 20:
            fc_load.reset()
            dialog2.v_model = False
            new_log(f"Failed to load, invalid file", False)
            load_btn.color = "red"
            time.sleep(0.5)
            load_btn.color = "default"
            return -1

        dialog2.v_model = False
        fc_load.reset()
        load_btn.color = "green"
        new_log(f"Loaded: {file_path}", True)

        sheet.items = load_tuple[0]
        buck_area.v_model = load_tuple[1]
        force_area.v_model = load_tuple[2]
        auto_buck_table.items = load_tuple[3]
        tab2_state = load_tuple[4]
        PHYSICAL_PARAMS = load_tuple[5]
        OLD_PHYSICAL_PARAMS = load_tuple[5]
        OUTPUTS = load_tuple[6]
        PI_SETS = load_tuple[7]
        CHOSEN_PI_SET = load_tuple[8]
        PI_LISTS = load_tuple[9]
        CHOSEN_PI_LIST = load_tuple[10]
        update_current_set()
        check1.v_model = tab2_state[0]
        check2.v_model = tab2_state[1]
        check3.v_model = tab2_state[2]
        if tab2_state[3]:
            force_area.error_messages = ""
            force_area.success_messages = ""
            check2.disabled = True
            check2.v_model = False
            force_area.readonly = False
            force_area.clearable = True
            force_area.background_color = "white"
            force_eq.disabled = False
            force_eq.background_color = "white"
            add_pi_btn.disabled = False
            if auto_buck_table.v_model:
                force_copy_btn.disabled = False
            force_buck_btn.children = [TL[11]]
        else:
            force_area.error_messages = ""
            force_area.success_messages = TL[18]
            check2.disabled = False
            force_area.readonly = True
            force_area.clearable = False
            force_area.background_color = "grey lighten-3"
            force_eq.disabled = True
            force_eq.v_model = ""
            force_eq.background_color = "grey lighten-3"
            add_pi_btn.disabled = True
            force_copy_btn.disabled = True
            force_buck_btn.children = [TL[14]]
        if tab2_state[4] == 0:
            check3.disabled = True
        else:
            check3.disabled = False
            setattr(auto_buck_table, 'v_model', [auto_buck_table.items[tab2_state[4] - 1]])

        anticipated_mo_entry.v_model = load_tuple[12][2]
        change_tab_3()
        phy_const_area.v_model = load_tuple[11][0]
        pi_const_area.v_model = load_tuple[11][1]
        select_DOE.v_model = load_tuple[12][0]
        select_log.v_model = load_tuple[12][1]

        does = load_tuple[13]

        if does:
            doeX, doePi, doePi_all, doePi_nearest, doePi_all_obj, doePI_active = does
            reduced_parameter_set, reduced_pi_set = PHYSICAL_PARAMS, CHOSEN_PI_SET
            for out in list(PHYSICAL_PARAMS.dictionary.keys())[-OUTPUTS:]:
                reduced_parameter_set, reduced_pi_set = vpl.reduce_parameter_set(reduced_parameter_set,
                                                                                 reduced_pi_set,
                                                                                 elected_output=out)
            init_doe_plots(doeX, reduced_parameter_set, doePi, doePi_all, doePi_nearest, doePi_all_obj, doePI_active,
                           reduced_pi_set)
            if len(doe_box.children) == 3:
                doe_box.children = list(doe_box.children) + [exp_panel_doe]

        result_headers, result_items = load_tuple[14]
        result_data.headers = csv.format_headers(result_headers)
        result_data.items = result_items

        if result_items:
            RESULT_DF = pd.DataFrame(result_items)
            func_x_to_pi = vpl.declare_func_x_to_pi(PHYSICAL_PARAMS, CHOSEN_PI_SET)
            ordered_columns = []
            for key in PHYSICAL_PARAMS.dictionary:
                ordered_columns.append(f"{key} [{PHYSICAL_PARAMS.dictionary[key].defined_units}]")
            re_ordered_result = RESULT_DF[ordered_columns]
            RESULT_PI = func_x_to_pi(re_ordered_result.to_numpy(dtype=float))
            threshold_slider.v_model = load_tuple[15]
            DEPENDENCY_CHECK_STATE = load_tuple[16]
            REGRESSION_PI_LIST = load_tuple[17]

        reg_state = load_tuple[18]
        if reg_state:
            select_pi0.v_model = reg_state[0]
            select_reg_criteria.v_model = reg_state[1]
            model_order_entry.v_model = int(reg_state[2])

        MODELS = load_tuple[19]
        if MODELS:
            regression_models(models_btn, 0, 0, slider_state=int(reg_state[3]))

        if tabs.v_model == 5:
            change_tab_5()
        if tabs.v_model == 6:
            change_tab_6()
        time.sleep(0.5)
        load_btn.color = "default"
    else:
        dialog2.v_model = False

# --------- Buckingham Tab Functions -----------------------------------------------------------------------------------


def add_pi(widget, event, data):
    """
    Returns Adds the pi number specified in force_eq to force_area
    -------

    """
    index = pif.get_pi_index(force_area.v_model)
    if force_eq.v_model is None or force_eq.v_model == "":
        force_eq.error_messages = TL[21]
    else:
        exp = pif.format_input(force_eq.v_model, index)
        if force_area.v_model is not None:
            force_area.v_model += exp + "\n"
        else:
            force_area.v_model = exp + "\n"
        force_eq.v_model = ""


def tab2_reload():
    global CHOSEN_PI_SET, CHOSEN_PI_LIST, PI_SETS, PI_LISTS
    CHOSEN_PI_SET = None
    PI_SETS = [None, None, []]
    CHOSEN_PI_LIST = []
    PI_LISTS = [[], [], []]
    update_current_set()
    buck_area.v_model = ""
    check1.v_model = True
    force_buck_btn.disabled = False
    force_buck_btn.children = [TL[11]]
    force_eq.v_model = ""
    force_eq.error_messages = ""
    force_area.v_model = ""
    force_area.success_messages = ""
    force_area.error_messages = ""
    force_area.readonly = False
    force_area.clearable = True
    add_pi_btn.disabled = False
    force_copy_btn.disabled = False
    check2.disabled = True
    check2.v_model = False
    auto_buck_btn.disabled = False
    auto_buck_table.items = []
    check3.disabled = True
    check3.v_model = False


def tab2_disable():
    force_buck_btn.disabled = True
    auto_buck_btn.disabled = True
    check1.disabled = True
    check1.v_model = False


def tab2_enable():
    force_buck_btn.disabled = False
    auto_buck_btn.disabled = False
    check1.disabled = False


# -----DOE Tab functions------------------------------------------------------------------------------------------------


def add_phy_const(widget, event, data):
    phy_const_entry.error_messages = ""
    if phy_const_entry.v_model is None or phy_const_entry.v_model == "":
        phy_const_entry.error_messages = TL[21]
    else:
        exp = phy_const_entry.v_model
        if phy_const_area.v_model is not None:
            phy_const_area.v_model += exp + "\n"
        else:
            phy_const_area.v_model = exp + "\n"
        phy_const_entry.v_model = ""


def add_pi_const(widget, event, data):
    pi_const_entry.error_messages = ""
    if pi_const_entry.v_model is None or pi_const_entry.v_model == "":
        pi_const_entry.error_messages = TL[21]
    else:
        exp = pi_const_entry.v_model
        if pi_const_area.v_model is not None:
            pi_const_area.v_model += exp + "\n"
        else:
            pi_const_area.v_model = exp + "\n"
        pi_const_entry.v_model = ""


def nb_of_terms():
    n = int(anticipated_mo_entry.v_model)
    p = len(CHOSEN_PI_LIST) - 1
    return noc.coefficient_nb(n, p, approx=(p >= 2*n and n > 10))


def mo_to_size(widget, event, data):
    nb_terms = nb_of_terms()
    wished_size_entry.v_model = DOE_MULTIPLIER * nb_terms
    model_order_entry.v_model = widget.v_model


def check_size(widget, event, data):
    expected = DOE_MULTIPLIER * nb_of_terms()
    if int(widget.v_model) > int(2*expected) or int(widget.v_model) < int(0.5*expected):
        widget.messages = "Warning: size not advised for model order"
        anticipated_mo_entry.messages = "Warning: size not advised for model order"
    else:
        widget.messages = ""
        anticipated_mo_entry.messages = ""


def gen_doe(widget, event, data):
    global WORKDIR
    dialog3.v_model = True
    dialog3.children[0].children[1].children = ["Current work directory: " + WORKDIR]
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%y_%H-%M-%S")
    doe_tf.v_model = "pyVPLM_" + dt_string


def customize_2d_plot(widget, event, data):
    global AX, TOTAL_DOE
    new_df = TOTAL_DOE
    i = 0
    for col in new_df:
        [col_min, col_max] = range_sliders.children[2*i + 1].v_model
        new_df = new_df[(new_df[col] >= col_min) & (new_df[col] <= col_max)]
        i += 1
    with customizable_2d_plot_output:
        clear_output(wait=True)
        AX.clear()
        AX.set_xlabel(select_2d_x.v_model)
        AX.set_ylabel(select_2d_y.v_model)
        AX.plot(new_df[select_2d_x.v_model], new_df[select_2d_y.v_model], 'o')
        display(AX.figure)


def init_doe_plots(doeX, parameter_set, doePi, doePi_all, doePi_nearest, doePi_all_obj, doePI_active, pi_set, log=True):
    spl.add_temp(WORKDIR)
    _, _, ww, _ = GetWindowRect(GetForegroundWindow())
    error = False
    if log:
        doeX = np.log10(doeX)
        doePi = np.log10(doePi)
        doePi_all = np.log10(doePi_all)
        doePi_nearest = np.log10(doePi_nearest)
        doePi_all_obj = np.log10(doePi_all_obj)
        doePI_active = np.log10(doePI_active)
    columns = []
    constants = []
    for key in parameter_set.dictionary:
        if log:
            column_name = f"log10({key}) [{parameter_set.dictionary[key].defined_units}]"
        else:
            column_name = f"{key} [{parameter_set.dictionary[key].defined_units}]"
        columns.append(column_name)
        if len(parameter_set.dictionary[key].defined_bounds) == 0:
            constants.append(column_name)

    df = pd.DataFrame(data=doeX, columns=columns)
    df = df.drop(labels=constants, axis=1)

    phy_scatter_matrix_output.clear_output()
    with phy_scatter_matrix_output:
        try:
            plt.rcParams['axes.labelsize'] = 14
            sm1 = scatter_matrix(df, figsize=(30*ww/1928, 30*ww/1928), alpha=0.9, diagonal="kde")
            for i in range(np.shape(sm1)[0]):
                for j in range(np.shape(sm1)[1]):
                    if i < j:
                        sm1[i, j].set_visible(False)
            plt.savefig(WORKDIR + "\\temp\\phy_scatter_matrix.pdf")
            plt.show()
        except ValueError:
            error = True
    columns_2 = []
    for key in pi_set.dictionary:
        if log:
            columns_2.append("log10(" + key + ")")
        else:
            columns_2.append(key)
    df_2 = pd.DataFrame(data=doePi, columns=columns_2)
    constant_pi = cpi.get_constant_pi(df_2)
    df_2 = df_2.drop(labels=constant_pi, axis=1)

    df_2_1 = pd.DataFrame(data=doePi_all, columns=columns_2)
    df_2_1 = df_2_1.drop(labels=constant_pi, axis=1)

    df_2_2 = pd.DataFrame(data=doePi_nearest, columns=columns_2)
    df_2_2 = df_2_2.drop(labels=constant_pi, axis=1)

    df_2_3 = pd.DataFrame(data=doePI_active, columns=columns_2)
    df_2_3 = df_2_3.drop(labels=constant_pi, axis=1)

    df_2_4 = pd.DataFrame(data=doePi_all_obj, columns=columns_2)
    df_2_4 = df_2_4.drop(labels=constant_pi, axis=1)

    df_2_f = pd.concat([df_2, df_2_1, df_2_2, df_2_3, df_2_4], ignore_index=True)
    lab0 = "Elected (Feas.)"
    lab1 = "All (Feas.)"
    lab2 = "3 Nearest (Feas.)"
    lab3 = "Active (Obj.)"
    lab4 = "All (Obj.)"
    df_2_f["DOE points"] = [lab0]*len(df_2) + [lab1]*len(df_2_1) + [lab2]*len(df_2_2) + [lab3]*len(df_2_3) + \
                           [lab4]*len(df_2_4)

    pi_scatter_matrix_output.clear_output()
    with pi_scatter_matrix_output:
        try:
            pass
        except ValueError:
            error = True
        palette = {lab0: "blue", lab1: "green", lab2: "cyan", lab3: "red", lab4: "black"}
        sns.pairplot(df_2_f, hue="DOE points", hue_order=[lab3, lab0, lab2, lab1, lab4], palette=palette, corner=True,
                     height=7*ww/1928, markers=["D", ".", ".", "s", "."], diag_kind="kde")
        plt.savefig(WORKDIR + "\\temp\\pi_scatter_matrix.pdf")
        plt.show()

    if error:
        raise ValueError

    df_3 = pd.concat([df, df_2], axis=1)

    df_3_col_list = list(df_3.columns)
    select_2d_x.items = df_3_col_list
    select_2d_x.v_model = df_3_col_list[0]
    select_2d_y.items = df_3_col_list
    select_2d_y.v_model = df_3_col_list[1]

    range_slider_card.width = ww * 600 / 1928
    range_slider_card.height = ww * 580 / 1928
    range_sliders.children = []
    for col_name in df_3_col_list:
        col_min = rmm.round_min(df_3[col_name].min())
        col_max = rmm.round_max(df_3[col_name].max())
        act_min = col_min - 0.1*abs(col_min)
        act_max = col_max + 0.1*abs(col_max)
        step = round((act_max - act_min) / 100, 2)
        range_sliders.children = range_sliders.children + [v.Subheader(children=[col_name], class_="justify-center"),
                                                           v.RangeSlider(min=act_min,
                                                                         max=act_max,
                                                                         v_model=[act_min, act_max],
                                                                         step=step,
                                                                         thumb_label="always")]
        for i in range(len(range_sliders.children)):
            if i % 2 == 1:
                range_sliders.children[i].on_event("change", customize_2d_plot)

    customizable_2d_plot_output.clear_output()
    with customizable_2d_plot_output:
        global AX
        AX.clear()
        AX.set_xlabel(select_2d_x.v_model)
        AX.set_ylabel(select_2d_y.v_model)
        AX.plot(df_3[select_2d_x.v_model], df_3[select_2d_y.v_model], 'o')
        FIG.set(size_inches=(10*ww/1928, 10*ww/1928))
        FIG.savefig(WORKDIR + "\\temp\\customizable_2D_plot.pdf")
        display(AX.figure)

    fig = go.FigureWidget()
    fig.layout.width = ww - 300 if ww - 300 > 200 else 200
    fig.layout.height = 800
    parcoords_labels = {}
    if len(df_3.columns) < 5:
        for col_name in df_3.columns:
            parcoords_labels[col_name] = col_name
    else:
        for col_name in df_3.columns:
            parcoords_labels[col_name] = col_name.split("[")[0]
    fig.add_parcoords(dimensions=[{'label': parcoords_labels[n], 'values': df_3[n]} for n in df_3.columns])
    parallel_plot_box.children = [fig]
    fig.write_image(WORKDIR + "\\temp\\parallel_plot.pdf")

    global TOTAL_DOE
    TOTAL_DOE = df_3


# noinspection PyTypeChecker,
# PyUnresolvedReferences
def hide_doe(widget, event, data):
    widget.disabled = True
    widget.loading = True
    gen_DOE_btn.disabled = True
    gen_DOE_btn.loading = True
    doe_tf.error_messages = ""
    if doe_tf.v_model.strip():
        phy_save_btn.disabled = True
        pi_save_btn.disabled = True
        cus_save_btn.disabled = True
        para_save_btn.disabled = True
        file_name = WORKDIR + "\\" + doe_tf.v_model + ".csv"
        valid_input = True
        if PHYSICAL_PARAMS is None or CHOSEN_PI_SET is None:
            valid_input = False
        if file_name and valid_input:
            reduced_parameter_set, reduced_pi_set = PHYSICAL_PARAMS, CHOSEN_PI_SET
            out_headers = []
            for out in list(PHYSICAL_PARAMS.dictionary.keys())[-OUTPUTS:]:
                reduced_parameter_set, reduced_pi_set = vpl.reduce_parameter_set(reduced_parameter_set,
                                                                                 reduced_pi_set,
                                                                                 elected_output=out)
                out_headers.append(out + " [" + PHYSICAL_PARAMS.dictionary[out].defined_units + "]")
            func_x_to_pi = vpl.declare_func_x_to_pi(reduced_parameter_set, reduced_pi_set)
            try:
                parameter_constraints = vpl.declare_constraints(reduced_parameter_set,
                                                                csf.str_to_constraint_set(phy_const_area.v_model))
            except (ValueError, SyntaxError):
                phy_const_area.error_messages = "Invalid constraints"
                widget.disabled = False
                widget.loading = False
                gen_DOE_btn.disabled = False
                gen_DOE_btn.loading = False
                dialog3.v_model = False
                return -1
            try:
                pi_constraints = vpl.declare_constraints(reduced_pi_set, csf.str_to_constraint_set(pi_const_area.v_model))
            except (ValueError, SyntaxError):
                pi_const_area.error_messages = "Invalid constraints"
                widget.disabled = False
                widget.loading = False
                dialog3.v_model = False
                gen_DOE_btn.disabled = False
                gen_DOE_btn.loading = False
                return -1
            out_tuple = doe.create_const_doe(reduced_parameter_set, reduced_pi_set, func_x_to_pi,
                                             parameters_constraints=parameter_constraints,
                                             pi_constraints=pi_constraints,
                                             whished_size=int(wished_size_entry.v_model),
                                             test_mode=True,
                                             log_space=(select_log.v_model == "Log"))
            doeX, doePi, doePi_all, doePi_nearest, doePi_all_obj, doePI_active = out_tuple
            global DOE
            DOE = [doeX, doePi, doePi_all, doePi_nearest, doePi_all_obj, doePI_active]
            csv.generate_csv(doeX, file_name, reduced_parameter_set, out_headers)
            if len(doe_box.children) == 3:
                doe_box.children = list(doe_box.children) + [exp_panel_doe]
            widget.disabled = False
            widget.loading = False
            gen_DOE_btn.disabled = False
            gen_DOE_btn.loading = False
            dialog3.v_model = False
            try:
                init_doe_plots(doeX, reduced_parameter_set, doePi, doePi_all, doePi_nearest, doePi_all_obj,
                               doePI_active, reduced_pi_set, log=(select_log.v_model == "Log"))
                phy_save_btn.disabled = False
                pi_save_btn.disabled = False
                cus_save_btn.disabled = False
                para_save_btn.disabled = False

            except ValueError:
                if len(doe_box.children) > 3:
                    doe_box.children = list(doe_box.children[:-1])
                phy_const_area.error_messages = "Constraints are too restrictive"
                pi_const_area.error_messages = "Constraints are too restrictive"
    else:
        doe_tf.error_messages = "Please specify a file name"
        widget.disabled = False
        widget.loading = False
        gen_DOE_btn.disabled = False
        gen_DOE_btn.loading = False


def save_phy(widget, event, data):
    try:
        new_name = spl.save_single_plot(WORKDIR, "phy_scatter_matrix.pdf")
    except FileNotFoundError:
        new_log(f"Failed to save (plot may already be saved)", False)
        widget.color = "red"
        time.sleep(1)
        widget.color = "default"
    else:
        new_log(f"Saved plot as: {new_name}", True)
        widget.color = "green"
        time.sleep(1)
        widget.color = "default"


def save_pi(widget, event, data):
    try:
        new_name = spl.save_single_plot(WORKDIR, "pi_scatter_matrix.pdf")
    except FileNotFoundError:
        new_log(f"Failed to save (plot may already be saved)", False)
        widget.color = "red"
        time.sleep(1)
        widget.color = "default"
    else:
        new_log(f"Saved plot as: {new_name}", True)
        widget.color = "green"
        time.sleep(1)
        widget.color = "default"


def save_cus(widget, event, data):
    try:
        new_name = spl.save_single_plot(WORKDIR, "customizable_2D_plot.pdf")
    except FileNotFoundError:
        new_log(f"Failed to save (plot may already be saved)", False)
        widget.color = "red"
        time.sleep(1)
        widget.color = "default"
    else:
        new_log(f"Saved plot as: {new_name}", True)
        widget.color = "green"
        time.sleep(1)
        widget.color = "default"


def save_para(widget, event, data):
    try:
        new_name = spl.save_single_plot(WORKDIR, "parallel_plot.pdf")
    except FileNotFoundError:
        new_log(f"Failed to save (plot may already be saved)", False)
        widget.color = "red"
        time.sleep(1)
        widget.color = "default"
    else:
        new_log(f"Saved plot as: {new_name}", True)
        widget.color = "green"
        time.sleep(1)
        widget.color = "default"


def tab3_reload():
    doe_alert_cont.children = []
    input_pi.children[1].children = [""]
    output_pi.children[1].children = [""]
    phy_const_entry.v_model = ""
    phy_const_area.v_model = ""
    pi_const_entry.v_model = ""
    pi_const_area.v_model = ""
    select_DOE.v_model = "Full Fact"
    anticipated_mo_entry.v_model = 1
    wished_size_entry.v_model = 40


def tab3_disable():
    phy_const_entry.disabled = True
    phy_const_btn.disabled = True
    phy_const_area.disabled = True
    pi_const_entry.disabled = True
    pi_const_btn.disabled = True
    pi_const_area.disabled = True
    select_DOE.disabled = True
    anticipated_mo_entry.disabled = True
    wished_size_entry.disabled = True
    gen_DOE_btn.disabled = True


def tab3_enable():
    phy_const_entry.disabled = False
    phy_const_btn.disabled = False
    phy_const_area.disabled = False
    pi_const_entry.disabled = False
    pi_const_btn.disabled = False
    pi_const_area.disabled = False
    select_DOE.disabled = False
    anticipated_mo_entry.disabled = False
    wished_size_entry.disabled = False
    gen_DOE_btn.disabled = False

# -----Result import Tab functions--------------------------------------------------------------------------------------


def gen_empty_csv(widget, event, data):
    global WORKDIR
    dialog5.v_model = True
    dialog5.children[0].children[1].children = ["Current work directory: " + WORKDIR]
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%y_%H-%M-%S")
    empty_tf.v_model = "pyVPLM_empty_" + dt_string


def hide_empty_csv(widget, event, data):
    widget.disabled = True
    widget.loading = True
    empty_csv_btn.disabled = True
    empty_csv_btn.loading = True
    empty_tf.error_messages = ""
    global PHYSICAL_PARAMS, RESULT_DF, RESULT_PI, CHOSEN_PI_SET, WORKDIR
    path = WORKDIR + "\\" + empty_tf.v_model + ".csv"
    if empty_tf.v_model.strip():
        try:
            reduced_parameter_set = copy.deepcopy(PHYSICAL_PARAMS)
            out_headers = []
            for out in list(PHYSICAL_PARAMS.dictionary.keys())[-OUTPUTS:]:
                del reduced_parameter_set.dictionary[out]
                out_headers.append(out + " [" + PHYSICAL_PARAMS.dictionary[out].defined_units + "]")
            csv.generate_csv(np.array([]), path, reduced_parameter_set, out_headers)
        except Exception as e:
            result_alert.children = [str(e)]
            result_alert_cont.children = [result_alert]
        widget.disabled = False
        widget.loading = False
        empty_csv_btn.loading = False
        empty_csv_btn.disabled = False
        dialog5.v_model = False
        empty_csv_btn.children = ["Empty csv generated"]
        empty_csv_btn.color = "grey lighten-2"
        time.sleep(1.5)
        empty_csv_btn.children = ["Generate empty csv"]
        empty_csv_btn.color = "grey lighten-4"
    else:
        empty_tf.error_messages = "Please specify a file name"
        widget.disabled = False
        widget.loading = False
        empty_csv_btn.loading = False
        empty_csv_btn.disabled = False


def result_import(widget, event, data):
    dialog4.v_model = True
    fc_res.default_path = WORKDIR


def hide_res_import():
    result_btn.disabled = True
    result_btn.loading = True
    global PHYSICAL_PARAMS, RESULT_DF, RESULT_PI, CHOSEN_PI_SET, DEPENDENCY_CHECK_STATE
    path = fc_res.selected
    if path:
        try:
            headers, items, RESULT_DF = csv.read_csv(path, PHYSICAL_PARAMS, round_=True)
            result_data.headers = headers
            result_data.items = items
            result_alert_cont.children = []
            if CHOSEN_PI_SET:
                func_x_to_pi = vpl.declare_func_x_to_pi(PHYSICAL_PARAMS, CHOSEN_PI_SET)
                ordered_columns = []
                for key in PHYSICAL_PARAMS.dictionary:
                    ordered_columns.append(f"{key} [{PHYSICAL_PARAMS.dictionary[key].defined_units}]")
                re_ordered_result = RESULT_DF[ordered_columns]
                RESULT_PI = func_x_to_pi(re_ordered_result.to_numpy(dtype=float))
                DEPENDENCY_CHECK_STATE = []
                select_pi0.v_model = ""
        except Exception as e:
            result_alert.children = [str(e)]
            result_alert_cont.children = [result_alert]
    result_btn.disabled = False
    result_btn.loading = False
    dialog4.v_model = False

# -----Dependency Tab functions-----------------------------------------------------------------------------------------


def input_output_lists():
    global OUTPUTS, CHOSEN_PI_LIST, PHYSICAL_PARAMS, DOE_PI_LIST
    if CHOSEN_PI_LIST:
        if OUTPUTS == 0:
            raise ValueError("No output pi")
        else:
            output_index = pif.output_pi_index(CHOSEN_PI_LIST, PHYSICAL_PARAMS, OUTPUTS)
            output_list = [CHOSEN_PI_LIST[i] for i in output_index]
            input_list = CHOSEN_PI_LIST.copy()
            input_index = [i for i in range(0, len(CHOSEN_PI_LIST))]
            for i in range(len(output_list)):
                input_list.remove(output_list[i])
            for ind in output_index:
                input_index.remove(ind)
            input_pi_names = []
            output_pi_names = []
            for index in input_index:
                input_pi_names.append("pi" + str(index + 1))
            for index in output_index:
                output_pi_names.append("pi" + str(index + 1))
            return input_pi_names, output_pi_names
    else:
        raise ValueError("No chosen pi set")


def dependency_check(widget, event, data):
    global REGRESSION_PI_LIST, DEPENDENCY_CHECK_STATE
    index = int(widget.label[-1]) - 1
    if data:
        REGRESSION_PI_LIST[index] = CHOSEN_PI_LIST[index]
        DEPENDENCY_CHECK_STATE[index] = True
    else:
        REGRESSION_PI_LIST[index] = None
        DEPENDENCY_CHECK_STATE[index] = False
    dependency_set.color = "green lighten-3"
    dependency_set.children[0].children = ["Current pi set:"]
    dependency_set.children[1].children = pi_set_html(pif.pi_list_to_str(REGRESSION_PI_LIST))
    toggle_dependency_check()


def update_dependency_check():
    global REGRESSION_PI_LIST, DEPENDENCY_CHECK_STATE
    for index in range(len(DEPENDENCY_CHECK_STATE)):
        if DEPENDENCY_CHECK_STATE[index]:
            REGRESSION_PI_LIST[index] = CHOSEN_PI_LIST[index]
        else:
            REGRESSION_PI_LIST[index] = None
    dependency_set.color = "green lighten-3"
    dependency_set.children[0].children = ["Current pi set:"]
    dependency_set.children[1].children = pi_set_html(pif.pi_list_to_str(REGRESSION_PI_LIST))
    toggle_dependency_check()


def toggle_dependency_check():
    piN, pi0 = input_output_lists()
    inp_index = []
    for pi_n in piN:
        inp_index.append(int(pi_n.replace("pi", "")) - 1)
    out_index = []
    for pi_n in pi0:
        out_index.append(int(pi_n.replace("pi", "")) - 1)
    nb_inputs = 0
    for i in inp_index:
        if DEPENDENCY_CHECK_STATE[i]:
            nb_inputs += 1
    nb_outputs = 0
    for i in out_index:
        if DEPENDENCY_CHECK_STATE[i]:
            nb_outputs += 1
    if nb_inputs == 1:
        for i in inp_index:
            if DEPENDENCY_CHECK_STATE[i]:
                dependency_checkboxes.children[i].disabled = True
    else:
        for i in inp_index:
            dependency_checkboxes.children[i].disabled = False
    if nb_outputs == 1:
        for i in out_index:
            if DEPENDENCY_CHECK_STATE[i]:
                dependency_checkboxes.children[i].disabled = True
    else:
        for i in out_index:
            dependency_checkboxes.children[i].disabled = False


def update_dependency_plots(widget, event, data):
    widget.disabled = True
    widget.loading = True
    sen_save_btn.disabled = True
    dep_save_btn.disabled = True
    piN, pi0 = input_output_lists()
    for i in range(len(DEPENDENCY_CHECK_STATE)):
        if not DEPENDENCY_CHECK_STATE[i]:
            pi_n = f"pi{i + 1}"
            if pi_n in piN:
                piN.remove(pi_n)
            elif pi_n in pi0:
                pi0.remove(pi_n)
    sensitivity_output.clear_output(wait=True)
    with sensitivity_output:
        dpp.pi_sensitivity_plot(CHOSEN_PI_SET, RESULT_PI, WORKDIR, pi0=pi0, piN=piN, latex=True)
    dependency_output.clear_output(wait=True)
    with dependency_output:
        dpp.pi_dependency_plot(CHOSEN_PI_SET, RESULT_PI, WORKDIR, x_list=piN, y_list=piN, latex=True,
                               threshold=threshold_slider.v_model)
    widget.disabled = False
    widget.loading = False
    sen_save_btn.disabled = False
    dep_save_btn.disabled = False


def change_threshold(widget, event, data):
    widget.loading = True
    dep_save_btn.disabled = True
    piN, _ = input_output_lists()
    for i in range(len(DEPENDENCY_CHECK_STATE)):
        if not DEPENDENCY_CHECK_STATE[i]:
            pi_n = f"pi{i + 1}"
            if pi_n in piN:
                piN.remove(pi_n)
    dependency_output.clear_output(wait=True)
    with dependency_output:
        dpp.pi_dependency_plot(CHOSEN_PI_SET, RESULT_PI, WORKDIR, x_list=piN, y_list=piN, latex=True,
                               threshold=widget.v_model)
    widget.loading = False
    dep_save_btn.disabled = False


def save_sen(widget, event, data):
    try:
        new_name = spl.save_single_plot(WORKDIR, "sensitivity_plot.pdf")
    except FileNotFoundError:
        new_log(f"Failed to save (plot may already be saved)", False)
        widget.color = "red"
        time.sleep(1)
        widget.color = "default"
    else:
        new_log(f"Saved plot as: {new_name}", True)
        widget.color = "green"
        time.sleep(1)
        widget.color = "default"


def save_dep(widget, event, data):
    try:
        new_name = spl.save_single_plot(WORKDIR, "dependency_plot.pdf")
    except FileNotFoundError:
        new_log(f"Failed to save (plot may already be saved)", False)
        widget.color = "red"
        time.sleep(1)
        widget.color = "default"
    else:
        new_log(f"Saved plot as: {new_name}", True)
        widget.color = "green"
        time.sleep(1)
        widget.color = "default"

# -----Regression Tab functions-----------------------------------------------------------------------------------------


def tab6_enable():
    select_pi0.disabled = False
    model_order_entry.disabled = False
    select_reg_criteria.disabled = False
    models_btn.disabled = False
    nb_terms_slider.disabled = False


def tab6_disable():
    select_pi0.disabled = True
    model_order_entry.disabled = True
    select_reg_criteria.disabled = True
    models_btn.disabled = True
    nb_terms_slider.disabled = True


def slider_tick_labels(max_nb):
    tick_labels = list(range(1, max_nb + 1))
    if max_nb > 50:
        visible_labels = [1]
        for i in range(1, 11):
            visible_labels.append(round(i*(max_nb - 1)/10 + 1))
        for i in range(0, max_nb):
            if i + 1 not in visible_labels:
                tick_labels[i] = ""
    return tick_labels


def regression_models(widget, event, data, slider_state=1):
    spl.add_temp(WORKDIR)
    widget.disabled = True
    widget.loading = True
    models_save_btn.disabled = True
    nb_terms_slider.disabled = True
    model_order_entry.error_messages = ""
    model_order = int(float(model_order_entry.v_model))
    if model_order < 1:
        model_order_entry.error_messages = "Model order should be >= 1"
        widget.disabled = False
        widget.loading = False
        nb_terms_slider.disabled = False
        return -1
    global MODELS, RESULT_PI, REGRESSIONS, PI0_PI_LIST
    modified_result_pi = RESULT_PI
    selected_pi0 = int(select_pi0.v_model[2:])
    max_pi_nb = np.shape(RESULT_PI)[1]
    list_to_del = []
    _, output_pi_names = input_output_lists()
    for pi_name in output_pi_names:
        index = int(pi_name[2:]) - 1
        if index != selected_pi0 - 1:
            list_to_del.append(index)
    if DEPENDENCY_CHECK_STATE:
        for i in range(len(DEPENDENCY_CHECK_STATE)):
            if not DEPENDENCY_CHECK_STATE[i] and i not in list_to_del:
                list_to_del.append(i)
    modified_result_pi = np.delete(modified_result_pi, list_to_del, 1)
    actual_pi0 = selected_pi0 - 1
    for i in list_to_del:
        if i < selected_pi0 - 1:
            actual_pi0 -= 1
    eff_pi0 = actual_pi0 + 1
    pi_list = []
    for i in range(0, max_pi_nb):
        if i not in list_to_del:
            pi_list.append(f"pi{i + 1}")
    PI0_PI_LIST = [eff_pi0 - 1, pi_list]

    criteria = select_reg_criteria.v_model
    if criteria == "max(error)":
        choice = 1
    elif criteria == "avg(error magnitude)":
        choice = 2
    elif criteria == "avg(error)":
        choice = 3
    else:
        choice = 4
    if not RESULT_DF.empty:
        models_output.clear_output(wait=True)
        _, _, ww, _ = GetWindowRect(GetForegroundWindow())
        with models_output:
            warnings.filterwarnings("ignore")
            MODELS, axs, fig = vpl.regression_models(modified_result_pi, elected_pi0=select_pi0.v_model,
                                                     order=model_order, test_mode=True, plots=True,
                                                     force_choice=choice, ymax_axis=1000, removed_pi=list_to_del,
                                                     eff_pi0=eff_pi0, skip_cross_validation=True, return_axes=True,
                                                     fig_size=(29*ww/1928, 12*ww/1928))
            max_nb_terms = len(MODELS.keys()) - 4
            fig_width, _ = fig.get_size_inches()*fig.dpi
            omicron = 0.001 * max_nb_terms
            if slider_state >= max_nb_terms:
                slider_state = 1
            for i in range(len(axs)):
                ax = axs[i]
                err_train = "NaN"
                err_test = "NaN"
                if i == 0:
                    err_train = round(MODELS["max |e|"][0][slider_state], 1)
                    err_test = round(MODELS["max |e|"][1][slider_state], 1)
                elif i == 1:
                    err_train = round(MODELS["ave. |e|"][0][slider_state], 1)
                    err_test = round(MODELS["ave. |e|"][1][slider_state], 1)
                elif i == 2:
                    err_train = round(MODELS["ave. e"][0][slider_state], 1)
                    err_test = round(MODELS["ave. e"][1][slider_state], 1)
                elif i == 3:
                    err_train = round(MODELS["sigma e"][0][slider_state], 1)
                    err_test = round(MODELS["sigma e"][1][slider_state], 1)
                y_max = ax.get_ylim()[1]
                if slider_state == 0:
                    ax.axvline(1 + omicron, color="blue")
                    ax.text(1 + 10*omicron, 3*y_max/8, str(err_train), fontdict={"fontsize": "large",
                                                                      "fontfamily": "sans-serif"})
                    if err_test != 0:
                        ax.text(1 + 10*omicron, 5*y_max/8, str(err_test), color="red",
                                fontdict={"fontsize": "large", "fontfamily": "sans-serif"})
                else:
                    ax.axvline(slider_state + 1, color="blue")
                    ax.text(slider_state + 1 + 10*omicron, 3*y_max/8, str(err_train),
                            fontdict={"fontsize": "large", "fontfamily": "serif"})
                    if err_test != 0:
                        ax.text(slider_state + 1 + 10*omicron, 5*y_max/8, str(err_test), color="red",
                                fontdict={"fontsize": "large", "fontfamily": "sans-serif"})
            fig.savefig(os.path.join(WORKDIR, "temp\\regression_models_plot.pdf"))
            plt.show()
        REGRESSIONS = []
        for i in range(max_nb_terms):
            expression, expression_latex, y, y_reg = vpl.perform_regression(modified_result_pi, MODELS,
                                                                            chosen_model=i + 1,
                                                                            latex=True, pi_list=pi_list,
                                                                            max_pi_nb=max_pi_nb,
                                                                            removed_pi=list_to_del,
                                                                            eff_pi0=eff_pi0, test_mode=True,
                                                                            no_plots=True)
            REGRESSIONS.append({"expr": expression, "expr_latex": expression_latex, "Y": y, "Y_reg": y_reg})
        nb_terms_slider.tick_labels = slider_tick_labels(max_nb_terms)
        nb_terms_slider.max = max_nb_terms - 1
        if len(regression_cont.children) == 3:
            regression_cont.children = regression_cont.children + [models_output_col, nb_terms_slider_row,
                                                                   save_reg_cont, regression_output]
        nb_terms_slider.v_model = slider_state
        slider_margin_right = 118*ww/1928
        nb_terms_slider.style_ = f"margin : 0px {slider_margin_right}px 0px 56px"
        perform_regression(nb_terms_slider, "change", 0, from_reg_models=True)
        nb_terms_slider.disabled = False
    models_save_btn.disabled = False
    widget.disabled = False
    widget.loading = False


def perform_regression(widget, event, data, from_reg_models=False):
    widget.disabled = True
    widget.loading = True
    models_save_btn.disabled = True
    reg_save_btn.disabled = True
    global REGRESSIONS, PI0_PI_LIST, MODELS
    chosen_model = nb_terms_slider.v_model
    if not from_reg_models:
        models_output.clear_output(wait=True)
        with models_output:
            axs, fig = dpp.regression_models_plot(MODELS, WORKDIR)
            with plt.rc_context({"text.usetex": False, "font.family": "sans-serif"}):
                max_nb_terms = len(MODELS.keys()) - 4
                omicron = 0.001 * max_nb_terms
                if chosen_model >= max_nb_terms:
                    chosen_model = 1
                for i in range(len(axs)):
                    err_train = "NaN"
                    err_test = "NaN"
                    if i == 0:
                        err_train = round(MODELS["max |e|"][0][chosen_model], 1)
                        err_test = round(MODELS["max |e|"][1][chosen_model], 1)
                    elif i == 1:
                        err_train = round(MODELS["ave. |e|"][0][chosen_model], 1)
                        err_test = round(MODELS["ave. |e|"][1][chosen_model], 1)
                    elif i == 2:
                        err_train = round(MODELS["ave. e"][0][chosen_model], 1)
                        err_test = round(MODELS["ave. e"][1][chosen_model], 1)
                    elif i == 3:
                        err_train = round(MODELS["sigma e"][0][chosen_model], 1)
                        err_test = round(MODELS["sigma e"][1][chosen_model], 1)
                    y_max = axs[i].get_ylim()[1]
                    if chosen_model == 0:
                        axs[i].axvline(1 + omicron, color="blue")
                        axs[i].text(1 + 10*omicron, 3 * y_max / 8, str(err_train), fontdict={"fontsize": "large",
                                                                                  "fontfamily": "sans-serif"})
                        if err_test != 0:
                            axs[i].text(1 + 10*omicron, 5 * y_max / 8, str(err_test), color="red",
                                        fontdict={"fontsize": "large", "fontfamily": "sans-serif"})
                    else:
                        axs[i].axvline(chosen_model + 1, color="blue")
                        axs[i].text(chosen_model + 1 + 10*omicron, 3 * y_max / 8, str(err_train),
                                    fontdict={"fontsize": "large", "fontfamily": "sans-serif"})
                        if err_test != 0:
                            axs[i].text(chosen_model + 1 + 10*omicron, 5 * y_max / 8, str(err_test), color="red",
                                        fontdict={"fontsize": "large", "fontfamily": "sans-serif"})
            fig.savefig(os.path.join(WORKDIR, "temp\\regression_models_plot.pdf"))
            plt.show()

    regression_output.clear_output(wait=True)
    with regression_output:
        dic = REGRESSIONS[chosen_model]
        dpp.perform_regression_plot(dic["expr"], dic["Y"], dic["Y_reg"], PI0_PI_LIST[0],
                                    PI0_PI_LIST[1], WORKDIR)
        plt.show()
    if len(regression_cont.children) == 7:
        regression_cont.children = regression_cont.children + [expression_card]
    math_widget = widgets.HTMLMath(dic["expr_latex"])
    expression_cont.children = [math_widget]
    models_save_btn.disabled = False
    reg_save_btn.disabled = False
    widget.disabled = False
    widget.loading = False


def save_models(widget, event, data):
    try:
        new_name = spl.save_single_plot(WORKDIR, "regression_models_plot.pdf")
    except FileNotFoundError:
        new_log(f"Failed to save (plot may already be saved)", False)
        widget.color = "red"
        time.sleep(1)
        widget.color = "default"
    else:
        new_log(f"Saved plot as: {new_name}", True)
        widget.color = "green"
        time.sleep(1)
        widget.color = "default"


def save_reg(widget, event, data):
    try:
        new_name = spl.save_single_plot(WORKDIR, "perform_regression_plot.pdf")
    except FileNotFoundError:
        new_log(f"Failed to save (plot may already be saved)", False)
        widget.color = "red"
        time.sleep(1)
        widget.color = "default"
    else:
        new_log(f"Saved plot as: {new_name}", True)
        widget.color = "green"
        time.sleep(1)
        widget.color = "default"

# -----All Tabs functions-----------------------------------------------------------------------------------------------


def change_tab_2():
    global OLD_PHYSICAL_PARAMS, PHYSICAL_PARAMS, OUTPUTS
    valid_param_set = True
    if len(sheet.items) == 0:
        OUTPUTS = 0
        PHYSICAL_PARAMS = None
        if len(list(vbox2.children)) == 2:
            vbox2.children = [buck_error] + list(vbox2.children)
        if len(list(vbox2.children)) == 3:
            vbox2.children = [buck_error] + list(vbox2.children)[1:]
        tab2_reload()
        tab2_disable()
    if len(sheet.items) != 0:
        old_outputs = OUTPUTS
        get_outputs()
        if PHYSICAL_PARAMS is None:
            PHYSICAL_PARAMS = gen_parameter_set()
            if len(list(vbox2.children)) == 3:
                vbox2.children = list(vbox2.children)[1:]
            tab2_reload()
            valid_param_set = buckingham()
        else:
            PHYSICAL_PARAMS = gen_parameter_set()
            if OLD_PHYSICAL_PARAMS == PHYSICAL_PARAMS and OUTPUTS == old_outputs:
                if len(list(vbox2.children)) == 3:
                    vbox2.children = list(vbox2.children)[1:]
            elif OLD_PHYSICAL_PARAMS:
                if len(list(vbox2.children)) == 2:
                    vbox2.children = [buck_warn] + list(vbox2.children)
                if len(list(vbox2.children)) == 3:
                    vbox2.children = [buck_warn] + list(vbox2.children)[1:]
                tab2_reload()
                valid_param_set = buckingham()
            else:
                tab2_reload()
                valid_param_set = buckingham()
        if not valid_param_set:
            buck_area.v_model = "/!\ Cannot generate pi set out of the given parameters /!\ "
            tab2_disable()
        else:
            tab2_enable()
    OLD_PHYSICAL_PARAMS = PHYSICAL_PARAMS


def change_tab_3():
    global OUTPUTS, CHOSEN_PI_LIST, PHYSICAL_PARAMS, DOE_PI_LIST
    if CHOSEN_PI_LIST:
        if OUTPUTS == 0:
            tab3_reload()
            tab3_disable()
            doe_alert_cont.children = [no_output_error]
        elif OUTPUTS == len(CHOSEN_PI_LIST):
            tab3_reload()
            tab3_disable()
            doe_alert_cont.children = [no_input_error]
        else:
            if DOE_PI_LIST and DOE_PI_LIST != CHOSEN_PI_LIST:
                doe_alert_cont.children = [change_pi_set_warning]
            else:
                doe_alert_cont.children = []
            DOE_PI_LIST = CHOSEN_PI_LIST
            tab3_enable()
            output_index = pif.output_pi_index(CHOSEN_PI_LIST, PHYSICAL_PARAMS, OUTPUTS)
            output_list = [CHOSEN_PI_LIST[i] for i in output_index]
            output_pi.children[1].children = pi_set_html(pif.pi_sub_list_to_str(output_list, output_index))
            input_index = [i for i in range(0, len(CHOSEN_PI_LIST))]
            input_list = CHOSEN_PI_LIST.copy()
            for i in range(len(output_list)):
                input_list.remove(output_list[i])
            for ind in output_index:
                input_index.remove(ind)
            input_pi.children[1].children = pi_set_html(pif.pi_sub_list_to_str(input_list, input_index))
            wished_size_entry.v_model = DOE_MULTIPLIER * nb_of_terms()
    else:
        tab3_reload()
        tab3_disable()
        doe_alert_cont.children = [no_pi_set_error]


def change_tab_4():
    global PHYSICAL_PARAMS
    PHYSICAL_PARAMS = gen_parameter_set()
    get_outputs()
    if PHYSICAL_PARAMS is None:
        result_btn.disabled = True
        empty_csv_btn.disabled = True
        result_alert_cont.children = [result_warning]
    else:
        result_btn.disabled = False
        empty_csv_btn.disabled = False
        result_alert_cont.children = []


def change_tab_5():
    global RESULT_DF, RESULT_PI, CHOSEN_PI_SET, PHYSICAL_PARAMS, OLD_RESULT, OLD_PI_SET, REGRESSION_PI_LIST, \
        DEPENDENCY_CHECK_STATE
    dependency_alert_cont.children = []
    if CHOSEN_PI_SET is not None:
        sen_save_btn.disabled = True
        dep_save_btn.disabled = True
        update_dependency_plots_btn.loading = True
        nochange1 = CHOSEN_PI_SET == OLD_PI_SET
        nochange2 = RESULT_DF.equals(OLD_RESULT)
        if not RESULT_DF.empty and (not nochange2 or not nochange1):
            if not OLD_RESULT.empty and not nochange2:
                dependency_alert_cont.children = [dependency_change_alert]
            if not nochange1 and OLD_PI_SET:
                dependency_alert_cont.children = [dependency_change_alert_2]
            threshold_slider.disabled = True
            update_dependency_plots_btn.disabled = True
            REGRESSION_PI_LIST = CHOSEN_PI_LIST.copy()
            exp_panel_dependency.v_model = [0]
            exp_panel_dependency.disabled = False
            pi_removal_card.disabled = False
            sensitivity_output.clear_output()
            func_x_to_pi = vpl.declare_func_x_to_pi(PHYSICAL_PARAMS, CHOSEN_PI_SET)
            ordered_columns = []
            for key in PHYSICAL_PARAMS.dictionary:
                ordered_columns.append(f"{key} [{PHYSICAL_PARAMS.dictionary[key].defined_units}]")
            re_ordered_result = RESULT_DF[ordered_columns]
            RESULT_PI = func_x_to_pi(re_ordered_result.to_numpy(dtype=float))
            checkboxes = []
            if DEPENDENCY_CHECK_STATE:
                update_dependency_plots(update_dependency_plots_btn, 0, 0)
                for i in range(len(CHOSEN_PI_LIST)):
                    checkboxes.append(v.Checkbox(v_model=DEPENDENCY_CHECK_STATE[i], label=f"pi{i + 1}", class_="mx-2",
                                                 disabled=False))
                    checkboxes[i].on_event("change", dependency_check)
            else:
                with sensitivity_output:
                    try:
                        piN, pi0 = input_output_lists()
                        dpp.pi_sensitivity_plot(CHOSEN_PI_SET, RESULT_PI, WORKDIR, pi0=pi0, piN=piN, latex=True)
                    except ValueError as e:
                        print(e)
                dependency_output.clear_output()
                with dependency_output:
                    dpp.pi_dependency_plot(CHOSEN_PI_SET, RESULT_PI, WORKDIR, x_list=piN, y_list=piN, latex=True)
                dependency_set.children[1].children = pi_set_html(pif.pi_list_to_str(REGRESSION_PI_LIST))
                for i in range(len(CHOSEN_PI_LIST)):
                    checkboxes.append(v.Checkbox(v_model=True, label=f"pi{i + 1}", class_="mx-2", disabled=False))
                    checkboxes[i].on_event("change", dependency_check)
                    DEPENDENCY_CHECK_STATE.append(True)
            dependency_checkboxes.children = checkboxes
            update_dependency_check()
            threshold_slider.disabled = False
            update_dependency_plots_btn.disabled = False
        elif not RESULT_DF.empty and nochange2:
            dependency_alert_cont.children = []
            exp_panel_dependency.v_model = [0]
            exp_panel_dependency.disabled = False
            pi_removal_card.disabled = False
        else:
            dependency_alert_cont.children = [dependency_result_alert]
            exp_panel_dependency.v_model = []
            exp_panel_dependency.disabled = True
            pi_removal_card.disabled = True
        sen_save_btn.disabled = False
        dep_save_btn.disabled = False
        update_dependency_plots_btn.loading = False
    else:
        dependency_alert_cont.children = [dependency_pi_set_alert]
        exp_panel_dependency.v_model = []
        exp_panel_dependency.disabled = True
        pi_removal_card.disabled = True
    OLD_RESULT = RESULT_DF
    OLD_PI_SET = CHOSEN_PI_SET


def change_tab_6():
    tab6_enable()
    reg_alert_cont.children = []
    global DEPENDENCY_CHECK_STATE, OLD_DEPENDENCY_CHECK_STATE, REGRESSION_PI_LIST, CHOSEN_PI_LIST, CHOSEN_PI_SET
    if CHOSEN_PI_SET is not None:
        if not RESULT_DF.empty:
            if not REGRESSION_PI_LIST and CHOSEN_PI_LIST:
                REGRESSION_PI_LIST = CHOSEN_PI_LIST
            dependency_set.color = "green lighten-3"
            dependency_set.children[0].children = ["Current pi set:"]
            dependency_set.children[1].children = pi_set_html(pif.pi_list_to_str(REGRESSION_PI_LIST))
            _, pi0 = input_output_lists()
            out_index = []
            for pi_n in pi0:
                out_index.append(int(pi_n.replace("pi", "")) - 1)
            items = []
            if DEPENDENCY_CHECK_STATE and DEPENDENCY_CHECK_STATE != OLD_DEPENDENCY_CHECK_STATE:
                for i in out_index:
                    if DEPENDENCY_CHECK_STATE[i]:
                        items.append(f"pi{i + 1}")
                select_pi0.items = items
                if len(select_pi0.items) > 0:
                    select_pi0.v_model = select_pi0.items[0]
            else:
                for i in out_index:
                    items.append(f"pi{i + 1}")
                select_pi0.items = items
                if len(select_pi0.items) > 0 and select_pi0.v_model == "":
                    select_pi0.v_model = select_pi0.items[0]
                    select_reg_criteria.v_model = "max(error)"
                    model_order_entry.v_model = anticipated_mo_entry.v_model
        else:
            reg_alert_cont.children = [reg_no_result_error]
            tab6_disable()
        OLD_DEPENDENCY_CHECK_STATE = DEPENDENCY_CHECK_STATE
    else:
        reg_alert_cont.children = [reg_no_pi_set_error]
        tab6_disable()


def change_tab(widget, event, data):
    # if you change the number of tabs /!\ change line 789: if tabs.v_model == 4:
    if data == 2:
        change_tab_2()
    if data == 3:
        change_tab_3()
    if data == 4:
        change_tab_4()
    if data == 5:
        change_tab_5()
    if data == 6:
        change_tab_6()

# -----------Tutorial Tab-----------------------------------------------------------------------------------------------


_, _, x_w, y_w = GetWindowRect(GetForegroundWindow())
tutorial_box = v.Card(children=[v.CardTitle(children=["What is pyVPLM ?"]),
                                v.CardText(children=["Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam ac "
                                                     "eros nisi. Nam vitae enim mauris. Interdum et malesuada fames ac "
                                                     "ante ipsum primis in faucibus. Etiam dapibus bibendum felis. Nulla"
                                                     " et euismod lorem, eget pretium ligula. Proin feugiat et eros id "
                                                     "fringilla. Duis eu nibh ut quam ultricies ultricies ac et nulla. "
                                                     "Mauris in consequat nibh. Sed tristique, orci nec porttitor "
                                                     "aliquet, urna ex porttitor lorem, vel elementum lacus massa "
                                                     "a erat. Morbi quis pharetra diam. Nulla malesuada libero in mi "
                                                     "elementum, at viverra arcu lobortis. Donec sem ipsum, tempus sed "
                                                     "semper ac, convallis eget lacus. Proin rhoncus eros urna, in "
                                                     "feugiat purus eleifend vitae. Vivamus eros sem, tincidunt nec "
                                                     "tempus at, venenatis at est. Sed posuere nisi vel dignissim "
                                                     "vestibulum. Sed tortor enim, eleifend sit amet rutrum ultricies, "
                                                     "placerat ac tellus."]),
                                v.CardTitle(children=["How to use pyVPLM ?"]),
                                v.CardText(children=["Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nam ac "
                                                     "eros nisi. Nam vitae enim mauris. Interdum et malesuada fames ac "
                                                     "ante ipsum primis in faucibus. Etiam dapibus bibendum felis. Nulla"
                                                     " et euismod lorem, eget pretium ligula. Proin feugiat et eros id "
                                                     "fringilla. Duis eu nibh ut quam ultricies ultricies ac et nulla. "
                                                     "Mauris in consequat nibh. Sed tristique, orci nec porttitor "
                                                     "aliquet, urna ex porttitor lorem, vel elementum lacus massa "
                                                     "a erat. Morbi quis pharetra diam. Nulla malesuada libero in mi "
                                                     "elementum, at viverra arcu lobortis. Donec sem ipsum, tempus sed "
                                                     "semper ac, convallis eget lacus. Proin rhoncus eros urna, in "
                                                     "feugiat purus eleifend vitae. Vivamus eros sem, tincidunt nec "
                                                     "tempus at, venenatis at est. Sed posuere nisi vel dignissim "
                                                     "vestibulum. Sed tortor enim, eleifend sit amet rutrum ultricies, "
                                                     "placerat ac tellus."]),
                                v.CardText(children=[f"x = {x_w} ", f"y = {y_w}"])],
                      color="blue lighten-5", height=800)

# -----------Physical Parameters Tab------------------------------------------------------------------------------------


name_entry = v.TextField(label=TL[22], v_model='', outlined=True)
name_entry.on_event('click', error_end)

desc_entry = v.TextField(label=TL[23], v_model='', outlined=True)

unit_entry = v.TextField(label=TL[24], v_model='', outlined=True, append_icon="mdi-help-circle")
unit_entry.on_event('click', error_end)
unit_entry.on_event('click:append', pint_link)

lb_entry = v.TextField(v_model="", type="number", label="Lower bound", outlined=True)
lb_entry.on_event('click', error_end)

ub_entry = v.TextField(v_model="", type="number", label="Upper bound", outlined=True)
ub_entry.on_event('click', error_end)

add_btn = v.Btn(children=[TL[25]], height=56, width="100%")
add_btn.on_event('click', add_item)

h = [{'text': 'Name', 'sortable': False, 'value': 'name'},
     {'text': 'Description', 'sortable': False, 'value': 'description'},
     {'text': 'Unit', 'sortable': False, 'value': 'unit'},
     {'text': 'Lower bound', 'sortable': False, 'value': 'lower bound'},
     {'text': 'Upper Bound', 'sortable': False, 'value': 'upper bound'},
     {'text': 'Input/Output', 'sortable': False, 'value': 'in/out'}]
it = [{"name": "x", "description": "length", "unit": "m", "lower bound": 0.1, "upper bound": 100, 'in/out': 'Input'},
      {"name": "y", "description": "height", "unit": "cm", "lower bound": 1, "upper bound": 1000, 'in/out': 'Input'},
      {"name": "z", "description": "width", "unit": "m", "lower bound": 1, "upper bound": 20, 'in/out': 'Input'},
      {"name": "t", "description": "time", "unit": "s", "lower bound": 0.5, "upper bound": 10, 'in/out': 'Input'},
      {"name": "f", "description": "frequency", "unit": "s**-1", "lower bound": 100, "upper bound": 20000,
       'in/out': 'Input'},
      {"name": "v", "description": "speed", "unit": "m/s", "lower bound": 1, "upper bound": 50, 'in/out': 'Output'},
      {"name": "a", "description": "acceleration", "unit": "m/s**2", "lower bound": 0.1, "upper bound": 10,
       'in/out': 'Input'},
      {"name": "b", "description": "acceleration_2", "unit": "m/s**2", "lower bound": 1, "upper bound": 100,
       'in/out': 'Output'}
      ]

icon_up = v.Btn(children=[v.Icon(children=["mdi-arrow-up-bold"], large=True)],
                style_="margin : 40px 20px 10px 0px",
                icon=True)
icon_down = v.Btn(children=[v.Icon(children=["mdi-arrow-down-bold"], large=True)],
                  style_="margin : 10px 20px 10px 0px",
                  icon=True)
icon_del = v.Btn(children=[v.Icon(children=["mdi-delete"], large=True)],
                 v_on="tooltip.on",
                 style_="margin : 10px 20px 10px 0px",
                 icon=True)

tool_del = v.Tooltip(bottom=True, v_slots=[{
    'name': 'activator',
    'variable': 'tooltip',
    'children': icon_del,
}],
                     children=[TL[26]])

icon_out = v.Btn(children=[v.Icon(children=["mdi-variable-box"], size=27)],
                 v_on="tooltip.on",
                 icon=True,
                 style_="margin : 10px 20px 10px 0px")

tool_out = v.Tooltip(bottom=True, v_slots=[{
    'name': 'activator',
    'variable': 'tooltip',
    'children': icon_out,
}],
                     children=[TL[27]])

icon_del_all = v.Btn(children=[v.Icon(children=["mdi-recycle"], size=27)],
                     v_on="tooltip.on",
                     icon=True,
                     style_="margin : 10px 20px 10px 0px")

tool_del_all = v.Tooltip(bottom=True, v_slots=[{
    'name': 'activator',
    'variable': 'tooltip',
    'children': icon_del_all,
}],
                     children=["Delete all parameters"])

icon_up.on_event('click', up_item)
icon_down.on_event('click', down_item)
icon_del.on_event('click', del_item)
icon_out.on_event('click', set_as_out)
icon_del_all.on_event('click', del_all)

sheet = v.DataTable(v_model=[{'name': None}],
                    show_select=True,
                    single_select=True,
                    item_key='name',
                    headers=h,
                    items=it,
                    no_data_text=TL[28],
                    background_color="blue lighten-3",
                    layout=widgets.Layout(flex='90 1 auto', width='auto'))

const_alert = v.Alert(type="error",
                      value=False,
                      outlined=True,
                      children=[TL[29]],
                      transition="scroll-y-transition",
                      dismissible=True)

col1 = v.Col(children=[name_entry, lb_entry])
col2 = v.Col(children=[desc_entry, ub_entry])
col3 = v.Col(children=[unit_entry, add_btn])
box1 = v.Container(children=[v.Row(children=[col1, col2, col3])])

action_box = widgets.VBox([icon_up, icon_down, tool_del, tool_out, tool_del_all])

box2 = widgets.HBox([action_box, sheet])
box2.layout.align_content = "center"
box2.layout.justify_content = "space-between"

const_info = v.Alert(type="info", border="top", children=[TL[30]])

prio_info = v.Alert(type="info", border="top",
                    children=[TL[31],
                              v.Icon(children=["mdi-arrow-up-bold"]),
                              v.Icon(children=["mdi-arrow-down-bold"])])

vbox = widgets.VBox([const_info, box1, prio_info, box2, const_alert])
vbox.layout.margin = "15px 0px 10px 0px"

# -------- Buckingham Tab-----------------------------------------------------------------------------------------------

buck_error = v.Alert(type="error", dense=True, outlined=True,
                     children=[TL[32]])
buck_warn = v.Alert(type="warning", dense=True, outlined=True,
                    children=[TL[33]])

buck_area = v.Textarea(v_model='',
                       style_="margin : 15px 0px 0px 0px",
                       label=TL[34],
                       background_color="grey lighten-3",
                       readonly=True,
                       outlined=True,
                       auto_grow=True,
                       row=15)

force_buck_info = v.Alert(type="info", border="top", style_="margin : 5px",
                          children=[TL[35]]
                          )

force_eq = v.TextField(v_model='', label=TL[36], width=300, outlined=True, class_="mx-2")
force_eq.on_event('click', error_end)
force_eq.on_event('keydown.enter', add_pi)
add_pi_btn = v.Btn(children=[TL[37]], class_="mx-2", height="55")
add_pi_btn.on_event("click", add_pi)
force_copy_btn = v.Btn(children=[v.Icon(children=["mdi-clipboard-text-multiple-outline"])],
                       v_on='tooltip.on',
                       large=True,
                       icon=True,
                       disabled=True)
force_copy_btn.on_event('click', force_copy)
tool_copy = v.Tooltip(bottom=True, v_slots=[{
                                            'name': 'activator',
                                            'variable': 'tooltip',
                                            'children': force_copy_btn,
                                            }],
                      children=[TL[38]])

force_box = v.Container(justify="space-between", align_content="center",
                        children=[v.Row(children=[force_eq, add_pi_btn, tool_copy])])

force_area = v.Textarea(v_model='',
                        label=TL[39],
                        outlined=True,
                        background_color="white",
                        clearable=True,
                        auto_grow=True,
                        row=6)
force_area.on_event('click', error_end)

force_buck_btn = v.Btn(children=[TL[11]], width="50%", max_width=500)
force_buck_btn.on_event('click', force_buckingham)

box4 = v.Container(children=[v.Row(children=[force_buck_btn], justify="center")])

auto_buck_btn = v.Btn(children=[TL[40]], width="50%", max_width=500)
auto_buck_btn.on_event('click', automatic_buckingham)

box5 = v.Container(children=[v.Row(children=[auto_buck_btn], justify="center")])

buck_h = [{'text': TL[41], 'sortable': True, 'value': 'pi set number'},
          {'text': TL[42], 'sortable': False, 'value': 'expressions'}]

auto_buck_table = v.DataTable(v_model=[{'pi set number': None}],
                              show_select=True,
                              single_select=True,
                              checkbox_color="green",
                              items=[],
                              item_key='pi set number',
                              headers=buck_h,
                              no_data_text=TL[43],
                              layout=widgets.Layout(flex='90 1 auto', width='auto'))
auto_buck_table.on_event('item-selected', select_auto_pi_set)

check1 = v.Checkbox(v_model=True, label=TL[44], color="green")
check1.on_event('change', check1_change)
check2 = v.Checkbox(v_model=False, label=TL[44], color="green", disabled=True)
check2.on_event('change', check2_change)
check3 = v.Checkbox(v_model=False, label=TL[44], color="green", disabled=True)
check3.on_event('change', check3_change)

exp_panel = v.ExpansionPanels(v_model=[0], multiple=True, children=[
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="grey lighten-3",
                                                      class_='title font-weight-regular',
                                                      children=[TL[45]]),
                               v.ExpansionPanelContent(children=[buck_area, check1])
                               ]),
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="grey lighten-3",
                                                      class_='title font-weight-regular',
                                                      children=[TL[46]]),
                               v.ExpansionPanelContent(children=[force_buck_info,
                                                                 force_box,
                                                                 force_area,
                                                                 box4,
                                                                 check2])
                               ]),
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="grey lighten-3",
                                                      class_='title font-weight-regular',
                                                      children=[TL[47]]),
                               v.ExpansionPanelContent(children=[box5, auto_buck_table, check3])
                               ])
])

current_set = v.Card(color="grey lighten-3", margin=10, width=600,
                     children=[v.CardTitle(class_="title font-weight-regular",
                                           children=[TL[48]]),
                               v.CardText(class_="body-1", children=[])])

set_box = widgets.HBox([current_set])
set_box.layout.justify_content = "center"
set_box.layout.margin = "15px 0px 10px 0px"

vbox2 = widgets.VBox([exp_panel, set_box])
vbox2.layout.margin = "15px 0px 10px 0px"
vbox2.layout.justify_content = "space-between"

# ---------- DOE Tab ---------------------------------------------------------------------------------------------------

input_pi = v.Card(color="green lighten-3",
                  width="48%",
                  class_="mx-2",
                  children=[v.CardTitle(class_="title font-weight-regular",
                                        children=[TL[49]]),
                            v.CardText(class_="body-1", children=[])])
output_pi = v.Card(color="blue-grey lighten-3",
                   width="48%",
                   class_='mx-2',
                   children=[v.CardTitle(class_="title font-weight-regular",
                                         children=[TL[50]]),
                             v.CardText(class_="body-1", children=[])])
top_cont = v.Container(children=[v.Row(justify="space-between", children=[input_pi, output_pi])])

phy_const_entry = v.TextField(v_model='',
                              label="Declare physical parameter constraint",
                              width=300,
                              outlined=True,
                              class_="mx-2")
phy_const_entry.on_event("keydown.enter", add_phy_const)
phy_const_entry.on_event("click", error_end)
phy_const_btn = v.Btn(children=["Add constraint"], class_="mx-2", height="55")
phy_const_btn.on_event("click", add_phy_const)

phy_const_row = v.Row(style_="margin : 5px", children=[phy_const_entry, phy_const_btn])

phy_const_area = v.Textarea(v_model='',
                            label="Physical parameter constraints",
                            outlined=True,
                            background_color="white",
                            clearable=True,
                            auto_grow=True,
                            row=6)
phy_const_area.on_event("click", error_end)

pi_const_entry = v.TextField(v_model='', label="Declare pi constraint", width=300, outlined=True, class_="mx-2")
pi_const_entry.on_event("keydown.enter", add_pi_const)
pi_const_entry.on_event("click", error_end)
pi_const_btn = v.Btn(children=["Add constraint"], class_="mx-2", height="55")
pi_const_btn.on_event("click", add_pi_const)

pi_const_row = v.Row(style_="margin : 5px", children=[pi_const_entry, pi_const_btn])

pi_const_area = v.Textarea(v_model='',
                           label="Pi constraints",
                           outlined=True,
                           background_color="white",
                           clearable=True,
                           auto_grow=True,
                           row=6)
pi_const_area.on_event("click", error_end)

const_panel = v.ExpansionPanels(v_model=[0], multiple=True, children=[
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="grey lighten-3",
                                                      class_='title font-weight-regular',
                                                      children=["Physical parameter constraints"]),
                               v.ExpansionPanelContent(children=[phy_const_row, phy_const_area])]),
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="grey lighten-3",
                                                      class_='title font-weight-regular',
                                                      children=["Pi constraints"]),
                               v.ExpansionPanelContent(children=[pi_const_row, pi_const_area])])
])

select_DOE = v.Select(v_model="Full Fact", label="Select DOE type", outlined=True, items=["Full Fact", "Latin"],
                      class_="mx-2")
select_log = v.Select(v_model="Log", label="Log/Linear", outlined=True, items=["Log", "Linear"], class_="mx-2")
anticipated_mo_entry = v.TextField(v_model=1,
                                   label="Anticipated model order (optional)",
                                   type="number",
                                   width="20%",
                                   outlined=True,
                                   class_="mx-2")
anticipated_mo_entry.on_event("change", mo_to_size)

size_info = v.Alert(type="info",
                    border="top",
                    style_="margin : 15px 0 20px 0px",
                    class_="mx-2",
                    children=["Default wished size is determined by the anticipated model order"])

wished_size_entry = v.TextField(v_model=4 * DOE_MULTIPLIER,
                                label="Wished size",
                                type="number",
                                width="20%",
                                outlined=True,
                                class_="mx-2")
wished_size_entry.on_event("change", check_size)
gen_DOE_btn = v.Btn(children=["Generate DOE"], class_="mx-2", height=55, width=200)
gen_DOE_btn.on_event("click", gen_doe)

doe_tf = v.TextField(label="Filename without .csv extension", outlined=True, v_model="")
doe_tf.on_event("click", error_end)
doe_tf.on_event("keydown.enter", hide_doe)

dialog3 = v.Dialog(width='600',
                   v_model='dialog',
                   children=[
                        v.Card(color="white", children=[
                            v.CardTitle(class_='headline gray lighten-2', primary_title=True, children=[
                                "Name .csv file"
                                ]),
                            v.CardText(children=["Current work directory: " + WORKDIR], class_="font-italic"),
                            v.CardText(children=[
                                doe_tf,
                                v.Btn(children=['OK'])
                            ])
                        ])
                   ])
dialog3.v_model = False
dialog3.children[0].children[2].children[1].on_event("click", hide_doe)

DOE_rows = v.Col(children=[v.Row(children=[select_DOE, select_log]),
                           v.Row(children=[anticipated_mo_entry, wished_size_entry, gen_DOE_btn, dialog3])])

DOE_cont = v.Col(children=[const_panel, size_info, DOE_rows])

phy_scatter_matrix_output = widgets.Output()
pi_scatter_matrix_output = widgets.Output()

customizable_2d_plot_output = widgets.Output()
select_2d_x = v.Select(label="Select x-axis", outlined=True, items=[], class_="mx-2")
select_2d_x.on_event("change", customize_2d_plot)
select_2d_y = v.Select(label="Select y-axis", outlined=True, items=[], class_="mx-2")
select_2d_y.on_event("change", customize_2d_plot)
range_sliders = v.Col(children=[], style_="margin : 0 10 0 10")
range_slider_card = v.Card(children=[range_sliders], max_height=580,
                           style_='overflow-y: auto; overflow-x: hidden', class_="mx_2")

container_2d = v.Col(children=[v.Row(children=[select_2d_x, select_2d_y], align_content="center"),
                               v.Row(justify="space-around", children=[customizable_2d_plot_output, range_slider_card])
                               ])

parallel_plot_box = widgets.HBox([])

phy_save_btn = v.Icon(children=["mdi-content-save"], large=True, v_on='tooltip.on')
phy_save_btn.on_event('click', save_phy)
tool_save_phy = v.Tooltip(bottom=True, v_slots=[{
                                              'name': 'activator',
                                              'variable': 'tooltip',
                                              'children': phy_save_btn,
                                               }],
                          children=["Save plot"],
                          class_="overflow-hidden")
save_phy_cont = v.Row(children=[v.Spacer(), tool_save_phy])

pi_save_btn = v.Icon(children=["mdi-content-save"], large=True, v_on='tooltip.on')
pi_save_btn.on_event('click', save_pi)
tool_save_pi = v.Tooltip(bottom=True, v_slots=[{
                                              'name': 'activator',
                                              'variable': 'tooltip',
                                              'children': pi_save_btn,
                                               }],
                         children=["Save plot"],
                         class_="overflow-hidden")
save_pi_cont = v.Row(children=[v.Spacer(), tool_save_pi])

cus_save_btn = v.Icon(children=["mdi-content-save"], large=True, v_on='tooltip.on')
cus_save_btn.on_event('click', save_cus)
tool_save_cus = v.Tooltip(bottom=True, v_slots=[{
                                              'name': 'activator',
                                              'variable': 'tooltip',
                                              'children': cus_save_btn,
                                               }],
                          children=["Save plot"],
                          class_="overflow-hidden")

para_save_btn = v.Icon(children=["mdi-content-save"], large=True, v_on='tooltip.on')
para_save_btn.on_event('click', save_para)
tool_save_para = v.Tooltip(bottom=True, v_slots=[{
                                              'name': 'activator',
                                              'variable': 'tooltip',
                                              'children': para_save_btn,
                                               }],
                           children=["Save plot"],
                           class_="overflow-hidden")
save_para_cont = v.Row(children=[v.Spacer(), tool_save_para])

container_2d.children[0].children = container_2d.children[0].children + [tool_save_cus]

exp_panel_doe = v.ExpansionPanels(v_model=[0], multiple=True, style_='overflow-y: hidden',  children=[
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="grey lighten-3",
                                                      class_='title font-weight-regular',
                                                      children=["Scatter plot matrix (Physical Parameters)"]),
                               v.ExpansionPanelContent(children=[save_phy_cont, phy_scatter_matrix_output])
                               ]),
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="grey lighten-3",
                                                      class_='title font-weight-regular',
                                                      children=["Scatter plot matrix (Pi numbers)"]),
                               v.ExpansionPanelContent(children=[save_pi_cont, pi_scatter_matrix_output])
                               ]),
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="grey lighten-3",
                                                      class_='title font-weight-regular',
                                                      children=["2D Customizable plot"]),
                               v.ExpansionPanelContent(children=[container_2d])
                               ]),
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="grey lighten-3",
                                                      class_='title font-weight-regular',
                                                      children=["Parallel plot"]),
                               v.ExpansionPanelContent(children=[save_para_cont, parallel_plot_box])
                               ])
])

no_pi_set_error = v.Alert(type="error", dense=True, outlined=True,
                          children=["No selected pi set, please select a pi set in the Buckingham tab"])
no_output_error = v.Alert(type="error", dense=True, outlined=True,
                          children=["No pi number has been found to be an output,"
                                    " check if there is at least one output physical parameter"])
no_input_error = v.Alert(type="error", dense=True, outlined=True,
                         children=["No pi number has been found to be an input,"
                                   " check if there is at least one input physical parameter"
                                   " and enough parameters to make a input dimensionless number"])
change_pi_set_warning = v.Alert(type="warning", dense=True, outlined=True,
                                children=["Selected pi set changed"])

doe_alert_cont = v.Container(children=[])

doe_box = widgets.VBox([doe_alert_cont, top_cont, DOE_cont])

# ---------- Result import Tab------------------------------------------------------------------------------------------

result_info = v.Alert(type="info", border="top", children=["Import result supports only .csv files"])

empty_csv_btn = v.Btn(children=["Generate empty csv"], width="30%", max_width=400, height=55, class_="mx-2")
empty_csv_btn.on_event("click", gen_empty_csv)
result_btn = v.Btn(children=["Import result"], width="30%", height=55, max_width=400, class_="mx-2")
result_btn.on_event("click", result_import)

result_alert = v.Alert(type="error", dense=True, outlined=True, children=["Error"])
result_warning = v.Alert(type="warning", dense=True, outlined=True, children=["No physical parameter defined"])
result_alert_cont = v.Container(children=[])

fc_res = ipf.FileChooser(WORKDIR)
fc_res.filter_pattern = '*.csv'
fc_res._show_dialog()
fc_res.register_callback(hide_res_import)

dialog4 = v.Dialog(width='600',
                   v_model='dialog3',
                   children=[
                       v.Card(color="blue-grey lighten-4", children=[
                           v.CardTitle(class_='headline gray lighten-2', primary_title=True, children=[
                               "Choose .csv file"
                           ]),
                           v.CardText(children=[
                               fc_res
                           ])
                       ])
                   ])
dialog4.v_model = False

empty_tf = v.TextField(label="Filename without .csv extension", outlined=True, v_model="")
empty_tf.on_event("click", error_end)
empty_tf.on_event("keydown.enter", hide_empty_csv)

dialog5 = v.Dialog(width='600',
                   v_model='dialog',
                   children=[
                        v.Card(color="blue-grey lighten-4", children=[
                            v.CardTitle(class_='headline gray lighten-2', primary_title=True, children=[
                                "Name .csv file"
                                ]),
                            v.CardText(children=["Current work directory: " + WORKDIR], class_="font-italic"),
                            v.CardText(children=[
                                empty_tf,
                                v.Btn(children=['OK'])
                            ])
                        ])
                   ])
dialog5.v_model = False
dialog5.children[0].children[2].children[1].on_event("click", hide_empty_csv)

res_but_cont = v.Row(justify="center", children=[empty_csv_btn, result_btn])

result_h = [{'text': 'Measure', 'sortable': True, 'value': 'Measure'},
            {'text': 'Parameters', 'sortable': True, 'value': 'Parameters'}]

result_data = v.DataTable(v_model=[{'pi set number': None}],
                          items=[],
                          item_key='Measure',
                          headers=result_h,
                          no_data_text="No result imported",
                          layout=widgets.Layout(flex='90 1 auto', width='auto'))

result_box = v.Col(children=[result_info, res_but_cont, dialog4, dialog5, result_alert_cont, result_data])

# ---------- Dependency analysis Tab------------------------------------------------------------------------------------

dependency_result_alert = v.Alert(type="error", dense=True, outlined=True, children=["No result imported"])
dependency_pi_set_alert = v.Alert(type="error", dense=True, outlined=True, children=["No pi set defined"])
dependency_change_alert = v.Alert(type="warning", dense=True, outlined=True, children=["Imported result changed"])
dependency_change_alert_2 = v.Alert(type="warning", dense=True, outlined=True, children=["Pi set changed"])
dependency_alert_cont = v.Container(children=[])

sensitivity_info = v.Alert(type="info", border="top", style_="margin : 10px 0 10px 0px", class_="mx-2",
                           children=["MCC : Maximum Correlation Coefficient between Pearson and Spearman -- ",
                                     "alpha : Relative standard deviation (on dimensionless parameter) -- ",
                                     "IF : Impact factor IF=MCC*alpha"])

sensitivity_output = widgets.Output()


threshold_slider = v.Slider(label="R^2 threshold", v_model=0.9, min=0, max=1, step=0.01, thumb_label="always",
                            thumb_size=24, class_="mx-2")
threshold_slider.on_event("change", change_threshold)
threshold_cont = v.Container(children=[threshold_slider])
dependency_output = widgets.Output()

checkbox_info = v.Alert(type="info", border="top", style_="margin : 10px 0 10px 0px", class_="mx-2",
                        children=["Uncheck a pi number to remove it from the current set"])
dependency_checkboxes = v.Row(children=[], class_="mx-2")
dependency_checkboxes.layout.justify_content = "space-between"
checkboxes_cont = widgets.HBox([dependency_checkboxes])
checkboxes_cont.layout.justify_content = "center"

sen_save_btn = v.Icon(children=["mdi-content-save"], large=True, v_on='tooltip.on')
sen_save_btn.on_event('click', save_sen)
tool_save_sen = v.Tooltip(bottom=True, v_slots=[{
                                              'name': 'activator',
                                              'variable': 'tooltip',
                                              'children': sen_save_btn,
                                               }],
                          children=["Save plot"],
                          class_="overflow-hidden")
save_sen_cont = v.Row(children=[v.Spacer(), tool_save_sen])

dep_save_btn = v.Icon(children=["mdi-content-save"], large=True, v_on='tooltip.on')
dep_save_btn.on_event('click', save_dep)
tool_save_dep = v.Tooltip(bottom=True, v_slots=[{
                                              'name': 'activator',
                                              'variable': 'tooltip',
                                              'children': dep_save_btn,
                                               }],
                          children=["Save plot"],
                          class_="overflow-hidden")
save_dep_cont = v.Row(children=[v.Spacer(), tool_save_dep])

exp_panel_dependency = v.ExpansionPanels(v_model=[0], multiple=True, children=[
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="grey lighten-3",
                                                      class_='title font-weight-regular',
                                                      children=["Sensitivity analysis"]),
                               v.ExpansionPanelContent(children=[sensitivity_info, save_sen_cont, sensitivity_output])
                               ]),
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="grey lighten-3",
                                                      class_='title font-weight-regular',
                                                      children=["Dependency analysis"]),
                               v.ExpansionPanelContent(children=[threshold_cont, save_dep_cont, dependency_output])
                               ])
    ], class_="overflow-hidden")
exp_panel_cont = v.Container(children=[exp_panel_dependency])

update_dependency_plots_btn = v.Btn(children=["Update plots"], class_="mx-2", height=55,
                                    style_="margin : 0px 0 10px 0px")
update_dependency_plots_btn.on_event("click", update_dependency_plots)
update_plots_row = v.Row(justify="center", children=[update_dependency_plots_btn])
pi_removal_card = v.Card(children=[v.CardTitle(children=["Remove pi number"], class_="title font-weight-medium"),
                                   checkbox_info, checkboxes_cont,
                                   update_plots_row])
pi_removal_cont = v.Container(children=[pi_removal_card])

dependency_set = v.Card(color="grey lighten-3", margin=10, width=500,
                        children=[v.CardTitle(class_="title font-weight-regular",
                                              children=["No pi set defined"]),
                                  v.CardText(class_="body-1", children=[])])

set_box_2 = widgets.HBox([dependency_set])
set_box_2.layout.justify_content = "center"
set_box_2.layout.margin = "10px 0px 15px 0px"

dependency_vbox = widgets.VBox([dependency_alert_cont, exp_panel_dependency, pi_removal_cont, set_box_2])
dependency_vbox.layout.justify_content = "space-between"

# ---------- Regression Tab---------------------------------------------------------------------------------------------
reg_alert_cont = v.Col(children=[])
reg_no_result_error = v.Alert(type="error", dense=True, outlined=True, children=["No result imported"])
reg_no_pi_set_error = v.Alert(type="error", dense=True, outlined=True, children=["No pi set defined"])
reg_info = v.Alert(type="info", border="top", class_="mx-2", style_="margin : 12px 0px 0px 0px",
                   children=["If the number of points of the result > 10 * the number of models"
                             " the cross-validation step will be skipped"])

select_pi0 = v.Select(v_model="", label="Select pi0 (output)", outlined=True,
                      items=[])

model_order_entry = v.TextField(v_model=1,
                                label="Model order",
                                type="number",
                                outlined=True)
model_order_entry.on_event("click", error_end)

select_reg_criteria = v.Select(v_model="max(error)", label="Select regression criteria", outlined=True,
                               items=["max(error)", "avg(error magnitude)", "avg(error)", "sigma(error)"])

models_btn = v.Btn(children=["Show models"], class_="mx-2", height=55, width=300)
models_btn.on_event("click", regression_models)
models_btn_row = v.Row(children=[models_btn], justify="center")

regression_parameters = v.Row(children=[dependency_set,
                                        v.Col(children=[select_pi0, select_reg_criteria, model_order_entry,
                                                        models_btn_row], class_="mx-2"),
                                        v.Spacer()
                                        ], justify="center")

models_save_btn = v.Icon(children=["mdi-content-save"], large=True, v_on='tooltip.on')
models_save_btn.on_event('click', save_models)
tool_save_models = v.Tooltip(bottom=True, v_slots=[{
                                              'name': 'activator',
                                              'variable': 'tooltip',
                                              'children': models_save_btn,
                                               }],
                             children=["Save plot"],
                             class_="overflow-hidden")
save_models_cont = v.Row(children=[v.Spacer(), tool_save_models])

reg_save_btn = v.Icon(children=["mdi-content-save"], large=True, v_on='tooltip.on', disabled=True)
reg_save_btn.on_event('click', save_reg)
tool_save_reg = v.Tooltip(bottom=True, v_slots=[{
                                              'name': 'activator',
                                              'variable': 'tooltip',
                                              'children': reg_save_btn,
                                               }],
                          children=["Save plot"],
                          class_="overflow-hidden")
save_reg_cont = v.Row(children=[v.Spacer(), tool_save_reg])

models_output = widgets.Output()
models_output.layout.border = "2px solid black"
models_output_col = v.Col(children=[save_models_cont, models_output])

nb_terms_slider = v.Slider(v_model=0,
                           class_="mx-2",
                           tick_labels=[1, 2],
                           max=2,
                           step=1,
                           ticks="always",
                           tick_size="4")
nb_terms_slider.on_event("change", perform_regression)
nb_terms_slider_row = v.Row(children=[nb_terms_slider], style_=f"margin : 0px 118px 0px 56px")

regression_output = widgets.Output()

expression_cont = v.Container(children=[], style_="margin : 0px 10px 10px 10px")
expression_card = v.Card(children=[v.CardTitle(class_="title font-weight-medium", children=["Model expression:"]),
                                   expression_cont], style_='overflow-x: auto')

regression_cont = v.Col(children=[reg_alert_cont, regression_parameters, reg_info])

# --------- Main widgets------------------------------------------------------------------------------------------------

tabs = v.Tabs(v_model="tab", children=[v.Tab(children=["Tutorial"]),
                                       v.Tab(children=["Physical parameters"]),
                                       v.Tab(children=["Buckingham theorem"]),
                                       v.Tab(children=["DOE"]),
                                       v.Tab(children=["Result import"]),
                                       v.Tab(children=["Dependency analysis"]),
                                       v.Tab(children=["Regression"]),
                                       v.TabItem(children=[tutorial_box]),
                                       v.TabItem(children=[vbox]),
                                       v.TabItem(children=[vbox2]),
                                       v.TabItem(children=[doe_box]),
                                       v.TabItem(children=[result_box]),
                                       v.TabItem(children=[dependency_vbox]),
                                       v.TabItem(children=[regression_cont])],
              background_color="grey lighten-3", center_active=True)
tabs.on_event('change', change_tab)

fc_dir = ipf.FileChooser('../')
fc_dir.show_only_dirs = True
fc_dir.register_callback(hide_dir)
fc_dir._show_dialog()

dir_btn = v.Icon(children=["mdi-file-tree"], large=True, class_="mx-2", v_on='tooltip.on')
dir_btn.on_event("click", choose_dir)
tool_dir = v.Tooltip(bottom=True, v_slots=[{
                                            'name': 'activator',
                                            'variable': 'tooltip',
                                            'children': dir_btn,
                                            }],
                     children=["Choose working directory"])
dialog_dir = v.Dialog(width='600',
                      v_model='dialog',
                      children=[
                          v.Card(color="green lighten-4", children=[
                              v.CardTitle(class_='headline gray lighten-2', primary_title=True, children=[
                                  "Choose working directory"]),
                              v.CardText(children=["Current work directory: " + WORKDIR], class_="font-italic"),
                              v.CardText(children=[fc_dir], class_="body-1")
                          ])
                      ])
dialog_dir.v_model = False

save_btn = v.Icon(children=["mdi-content-save"], large=True, class_="mx-2", v_on='tooltip.on')
save_btn.on_event('click', save)
tool_save = v.Tooltip(bottom=True, v_slots=[{
                                            'name': 'activator',
                                            'variable': 'tooltip',
                                            'children': save_btn,
                                            }],
                      children=["Save"])

save_as_btn = v.Icon(children=["mdi-content-save-edit"], large=True, class_="mx-2", v_on='tooltip.on')
save_as_btn.on_event('click', save_as)
tool_save_as = v.Tooltip(bottom=True, v_slots=[{
                                              'name': 'activator',
                                              'variable': 'tooltip',
                                              'children': save_as_btn,
                                               }],
                         children=["Save as"])

save_as_tf = v.TextField(label="Filename without .txt extension", outlined=True, v_model="")
save_as_tf.on_event("click", error_end)
save_as_tf.on_event("keydown.enter", hide_save_as)

dialog = v.Dialog(width='600',
                  v_model='dialog',
                  children=[
                      v.Card(color="blue lighten-4", children=[
                          v.CardTitle(class_='headline gray lighten-2', primary_title=True, children=[
                              "Save as"
                          ]),
                          v.CardText(children=["Current work directory: " + WORKDIR], class_="font-italic"),
                          v.CardText(children=[
                              save_as_tf,
                              v.Btn(color='primary', children=['OK'])
                          ])
                      ])
                  ])
dialog.v_model = False
dialog.children[0].children[2].children[1].on_event("click", hide_save_as)

save_plots_btn = v.Icon(children=["mdi-image-multiple"], large=True, class_="mx-2", v_on='tooltip.on')
save_plots_btn.on_event("click", save_plots)
tool_save_plots = v.Tooltip(bottom=True, v_slots=[{
                                            'name': 'activator',
                                            'variable': 'tooltip',
                                            'children': save_plots_btn,
                                            }],
                            children=["Save all generated plots"])

fc_load = ipf.FileChooser(WORKDIR)
fc_load._show_dialog()
fc_load.filter_pattern = '*.txt'
fc_load.register_callback(hide_ld)

load_btn = v.Icon(children=["mdi-folder"], large=True, class_="mx-2", v_on='tooltip.on')
load_btn.on_event("click", load)

tool_load = v.Tooltip(bottom=True, v_slots=[{
                                            'name': 'activator',
                                            'variable': 'tooltip',
                                            'children': load_btn,
                                            }],
                      children=["Load"])

dialog2 = v.Dialog(width='600',
                   v_model='dialog2',
                   children=[
                       v.Card(color="orange lighten-4", children=[
                           v.CardTitle(class_='headline gray lighten-2', primary_title=True, children=[
                               "Load"
                                ]),
                           v.CardText(children=[fc_load])
                           ])
                       ])
dialog2.v_model = False

tool_icons_card = v.Card(children=[tool_dir, dialog_dir, tool_save_as, dialog, tool_save, dialog2, tool_save_plots,
                                   tool_load],
                         class_="mx-2")

log_class = "mx-2; pa-0; overflow-x: auto; overflow-y:auto"
logs_card = v.Sheet(children=[], height=37, rounded=True, width="50%", class_=log_class,
                    style_="flex-wrap: nowrap;overflow-x: auto", elevation=2)
logs_card.class_ = logs_card.class_ + "; grey--text"
logs_card.children = [v.Html(tag='div', children=["Default work directory: " + WORKDIR], class_="text-left py-2 px-2")]

img_cont = v.Row(children=[v.Img(src="logo_cut.png", max_height="55px", max_width="200px", contain=False,
                                 calss_="mr-3")],
                 justify="end")
sl_tool = v.Toolbar(children=[tool_icons_card, logs_card, img_cont], color="grey lighten-3",
                    justify="space-between")

main = v.Card(children=[sl_tool, tabs])
