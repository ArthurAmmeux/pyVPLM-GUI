# Import pyVPLM packages

from pyvplm.core.definition import PositiveParameter, PositiveParameterSet
from pyvplm.addon.variablepowerlaw import buckingham_theorem
from pint import UnitRegistry
import save_load as sl

# Import libs
import ipyfilechooser as ipf
import time
import ipywidgets as widgets
import ipyvuetify as v


def check_name(name):
    if name == '':
        name_entry.error_messages = "please specify a name"
        return False
    if ' ' in name or '|' in name:
        name_entry.error_messages = "invalid character: space, |"
        return False
    for item in sheet.items:
        if item['name'] == name:
            name_entry.error_messages = "name aready exists"
            return False
    return True


def check_desc(desc):
    if '|' in desc:
        desc_entry.error_messages = "invalid character: |"
        return False
    return True


def check_unit(unit):
    if unit == '':
        unit_entry.error_messages = "please specify a unit"
        return False
    base_registry = UnitRegistry()
    if unit not in base_registry:
        unit_entry.error_messages = "unrecognized unit"
        return False
    return True


def check_bounds():
    lb = lb_entry.v_model
    ub = ub_entry.v_model
    lbool = lb is None or lb == ""
    ubool = ub is None or lb == ""
    if ubool:
        ub_entry.error_messages = "please specify upper bound"
        return False
    err_mess = "bounds must be numbers"
    if lbool:
        try:
            ub = float(ub)
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
            err_mess = "Bound must be strictly positive"
            if lb <= 0:
                neg = True
                lb_entry.error_messages = err_mess
            if ub <= 0:
                neg = True
                ub_entry.error_messages = err_mess
            if neg:
                return False
            else:
                err_mess = "lower bound must be strictly inferior to upper bound"
                lb_entry.error_messages = err_mess
                ub_entry.error_messages = err_mess
            return False


def add_item(widget, data, event):
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
        upper_bound = float(ub_entry.v_model)
        name_entry.v_model = ''
        desc_entry.v_model = ''
        unit_entry.v_model = ''
        lb_entry.v_model = None
        ub_entry.v_model = None
        del_but = v.Btn(label="delete")
        sheet.items = sheet.items + [{"name": name,
                                      "description": description,
                                      "unit": unit,
                                      "lower bound": lower_bound,
                                      "upper bound": upper_bound}]


def buckingham(widget, data, event):
    widget.disabled = True
    widget.loading = True
    data = sheet.items
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
        pi_set, _ = buckingham_theorem(param_set, True)
        buck_area.v_model = str(pi_set)
    # buck_area.v_model = latex
    widget.loading = False
    widget.disabled = False


def del_item(widget, data, event):
    if sheet.v_model:
        item_name = sheet.v_model[0]['name']
        for i in range(len(sheet.items)):
            if sheet.items[i]['name'] == item_name:
                if i == len(sheet.items):
                    sheet.items = sheet.items[:-1]
                else:
                    sheet.items = sheet.items[0:i] + sheet.items[i + 1:]
                break


def up_item(widget, data, event):
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


def down_item(widget, data, event):
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


def error_end(widget, data, event):
    widget.error_messages = ""


def save(widget, event, data):
    dialog.v_model = True


def hide_sd(widget, data, event):
    file_path = fc_save.selected
    if file_path:
        sl.save(sheet.items, file_path)
        dialog.v_model = False
        save_btn.color = "blue darken-4"
        save_btn.children = ["Saved"]
        time.sleep(2)
        save_btn.color = "blue darken-2"
        save_btn.children = ["Save"]
    else:
        dialog.v_model = False


def load(widget, event, data):
    dialog2.v_model = True


def hide_ld(widget, data, event):
    file_path = fc_load.selected
    if file_path:
        sheet.items = sl.load(file_path)
        dialog2.v_model = False
        load_btn.color = "orange darken-4"
        load_btn.children = ["Loaded"]
        time.sleep(2)
        load_btn.color = "orange darken-2"
        load_btn.children = ["Load"]
    else:
        dialog2.v_model = False


# -----------Physical Quantities Tab-------------

name_entry = v.TextField(label="Name", v_model='', outlined=True)
name_entry.on_event('click', error_end)

desc_entry = v.TextField(label="Description", v_model='', outlined=True)

unit_entry = v.TextField(label="Unit", v_model='', outlined=True)
unit_entry.on_event('click', error_end)

lb_entry = v.TextField(v_model=None, type="number", label="Lower bound", outlined=True)
lb_entry.on_event('click', error_end)

ub_entry = v.TextField(v_model=None, type="number", label="Upper bound", outlined=True)
ub_entry.on_event('click', error_end)

add_btn = v.Btn(children=["Add parameter"], height=56, width=305, color="green")
add_btn.on_event('click', add_item)

