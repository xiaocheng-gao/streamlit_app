import streamlit as st
import numpy as np
import pandas as pd
from df_manipulation import df_manipulation
import matplotlib.pyplot as plt
import seaborn as sns
import plotly
import plotly.express as px
from plotly.offline import init_notebook_mode, iplot
import plotly.graph_objects as go

# Title
st.title('Magic+ Dashboard')


# Load data and assemble into a dataframe
@st.cache(allow_output_mutation=True)
def load_data():

    # int_shipment five main tools
    df_int = pd.read_csv('./datasets/int_shp_12mths_FiveMainTools.csv')

    # int_shipment other tools
    int_other_tools = ['Others_noFXSF0104', 'FXSF0104_part1', 'FXSF0104_part2', 'FXSF0104_part3']
    list_df_int_other_tools = [pd.read_csv('./datasets/othertools/int_shp_12mths_{}.csv'.format(tool)) for tool in int_other_tools]
    df_int_other_tools = pd.concat(list_df_int_other_tools)
    df_int_other_tools.loc[:, 'sw_ver'] = 'Others'
    df_int_other_tools = df_int_other_tools[['meter', 'sw_ver', 'total_shipments', 'avg_rev']]

    # Concatenate all tools
    df_alltools = pd.concat([df_int, df_int_other_tools])

    # Other relevant data
    df_cust_nbr = pd.read_csv('./datasets/Meter_CustNbr.csv')
    df_sphnd = pd.read_csv('./datasets/sphnd_int_12mths_FiveMainTools.csv')
    df_product_nm = pd.read_excel('./datasets/svc_bas_cd(product_nm).xlsx')
    df_cust_hierarchy = pd.read_csv('./datasets/EAN.csv')
    df_region = pd.read_excel('./datasets/Region.xlsx')

    # Assemble the dataframe
    df = df_alltools.merge(df_cust_nbr, on='meter', how='left').merge(df_product_nm[['product', 'product_nm']], on='product', how='left').merge(df_cust_hierarchy, on='cust_nbr', how='left').merge(df_region, on='cust_ctry', how='left')

    return df, df_sphnd


df, df_sphnd = load_data()


# Data clearning
@st.cache
def clean_data(df):
    # remove trailing spaces
    col_list = ['orig_ctry', 'dest_ctry']
    df = df_manipulation.StrStrip(df, col_list).strip_space()

    # remove 'nan' values
    df.dropna(subset=['cust_nbr', 'cust_nm'], inplace=True)
    return df


df = clean_data(df)


# Feature engineering
# def sphnd_encoding(x):
#     """
#     Function to be used in df_add_sphnd: assign sphnd to each customer
#     """
#
#     code = 'Unknown'
#     if ('DG' in x.values) and ('PriorityAlert' in x.values) and ('SpHnd' in x.values):
#         code = 'DG+PrioAlert+SpHnd'
#     elif ('DG' in x.values) and ('PriorityAlert' in x.values):
#         code = 'DG+PrioAlert'
#     elif ('DG' in x.values) and ('SpHnd' in x.values):
#         code = 'DG+SpHnd'
#     elif ('PriorityAlert' in x.values) and ('SpHnd' in x.values):
#         code = 'PrioAlert+SpHnd'
#     elif 'DG' in x.values:
#         code = 'DG'
#     elif 'PriorityAlert' in x.values:
#         code = 'PrioAlert'
#     elif 'SpHnd' in x.values:
#         code = 'SpHnd'
#     else:
#         code = 'NonSpecial'
#
#     return code


# def df_add_sphnd(df, df_sphnd):
#     """
#     Function to add 'sphnd' on EAN level: indicate whether a customer ships any special handling
#     """
#
#     # Remove codes which are not really Special Handling
#     df_sphnd = df_sphnd.loc[~df_sphnd.sphnd.isin([693,376,337,333,304,40,38])]
#
#     # Step 1
#     df_sphnd.loc[df_sphnd.sphnd.isin([6,4,14]), 'sphnd'] = 'DG'
#     df_sphnd.loc[df_sphnd.sphnd.isin([212,326,361,702,703,704,875,900]), 'sphnd'] = 'PriorityAlert'
#     df_sphnd.loc[(df_sphnd.sphnd != 'DG') & (df_sphnd.sphnd != 'PriorityAlert'), 'sphnd'] = 'SpHnd'
#
#     # Step 2
#     df = df.merge(df_sphnd, on='meter', how='left')
#     df.loc[df.sphnd.isna(), 'sphnd'] = 'NonSpecial'
#
#     # Step 3
#     df['SpHnd'] = df.groupby('cust_nbr').sphnd.transform(sphnd_encoding)
#
#     # Step 4
#     df.drop(['sphnd'], axis=1, inplace=True)
#     df.drop_duplicates(inplace=True)
#
#     return df


