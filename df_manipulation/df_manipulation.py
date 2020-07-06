class StrStrip:

    def __init__(self, df, col_list):
        self.df = df
        self.col_list = col_list

    def strip_space(self):
        for col_nm in self.col_list:
            self.df.loc[:, col_nm] = self.df.loc[:, col_nm].str.strip()
        return self.df



class MakeSubDFs:

    def __init__(self, df, select_rows, select_cols, divide_rows):
        self.df = df
        self.select_rows = select_rows
        self.select_cols = select_cols
        self.divide_rows = divide_rows
        self.sub_dfs = []

    def slice_rows(self):
        for colname, elements in self.select_rows.items():
            if isinstance(elements, list):
                self.df = self.df.loc[self.df[colname].isin(elements), :]
            else:
                self.df = self.df.loc[self.df[colname] == elements, :]
        return self

    def slice_cols(self):
        self.df = self.df.loc[:, self.select_cols]
        return self

    def divide_df(self):
        colname = next(iter(self.divide_rows.keys()))
        elements = next(iter(self.divide_rows.values()))
        for element in elements:
            sub_df = self.df.loc[self.df[colname] == element, :]
            self.sub_dfs.append(sub_df)
        return self

    def drop_duplicates(self):
        self.df = self.df.drop_duplicates()
        return self