h = [{'text': 'Name', 'sortable': False, 'value': 'name'},
     {'text': 'Description', 'sortable': False, 'value': 'description'},
     {'text': 'Unit', 'sortable': False, 'value': 'unit'},
     {'text': 'Lower bound', 'sortable': False, 'value': 'lower bound'},
     {'text': 'Upper Bound', 'sortable': False, 'value': 'upper bound'}]
it = [{"name": "x", "description": "length", "unit": "m", "lower bound": 0.1, "upper bound": 100},
      {"name": "y", "description": "height", "unit": "cm", "lower bound": 1, "upper bound": 1000},
      {"name": "t", "description": "time", "unit": "s", "lower bound": 0.5, "upper bound": 10},
      {"name": "v", "description": "speed", "unit": "m/s", "lower bound": 1, "upper bound": 50}]

icon_up = v.Btn(children=[v.Icon(children=["mdi-arrow-up-bold"], large=True)],
                style_="margin : 10px",
                color="green lighten-2")
icon_down = v.Btn(children=[v.Icon(children=["mdi-arrow-down-bold"], large=True)],
                  style_="margin : 10px",
                  color="green lighten-2")
icon_del = v.Btn(children=[v.Icon(children=["mdi-delete"], large=True)],
                 style_="margin : 10px",
                 color="red lighten-2")

icon_up.on_event('click', up_item)
icon_down.on_event('click', down_item)
icon_del.on_event('click', del_item)

sheet = v.DataTable(v_model=[{'name': None}],
                    show_select=True,
                    single_select=True,
                    item_key='name',
                    headers=h,
                    items=it,
                    background_color="blue lighten-3",
                    layout=widgets.Layout(flex='90 1 auto', width='auto'))

col1 = v.Col(children=[name_entry, lb_entry])
col2 = v.Col(children=[desc_entry, ub_entry])
col3 = v.Col(children=[unit_entry, add_btn])
box1 = v.Container(children=[v.Row(children=[col1, col2, col3])])

action_box = widgets.VBox([icon_up, icon_down, icon_del])

box2 = widgets.HBox([sheet, action_box])
box2.layout.align_content = "center"
box2.layout.justify_content = "space-between"

const_info = v.Alert(type="info", border="top", children=["For constants, do not specify a lower bound"])

prio_info = v.Alert(type="info", border="top",
                    children=["Higher parameters have higher priority to be repetitive parameters ",
                              v.Icon(children=["mdi-arrow-up-bold"]),
                              v.Icon(children=["mdi-arrow-down-bold"])])

vbox = widgets.VBox([const_info, box1, prio_info, box2])
vbox.layout.margin = "15px 0px 10px 0px"

# -------- Buckingham Tab-------------

buck_btn = v.Btn(children=["Buckingham theorem"], color="orange", width="50%")
buck_btn.on_event('click', buckingham)

box3 = v.Container(children=[v.Row(children=[buck_btn], justify="center")])

buck_area = v.Textarea(v_model='',
                       type='html',
                       label='Buckingham theorem output',
                       background_color="orange lighten-4",
                       readonly=True,
                       outlined=True,
                       auto_grow=True,
                       row=15)

force_buck_info = v.Alert(type="info", border="top", style_ = "margin : 5px",
                          children=["The equation variables must have the same name as in the previous tab"]
                          )

force_eq = v.TextField(label="Type your expression here", width=300, outlined=True, class_="mx-2")
force_eq_btn = v.Btn(children=["Add pi number"], color="orange", class_="mx-2")

force_box = v.Container(justify="space-between", children=[v.Row(children=[force_eq, force_eq_btn])])

force_area = v.Textarea(label="Forced Pi numbers",
                        outlined=True,
                        background_color="orange lighten-4",
                        readonly=True,
                        clearable=True,
                        auto_grow=True,
                        row=6)

force_buck_btn = v.Btn(children=["Complete Pi set"], color="orange", width="50%")
force_buck_btn.on_event('click', buckingham)

box4 = v.Container(children=[v.Row(children=[force_buck_btn], justify="center")])

force_buck_area = v.Textarea(v_model='',
                             type='html',
                             label='Force Buckingham output',
                             background_color="orange lighten-4",
                             readonly=True,
                             outlined=True,
                             auto_grow=True,
                             row=15)

auto_buck_btn = v.Btn(children=["Automatic Buckingham"], color="orange", width="50%")
auto_buck_btn.on_event('click', buckingham)

box5 = v.Container(children=[v.Row(children=[auto_buck_btn], justify="center")])

auto_buck_area = v.Textarea(v_model='',
                            type='html',
                            label='Automatic Buckingham output',
                            outlined=True,
                            background_color="orange lighten-4",
                            readonly=True,
                            auto_grow=True,
                            row=15)

