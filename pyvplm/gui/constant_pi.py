import pandas as pd


def drop_constant_column(dataframe):
    """
    Drops constant value columns of pandas dataframe.
    """
    return dataframe.loc[:, (dataframe != dataframe.iloc[0]).any()]


def get_constant_pi(df):
    constants = []
    for col in df.columns:
        items = list(df[col])
        prev = items[0]
        is_constant = True
        for item in items:
            if item != prev:
                is_constant = False
                break
            prev = item
        if is_constant:
            constants.append(col)
    return constants


if __name__ == '__main__':
    df = pd.DataFrame([[1, 2, 3], [0, 0, 3], [2, 5, 3]])
    print(df)
    print(drop_constant_column(df))
    df_2 = pd.DataFrame({"A": [10, 20, 30, 40], "B": [0, 0, 0, 0], "C": [2, 2, 2.1, 2], "D": [-2.1, -2.1, -2.1, -2.1]})
    print(df_2)
    print(get_constant_pi(df_2))
