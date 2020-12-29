import pandas as pd
# import sys
# sys.path.append('/Users/3908432/PycharmProjects/MagicPlus/df_manipulation')
import df_manipulation.df_manipulation

def load_data():

    df_int = pd.read_csv('./datasets/int_shp_12mths_FiveMainTools.csv')
    df_cust_nbr = pd.read_csv('./datasets/Meter_CustNbr.csv')
    df_sphnd = pd.read_csv('./datasets/sphnd_int_12mths_FiveMainTools.csv')
    df_product_nm = pd.read_excel('./datasets/svc_bas_cd(product_nm).xlsx')
    df_cust_hierarchy = pd.read_csv('./datasets/EAN.csv')
    df_Region = pd.read_excel('./datasets/Region.xlsx')

    # Assemble the dataframe
    df = df_int.merge(df_cust_nbr, on='meter', how='left').merge(df_product_nm[['product', 'product_nm']], on='product', how='left').merge(df_cust_hierarchy, on='cust_nbr', how='left')

    return df_int, df_sphnd, df_product_nm, df

df_int, df_sphnd, df_product_nm, df = load_data()

def clean_data(df):
    # remove trailing spaces
    col_list = ['orig_ctry', 'dest_ctry']
    df = df_manipulation.StrStrip(df, col_list).strip_space()

    # remove 'nan' values
    df.dropna(subset=['cust_nbr', 'cust_nm'], inplace=True)
    return df

df = clean_data(df)

def SpHndCustEncoding(x):
    code = 'Unknown'
    if ('DG' in x.values) and ('PriorityAlert' in x.values) and ('SpHnd' in x.values):
        code = 'DG+PrioAlert+SpHnd'
    elif ('DG' in x.values) and ('PriorityAlert' in x.values):
        code = 'DG+PrioAlert'
    elif ('DG' in x.values) and ('SpHnd' in x.values):
        code = 'DG+SpHnd'
    elif ('PriorityAlert' in x.values) and ('SpHnd' in x.values):
        code = 'PrioAlert+SpHnd'
    elif ('DG' in x.values):
        code = 'DG'
    elif ('PriorityAlert' in x.values):
        code = 'PrioAlert'
    elif ('SpHnd' in x.values):
        code = 'SpHnd'
    else:
        code = 'NonSpecial'
    return code

def df_add_SpHnd(df, df_sphnd):

    # Remove codes which are not really Special Handling
    df_sphnd = df_sphnd.loc[~df_sphnd.sphnd.isin([693,376,337,333,304,40,38])]

    # Step 1
    df_sphnd.loc[df_sphnd.sphnd.isin([6,4,14]), 'sphnd'] = 'DG'
    df_sphnd.loc[df_sphnd.sphnd.isin([212,326,361,702,703,704,875,900]), 'sphnd'] = 'PriorityAlert'
    df_sphnd.loc[(df_sphnd.sphnd != 'DG') & (df_sphnd.sphnd != 'PriorityAlert'), 'sphnd'] = 'SpHnd'

    # Step 2
    df = df.merge(df_sphnd, on='meter', how='left')
    df.loc[df.sphnd.isna(), 'sphnd'] = 'NonSpecial'

    # Step 3
    df['SpHnd'] = df.groupby('cust_nbr').sphnd.transform(SpHndCustEncoding)

    # Step 4
    df.drop(['sphnd'], axis=1, inplace=True)
    df.drop_duplicates(inplace=True)

    return df

df = df_add_SpHnd(df, df_sphnd)