check1 = v.Checkbox(v_model="True", label="Choose this Pi set", color="green")
check2 = v.Checkbox(label="Choose this Pi set", color="green")
check3 = v.Checkbox(label="Choose this Pi set", color="green")

exp_panel = v.ExpansionPanels(v_model=[0], multiple=True, children=[
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="orange lighten-2", children=["Simple Buckingham"]),
                               v.ExpansionPanelContent(children=[box3, buck_area, check1])
                               ]),
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="orange lighten-1", children=["Force Buckingham"]),
                               v.ExpansionPanelContent(children=[force_buck_info,
                                                                 force_box,
                                                                 force_area,
                                                                 box4,
                                                                 force_buck_area,
                                                                 check2])
                               ]),
    v.ExpansionPanel(children=[v.ExpansionPanelHeader(color="orange", children=["Automatic Buckingham"]),
                               v.ExpansionPanelContent(children=[box5, auto_buck_area, check3])
                               ])
    ]
    )

confirm_pi_set = v.Btn(children=["Confirm Pi set"], color="green", class_="mx-2", width=200, height=70)
current_set = v.Card(color="green lighten-3", class_="mx-2", width=200,
                     children=[v.CardTitle(children=["Selected Pi set:"])]
                     )
cont = v.Container(children=[v.Row(children=[current_set, confirm_pi_set], justify="space-between")])

vbox2 = widgets.VBox([exp_panel, cont])
vbox2.layout.margin = "15px 0px 10px 0px"
vbox2.layout.justify_content = "space-between"

# ---------- DOE Tab---------------

doe_card = v.Card(height=400, color="blue lighten-2",
                  children=[v.CardTitle(class_='headline gray lighten-2', primary_title=True, children=["DOE Tab"])]
                  )

# ---------- Result import Tab---------------

result_card = v.Card(height=400, color="green lighten-2",
                     children=[v.CardTitle(class_='headline gray lighten-2', primary_title=True,
                                           children=["Result import Tab"])]
                     )

# ---------- Dependency analysis Tab---------------

dependency_card = v.Card(height=400, color="yellow lighten-2",
                         children=[v.CardTitle(class_='headline gray lighten-2',
                                               primary_title=True,
                                               children=["Dependency analysis Tab"])
                                   ]
                         )

# ---------- Regression Tab---------------

regression_card = v.Card(height=400, color="orange lighten-2",
                         children=[v.CardTitle(class_='headline gray lighten-2', primary_title=True,
                                               children=["Regression Tab"])]
                         )

# --------- Main widgets------------

tabs = v.Tabs(v_model="tab", children=[v.Tab(children=["Phyical quantities"]),
                                       v.Tab(children=["Buckingham theorem"]),
                                       v.Tab(children=["DOE"]),
                                       v.Tab(children=["Result import"]),
                                       v.Tab(children=["Dependency analysis"]),
                                       v.Tab(children=["Regression"]),
                                       v.TabItem(children=[vbox]),
                                       v.TabItem(children=[vbox2]),
                                       v.TabItem(children=[doe_card]),
                                       v.TabItem(children=[result_card]),
                                       v.TabItem(children=[dependency_card]),
                                       v.TabItem(children=[regression_card]), ],
              background_color="cyan", center_active=True, dark=True, slider_color="yellow")

fc_save = ipf.FileChooser('./')
fc_save.filter_pattern = '*.txt'

save_btn = v.Btn(color='blue darken-2', class_="mx-2", dark=True, width=300, children=['Save'])
save_btn.on_event('click', save)

dialog = v.Dialog(width='600',
                  v_model='dialog',
                  children=[
                      v.Card(color="blue lighten-4", children=[
                          v.CardTitle(class_='headline gray lighten-2', primary_title=True, children=[
                              "Save"
                          ]),
                          v.CardText(children=[
                              fc_save,
                              v.Btn(color='primary', children=['OK'])
                          ])
                      ])
                  ])
dialog.v_model = False
dialog.children[0].children[1].children[1].on_event("click", hide_sd)

fc_load = ipf.FileChooser('./')
fc_load.filter_pattern = '*.txt'

load_btn = v.Btn(color='orange darken-2', class_="mx-2", dark=True, width=300, children=['Load'])
load_btn.on_event("click", load)

dialog2 = v.Dialog(width='600',
                   v_model='dialog2',
                   children=[
                       v.Card(color="orange lighten-4", children=[
                           v.CardTitle(class_='headline gray lighten-2', primary_title=True, children=[
                               "Load"
                           ]),
                           v.CardText(children=[
                               fc_load,
                               v.Btn(color='orange', children=['OK'])
                           ])
                       ])
                   ])
dialog2.v_model = False
dialog2.children[0].children[1].children[1].on_event("click", hide_ld)

sl_tool = v.Toolbar(children=[dialog, save_btn, dialog2, load_btn], color="cyan")

main = v.Card(children=[sl_tool, tabs])
