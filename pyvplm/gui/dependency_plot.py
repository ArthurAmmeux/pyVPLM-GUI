from pyvplm.addon.variablepowerlaw import pi_sensitivity_sub, pi_dependency_sub
import matplotlib.pyplot as plot
from matplotlib import colors
from matplotlib.ticker import PercentFormatter
import matplotlib.ticker as ticker
import save_plots as spl
import numpy
import os
from win32gui import GetWindowRect, GetForegroundWindow


def pi_sensitivity_plot(pi_set, doePI, workdir, **kwargs):
    spl.add_temp(workdir)
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
    _, _, ww, _ = GetWindowRect(GetForegroundWindow())
    axes, plot, _, _ = pi_sensitivity_sub(
        pi_set, doePI, pi0=pi0_list, piN=piN_list, figwidth=(30/1928)*ww, latex=True
    )
    if latex:
        plot.rc("text", usetex=True)
    plot.savefig(os.path.join(workdir, "temp\\sensitivity_plot.pdf"))
    plot.show()


def pi_dependency_plot(pi_set, doePI, workdir, threshold=0.9, **kwargs):
    spl.add_temp(workdir)
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
    _, _, ww, _ = GetWindowRect(GetForegroundWindow())
    _, _, _, plot = pi_dependency_sub(pi_set, doePI, order=2, threshold=threshold, figwidth=30*ww/1928,
                                      x_list=x_list_, y_list=y_list_)
    plot.savefig(os.path.join(workdir, "temp\\dependency_plot.pdf"))
    plot.show()


def regression_models_plot(models, workdir, y_max_axis=1000, latex=True):
    spl.add_temp(workdir)
    abs_error_max_train = models["max |e|"][0]
    abs_error_max_test = models["max |e|"][1]
    abs_error_average_train = models["ave. |e|"][0]
    abs_error_average_test = models["ave. |e|"][1]
    error_average_train = models["ave. e"][0]
    error_average_test = models["ave. e"][1]
    error_sigma_train = models["sigma e"][0]
    error_sigma_test = models["sigma e"][1]
    if latex:
        plot.rc("text", usetex=True)
        plot.rc("font", family="serif")
        # Start to plot the graph with indicators
    x = numpy.array(range(len(models.keys()))[:-4]).astype(int) + 1
    _, _, ww, _ = GetWindowRect(GetForegroundWindow())
    fig, axs = plot.subplots(4, sharex=True, gridspec_kw={"hspace": 0.05}, figsize=(29*ww/1928, 12*ww/1928))
    # Plot maximum absolute relative error
    axs[0].plot(x, numpy.array(abs_error_max_train), "k-*", label="Fitting set")
    if not (max(abs_error_max_test) == 0.0 and min(abs_error_max_test) == 0.0):  # FIXES 06/05/21
        axs[0].plot(x, numpy.array(abs_error_max_test), "r-*", label="Cross-validation set")
    y_max = min(y_max_axis, max(max(abs_error_max_train), max(abs_error_max_test)))
    axs[0].axis([numpy.amin(x), numpy.amax(x), 0, y_max])
    axs[0].set_ylabel(r"(1): $\max \mid \epsilon \mid$", fontsize=18)
    axs[0].grid(True)
    axs[0].legend(fontsize=16)
    # Plot average |relative error|
    axs[1].plot(x, numpy.array(abs_error_average_train), "k-*", label="Fitting set")
    if not (max(abs_error_average_test) == 0.0 and min(abs_error_average_test) == 0.0):  # FIXES 06/05/21
        axs[1].plot(x, numpy.array(abs_error_average_test), "r-*", label="Cross-validation set")
    y_max = min(y_max_axis, max(max(abs_error_average_train), max(abs_error_average_test)))
    axs[1].axis([numpy.amin(x), numpy.amax(x), 0, y_max])
    axs[1].set_ylabel(
        r"(2): $\frac{1}{n} \cdot \sum_{i=1}^n \mid \epsilon \mid$", fontsize=18
    )
    axs[1].grid(True)
    # Plot the |average relative error|
    axs[2].plot(x, numpy.absolute(error_average_train), "k-*", label="Fitting set")
    if not (max(error_average_test) == 0.0 and min(error_average_test) == 0.0):  # FIXES 06/05/21
        axs[2].plot(x, numpy.absolute(error_average_test), "r-*", label="Cross-validation set")
    y_max = min(
        y_max_axis,
        max(max(map(abs, error_average_train)), max(map(abs, error_average_test))),
    )
    axs[2].axis([numpy.amin(x), numpy.amax(x), 0, y_max])
    axs[2].set_ylabel(r"(3): $\mid \overline{\epsilon} \mid = \mid \mu \mid$", fontsize=18)
    axs[2].grid(True)
    # Plot the standard deviation
    axs[3].plot(x, numpy.absolute(error_sigma_train), "k-*", label="Fitting set")
    if not (max(error_sigma_test) == 0.0 and min(error_sigma_test) == 0.0):  # FIXES 06/05/21
        axs[3].plot(x, numpy.absolute(error_sigma_test), "r-*", label="Cross-validation set")
    y_max = min(
        y_max_axis, max(max(map(abs, error_sigma_train)), max(map(abs, error_sigma_test)))
    )
    axs[3].axis([numpy.amin(x), numpy.amax(x), 0, y_max])
    axs[3].set_ylabel(r"(4): $\mid \sigma_{\epsilon} \mid$", fontsize=18)
    axs[3].set_xlabel("Model terms number", fontsize=16)
    axs[3].grid(True)
    majors = range(len(x) + 1)
    majors = ["$" + str(majors[i]) + "$" for i in range(len(majors))]
    axs[3].xaxis.set_major_locator(ticker.MultipleLocator(1))
    axs[3].xaxis.set_major_formatter(ticker.FixedFormatter(majors))
    path = os.path.join(workdir, "temp\\regression_models_plot.pdf")
    plot.savefig(path)
    return axs, fig