@st.cache(allow_output_mutation=True)
def df_add_sphnd(df, df_sphnd):
    """
    Function to add 'sphnd' on METER level: indicate whether a meter ships any special handling,
    so we can see number of shipments of each special handling
    """

    # Remove codes which are not really Special Handling
    df_sphnd = df_sphnd.loc[~df_sphnd.sphnd.isin([693,376,337,333,304,40,38])]

    # Step 1
    df_sphnd.loc[df_sphnd.sphnd.isin([6, 4, 14]), 'sphnd'] = 'DG'
    df_sphnd.loc[df_sphnd.sphnd != 'DG', 'sphnd'] = 'SpHnd'

    # Step 2
    df_sphnd['sphnd_nunique'] = df_sphnd.groupby('meter').sphnd.transform('nunique')

    # Step 3
    df_sphnd.loc[df_sphnd.sphnd_nunique == 2, 'sphnd'] = 'DG'

    # Step 4
    df_sphnd.drop_duplicates(inplace=True)

    # Step 5
    df = df.merge(df_sphnd, on='meter', how='left')

    # Step 6
    df.loc[df.sphnd.isna(), 'sphnd'] = 'NonSpHnd'

    return df


df = df_add_sphnd(df, df_sphnd)


@st.cache
def df_add_features(df):
    """
    Function to add other features into dataframe:
    'prod_cplx': how many unique products a customer ship
    'freight': whether a customer ship freight
    'freight_sphnd': whether a customer ship freight and/or special handling
    'tot_revenue': total revenue of one record
    'avg_rev_per_shp': average revenue per shipment of a customer
    """

    # 'prod_cplx': count unique product of each customer
    df['prod_cplx'] = df.groupby('cust_nbr').product.transform('nunique')

    # 'freight': indicate whether a meter contains freight
    df['freight'] = df['product'].isin([32,70,80,83,84,86])

    # 'freight_sphnd': indicate whether a customer ship any freight or special handling
    BoolToStr_freight = {True: 'Freight', False: 'NonFreight'}
    df['freight'] = df.freight.map(BoolToStr_freight)
    df['freight_sphnd'] = df.freight + '_' + df.sphnd

    # 'avg_rev_per_shp': average revenue per shipment
    df['tot_revenue'] = df.total_shipments * df.avg_rev
    df['avg_rev_per_shp'] = df.groupby('cust_nbr').tot_revenue.transform('sum') / df.groupby('cust_nbr').total_shipments.transform('sum')

    return df


df = df_add_features(df)


# Creating bar plots
cust_nbr_list = st.text_input('Enter a list of customer numbers(EANs) from which you want to get insights, separated by comma.\nThen click "Display" button.')
cust_nbr_list = cust_nbr_list.split(',')

if st.button('Display'):

    st.subheader('Proportion of shipments booked with freight and/or special handling')
    fig, axes = plt.subplots(figsize=(15, 10))
    axis_1_index = ['Freight_DG', 'Freight_SpHnd', 'Freight_NonSpHnd', 'NonFreight_DG', 'NonFreight_SpHnd', 'NonFreight_NonSpHnd']
    sns.set_palette(sns.color_palette("husl", len(axis_1_index)))
    df.loc[df.cust_nbr.isin(cust_nbr_list)].groupby(['cust_nm','freight_sphnd']).total_shipments.sum().unstack().fillna(0).reindex(axis_1_index, axis=1).plot(kind='bar', stacked=True, ax=axes, grid=True, title='Freight/Special Handling Codes that were used')
    axes.set(xlabel='Customers', ylabel='Total shipments')
    axes.set_xticklabels(axes.get_xticklabels(), rotation=30, ha='right')
    axes.legend(loc='best')
    plt.tight_layout()
    st.pyplot()

    st.subheader('Proportion of shipments booked with different applications')
    fig, axes = plt.subplots(figsize=(15, 10))
    n_colors = df.loc[df.cust_nbr.isin(cust_nbr_list)].sw_ver.nunique()
    sns.set_palette(sns.color_palette("husl", n_colors))
    df.loc[df.cust_nbr.isin(cust_nbr_list)].groupby(['cust_nm','sw_ver']).total_shipments.sum().unstack().fillna(0).plot(kind='bar', stacked=True, ax=axes, grid=True, title='Tools that were used')
    axes.set(xlabel='Customers', ylabel='Total shipments')
    axes.set_xticklabels(axes.get_xticklabels(), rotation=30, ha='right')
    plt.tight_layout()
    st.pyplot()

    st.subheader('Proportion of shipments booked with different products')
    fig, axes = plt.subplots(figsize=(15, 10))
    n_colors = df.loc[df.cust_nbr.isin(cust_nbr_list)].product_nm.nunique()
    sns.set_palette(sns.color_palette("husl", n_colors))
    df.loc[df.cust_nbr.isin(cust_nbr_list)].groupby(['cust_nm','product_nm']).total_shipments.sum().unstack().fillna(0).plot(kind='bar', stacked=True, ax=axes, grid=True, title='Products that were used')
    axes.set(xlabel='Customers', ylabel='Total shipments')
    axes.set_xticklabels(axes.get_xticklabels(), rotation=30, ha='right')
    axes.legend(loc='best')
    plt.tight_layout()
    st.pyplot()


