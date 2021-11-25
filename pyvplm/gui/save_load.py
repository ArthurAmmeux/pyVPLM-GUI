import easygui


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


def save(items, file_name):
    f = open_file(file_name)[0]
    wrt = ""
    for item in items:
        wrt += item["name"] + "|" + item["description"] + "|" + item["unit"] + "|"
        wrt += str(item["lower bound"]) + "|" + str(item["upper bound"]) + "|" + item["in/out"] + "\n"
    f.write(wrt)
    f.close()


def load(f_name):
    f = open(f_name, "r")
    data = []
    lines = f.readlines()
    for line in lines:
        line = line.strip()
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
        data.append(dic)
    f.close()
    return data
