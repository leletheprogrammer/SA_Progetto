import pandas as pd
from sklearn.model_selection import train_test_split

def split_strat_train_val_test(
        df_input, stratify_colname='y', random_state=123,
        frac_train=0.8, frac_val=0.10, frac_test=0.10):
    if frac_train + frac_val + frac_test != 1.0:
        raise ValueError('fractions %f, %f, %f do not add up to 1.0' % \
                         (frac_train, frac_val, frac_test))
    if stratify_colname not in df_input.columns:
        raise ValueError('%s is not a column in the dataframe' % stratify_colname)
    X = df_input
    y = df_input[[stratify_colname]]
    df_train, df_temp, y_train, y_temp = train_test_split(
        X, y, stratify=y, test_size=(1.0 - frac_train), random_state=random_state)
    relative_frac_test = frac_test / (frac_val + frac_test)
    df_val, df_test, y_val, y_test = train_test_split(
        df_temp, y_temp, stratify=y_temp, test_size=relative_frac_test, random_state=random_state)
    assert len(df_input) == len(df_train) + len(df_val) + len(df_test)
    return df_train, df_val, df_test