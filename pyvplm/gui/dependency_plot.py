from pyvplm.addon.variablepowerlaw import pi_sensitivity_sub, pi_dependency_sub


def pi_sensitivity_plot(pi_set, doePI, **kwargs):
    latex = False
    pi0_list = [list(pi_set.dictionary.keys())[0]]
    piN_list = list(pi_set.dictionary.keys())[1: len(list(pi_set.dictionary.keys()))]
    for key, value in kwargs.items():
        if key == "latex":
            if isinstance(value, bool):
                latex = value
            else:
                raise TypeError("latex should be boolean")
        if key == "pi0":
            if isinstance(value, list):
                pi0_list = value
            else:
                raise TypeError("pi0 should be a list")
        if key == "piN":
            if isinstance(value, list):
                piN_list = value
            else:
                raise TypeError("piN should be a list")
    pi_list = []
    for pi in pi_set.dictionary.keys():
        pi_list.append(pi.replace("pi", "$\pi_{") + "}$")
    axes, plot, _, _ = pi_sensitivity_sub(
        pi_set, doePI, pi0=pi0_list, piN=piN_list, figwidth=16, latex=True
    )
    if latex:
        plot.rc("text", usetex=True)
    plot.show()


def pi_dependency_plot(pi_set, doePI, threshold=0.9, **kwargs):
    x_list_ = []
    y_list_ = []
    for key, value in kwargs.items():
        if key == "x_list":
            if isinstance(value, list):
                x_list_ = value
            else:
                raise TypeError("x_list should be a list")
        if key == "y_list":
            if isinstance(value, list):
                y_list_ = value
            else:
                raise TypeError("y_list should be a list")
    _, _, _, plot = pi_dependency_sub(pi_set, doePI, order=2, threshold=threshold, figwidth=16,
                                      x_list=x_list_, y_list=y_list_)
    plot.show()
