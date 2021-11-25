import numpy as np
import csv

import pandas as pd


def open_csv_file(f_name):
    """
    :param f_name: name of the csv file
    :return: a new csv file with as many (1) as needed to not already exist
    """
    try:
        f = open(f_name, "x")
        return f, f_name
    except IOError:
        return open_csv_file(f_name[:-4] + "(1)" + f_name[-4:])


def generate_csv(doeX, file_name, parameter_set, out_headers):
    _, file_name = open_csv_file(file_name)
    with open(file_name, 'w', encoding='UTF8', newline='') as out_file:
        writer = csv.writer(out_file)
        headers = []
        for key in parameter_set.dictionary:
            headers.append(f"{key} [{parameter_set.dictionary[key].defined_units}]")
        headers = headers + out_headers
        writer.writerow(headers)
        doe_list = doeX.tolist()
        for point in doe_list:
            writer.writerow(point)
        out_file.close()


def format_headers(headers):
    out_headers = []
    for header in headers:
        header_dict = {'text': header, 'sortable': True, 'value': header}
        out_headers.append(header_dict)
    return out_headers


def check_headers(df_headers, physical_parameters):
    params = list(physical_parameters.dictionary.keys())
    raw_headers = []
    units = []
    for header in df_headers:
        try:
            spt = header.split("[")
            raw_headers.append(spt[0].strip())
            units.append(spt[1].split("]")[0])
        except Exception:
            raise SyntaxError("Invalid csv file")
    if len(raw_headers) < len(params):
        raise ValueError(
            f"Not enough columns ({len(raw_headers)}, should be {len(params)}), physical parameter missing")
    if len(raw_headers) > len(params):
        raise ValueError(
            f"Too many columns ({len(raw_headers)}, should be {len(params)}),"
            f" inconsistent with defined physical parameters")
    for i in range(len(raw_headers)):
        if raw_headers[i] != params[i]:
            raise ValueError(
                f"CSV headers and defined physical parameters do not match: {raw_headers[i]} =/= {params[i]}")
        cur_unit = physical_parameters.dictionary[params[i]].defined_units
        if units[i] != cur_unit:
            raise ValueError(
                f"CSV units and defined physical parameters units do not match: {units[i]} =/= {cur_unit}")


def check_content(result_df):
    errors = []
    for col in result_df.columns:
        chk_sum = result_df[col].isnull().sum()
        if chk_sum > 0:
            errors.append([col, chk_sum])
    if errors:
        err_str = "Csv contains None values: "
        for error in errors:
            err_str += f"in column {error[0]} {error[1]} None values, "
        raise ValueError(err_str[:-2])


def read_csv(path, physical_parameters):
    with open(path) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        df_headers = []
        df_items = []
        headers = ['Measure']
        items = []
        for row in csv_reader:
            if line_count == 0:
                df_headers = list(row.keys())
                headers = headers + list(row.keys())
                line_count += 1
            df_items.append(list(row.values()))
            row['Measure'] = line_count
            items.append(row)
            line_count += 1
        result_df = pd.DataFrame(df_items, columns=df_headers)
        check_headers(df_headers, physical_parameters)
        check_content(result_df)
        return format_headers(headers), items, result_df


if __name__ == '__main__':
    from pyvplm.core.definition import PositiveParameter, PositiveParameterSet
    #doePI = pandas.read_excel('./pi_analysis_example.xls')
    #doePI = doe[['pj', 'pfe', 'pi2', 'pi3', 'pi4', 'pi5', 'pi6']].values
    pi1 = PositiveParameter('pi1', [0.1, 1], '', 'p_j')
    pi2 = PositiveParameter('pi2', [0.1, 1], '', 'p_fe')
    pi3 = PositiveParameter('pi3', [0.1, 1], '', 'd_i*d_e**-1')
    pi4 = PositiveParameter('pi4', [0.1, 1], '', 'e_tooth*d_e**-1*n')
    pi5 = PositiveParameter('pi5', [0.1, 1], '', 'e_yoke*d_e**-1*n')
    pi6 = PositiveParameter('pi6', [0.1, 1], '', 'w_pm*d_e**-1')
    pi7 = PositiveParameter('pi7', [0.1, 1], '', 'r_i*d_e**-1')
    pi_set = PositiveParameterSet(pi1, pi2, pi3, pi4, pi5, pi6, pi7)
    doe = np.array([[1.1, 2.2, 3.5, 4.7, 5.3, 6.9, 7.1], [0.1, 2, 3, 4, 5.5, 6, 0], [7, 5, 4, 8.4, 5, 6, 9]])
    generate_csv(doe, 'test_csv.csv', pi_set, [])
    read_csv('test_csv.csv', pi_set)
