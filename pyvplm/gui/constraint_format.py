from pyvplm.core.definition import Constraint, ConstraintSet


def str_to_constraint_set(inp):
    """
    Parameters
    ----------
    inp a string to be converted

    Returns Converts a input string in a ConstraintSet
    -------

    """
    lines = inp.strip().splitlines()
    const_list = []
    for line in lines:
        if line != "":
            const_list.append(Constraint(line))
    return ConstraintSet(*const_list)


if __name__ == '__main__':
    from pyvplm.core.definition import PositiveParameter, PositiveParameterSet
    from pyvplm.addon.variablepowerlaw import declare_constraints
    pi5 = PositiveParameter('x', [0.1, 1], '', 's')
    pi6 = PositiveParameter('y', [0.1, 1], '', 's')
    pi7 = PositiveParameter('z', [0.1, 1], '', 's')
    pi_set = PositiveParameterSet(pi5, pi6, pi7)
    const = str_to_constraint_set("x > y\ny > z + x\n")
    print(declare_constraints(pi_set, const))
