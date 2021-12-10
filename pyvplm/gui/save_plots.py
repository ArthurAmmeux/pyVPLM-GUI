import os
import shutil
from datetime import datetime


def save_all_plots(workdir):
    source_dir = workdir + "\\temp"
    target_dir = workdir

    file_names = os.listdir(source_dir)

    if len(file_names) > 0:
        now = datetime.now()
        dt_string = now.strftime("_%d%m%y_%H%M%S")
        for file_name in file_names:
            new_file_name = file_name[:-4] + dt_string + file_name[-4:]
            os.rename(os.path.join(source_dir, file_name), os.path.join(source_dir, new_file_name))
            shutil.move(os.path.join(source_dir, new_file_name), target_dir)
    else:
        raise FileNotFoundError("No plots have been generated")


def save_single_plot(workdir, name):
    add_temp(workdir)
    now = datetime.now()
    dt_string = now.strftime("_%d%m%y_%H%M%S")
    new_name = name[:-4] + dt_string + name[-4:]
    try:
        os.rename(os.path.join(workdir, "temp\\" + name), os.path.join(workdir, "temp\\" + new_name))
    except FileNotFoundError:
        raise FileNotFoundError("Plot not yet generated")
    src_path = os.path.join(workdir,  "temp\\" + new_name)
    if os.path.exists(src_path):
        shutil.move(src_path, workdir)
        return new_name
    else:
        raise FileNotFoundError("Plot not yet generated")


def add_temp(workdir):
    if not os.path.exists(workdir + "\\temp"):
        os.mkdir(workdir + "\\temp")


def move_temp(old_workdir, new_workdir):
    if os.path.exists(new_workdir + "\\temp"):
        shutil.rmtree(new_workdir + "\\temp")
    try:
        shutil.move(old_workdir + "\\temp", new_workdir, copy_function=shutil.copytree)
        os.chdir(new_workdir)
    except shutil.Error as e:
        print(e)


def save_plot_test(workdir):
    os.chdir(workdir)
    try:
        os.mkdir("temp")
    except OSError as e:
        print(e)
    finally:
        f = open("temp\\test_file.txt", "x")
        f.write("TEST")


WORKDIR = os.getcwd()

if __name__ == "__main__":
    save_plot_test(WORKDIR)
    NEW_WORKDIR = "C:\\Users\\ammeux\\Documents\\pyVPLM\\pyvplm\\tests"
    move_temp(WORKDIR, NEW_WORKDIR)
    add_temp(WORKDIR)
    print(os.getcwd())
    print(WORKDIR)
    save_all_plots(WORKDIR + "\\tests")