def perform_regression_plot(expression, Y, Y_reg, eff_pi0, pi_list, workdir):
    spl.add_temp(workdir)
    plot.rc("text", usetex=True)
    plot.rc("font", family="serif")
    elected_pi0 = expression[0: expression.find("=")]
    elected_pi0 = elected_pi0.replace("log(", "")
    elected_pi0 = elected_pi0.replace(")", "")
    elected_pi0 = elected_pi0.replace(" ", "")
    fig, axs = plot.subplots(1, 2, tight_layout=True)
    _, _, ww, _ = GetWindowRect(GetForegroundWindow())
    fig.set_size_inches(22*ww/1928, 11*ww/1928)
    xmin = min(min(Y), min(Y_reg))
    xmax = max(max(Y), max(Y_reg))
    axs[0].plot([xmin, xmax], [xmin, xmax], "b-")
    axs[0].plot(Y, Y_reg, "r.")
    axs[0].axis([xmin, xmax, xmin, xmax])
    axs[0].grid(True)
    axs[0].set_title("Regression model", fontsize=18)
    elected_pi0 = int(elected_pi0.replace("pi", "")) - 1
    if eff_pi0 != -1:
        elected_pi0 = eff_pi0
    axs[0].set_xlabel("$" + pi_list[elected_pi0] + "$", fontsize=16)
    y_label = "$" + pi_list[elected_pi0] + " \simeq f("
    for i in range(len(pi_list)):
        if i != elected_pi0:
            y_label += pi_list[i] + ","
    y_label = y_label[0: len(y_label) - 1] + ")$"
    axs[0].set_ylabel(y_label, fontsize=18)
    error = ((numpy.array(Y_reg) - numpy.array(Y)) * (1 / numpy.array(Y)) * 100).tolist()
    n_bins = max(1, int(len(error) / 5))
    N, bins, patches = axs[1].hist(error, bins=n_bins)
    fracs = N / N.max()
    norm = colors.Normalize(fracs.min(), fracs.max())
    for thisfrac, thispatch in zip(fracs, patches):
        color = plot.cm.viridis(norm(thisfrac))
        thispatch.set_facecolor(color)
    axs[1].yaxis.set_major_formatter(PercentFormatter(xmax=len(error)))
    axs[1].grid(True)
    axs[1].set_title(r"$\epsilon$ repartition", fontsize=18)
    expression = (
            "$\overline{\epsilon}$="
            + "{:.1f}\% ".format(numpy.mean(error))
            + "$\sigma_{\epsilon}$="
            + "{:.1f}\%".format(numpy.std(error))
    )
    axs[1].set_xlabel(expression, fontsize=16)
    axs[1].set_ylabel(r"Probability", fontsize=18)
    axs[1].set_xlim(
        [-3 * numpy.std(error) + numpy.mean(error), 3 * numpy.std(error) + numpy.mean(error)]
    )
    fig.savefig(os.path.join(workdir, "temp\\perform_regression_plot.pdf"))