# Creating sankey plots
def genSankey(df, cat_cols=[], value_cols='', title='Sankey Diagram'):
    # maximum of 6 value cols -> 6 colors
    colorPalette = ['#eb7134', '#ebba34', '#89eb34', '#34d0eb', '#7303fc']
    labelList = []  # [uniqueGENs, uniqueCENs, uniqueEANs, uniqueMeters]
    colorNumList = []  # [nuniqueGENs, nuniqueCENs, nuniqueEANs, nuniqueMeters]
    for catCol in cat_cols:
        labelListTemp = list(set(df[catCol].values))  # labelListTemp = [uniqueGENs]
        colorNumList.append(len(labelListTemp))
        labelList = labelList + labelListTemp

    # remove duplicates from labelList
    labelList = list(dict.fromkeys(labelList))

    # define colors based on number of levels
    colorList = []  # [['#4B8BBE'] * nuniqueGENs, ['#306998'] * nuniqueCENs, ['#FFE873'] * nuniqueEANs, ['#FFD43B'] * nuniqueMeters]
    for idx, colorNum in enumerate(colorNumList):
        colorList = colorList + [colorPalette[idx]] * colorNum

    # transform df into a source-target pair
    for i in range(len(cat_cols) - 1):
        if i == 0:
            sourceTargetDf = df[[cat_cols[i], cat_cols[i + 1], value_cols]]
            sourceTargetDf.columns = ['source', 'target', 'count']
        else:
            tempDf = df[[cat_cols[i], cat_cols[i + 1], value_cols]]
            tempDf.columns = ['source', 'target', 'count']
            sourceTargetDf = pd.concat([sourceTargetDf, tempDf])
        sourceTargetDf = sourceTargetDf.groupby(['source', 'target']).agg({'count': 'sum'}).reset_index()

    # add index for source-target pair
    sourceTargetDf['sourceID'] = sourceTargetDf['source'].apply(lambda x: labelList.index(x))
    sourceTargetDf['targetID'] = sourceTargetDf['target'].apply(lambda x: labelList.index(x))

    # creating the sankey diagram
    data = dict(
        type='sankey',
        node=dict(
            pad=15,
            thickness=20,
            line=dict(
                color="black",
                width=0.5
            ),
            label=labelList,
            color=colorList
        ),
        link=dict(
            source=sourceTargetDf['sourceID'],
            target=sourceTargetDf['targetID'],
            value=sourceTargetDf['count']
        )
    )

    return data


st.subheader('Distribution of shipments across different customer hierarchy')


EAN_list = cust_nbr_list
GEN_list = df.loc[df.cust_nbr.isin(EAN_list)].glb_enti_nbr.unique().tolist()

data_list = []
for GEN in GEN_list:
    sub_df = pd.DataFrame(df.loc[df.glb_enti_nbr==GEN].groupby(['glb_enti_nbr', 'ctry_enti_nbr', 'cust_nbr', 'meter', 'sw_ver']).total_shipments.sum()).reset_index()
    data = genSankey(sub_df,cat_cols=['glb_enti_nbr','ctry_enti_nbr','cust_nbr','meter','sw_ver'],value_cols='total_shipments',title='Shipments_Distribution')
    data_list.append(data)

buttons = []
for i, GEN in enumerate(GEN_list):
    visible_list = [False] * len(GEN_list)
    visible_list[i] = True
    EAN = df.loc[(df.glb_enti_nbr==GEN) & (df.cust_nbr.isin(EAN_list))].cust_nbr.unique()[0]
    button = dict(label = '{}'.format(EAN), method = 'update', args = [{'visible': visible_list}])
    buttons.append(button)

updatemenus = [dict(active=-1, buttons= buttons)]

# Set layout
layout = dict(title='Select a customer number',
              showlegend=False,
              updatemenus=updatemenus)

# Create fig
fig = dict(data=data_list, layout=layout)

st.plotly_chart(fig)

