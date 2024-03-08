from lib import *

os.environ['GSPREAD_SILENCE_WARNINGS'] = '1'
SA_KEY = "sa_key.json"


class GoogleSheet:

    def __init__(self, url):
        gc = gspread.service_account(filename=SA_KEY)
        self.sh = gc.open_by_url(url)

    def export(self, data, sheet_name):
        sheet = self.sh.worksheet(sheet_name)
        sheet.clear()
        data.fillna(0, inplace=True)
        data_columns = data.columns.to_list()
        data_list = data.to_numpy().tolist()
        data_all = [data_columns] + data_list
        sheet.update(data_all)
        print("[INFO]: Данные загружены в google sheet")

    def get_cost_price(self):
        sheet = self.sh.worksheet('Себестоимость')
        name = sheet.col_values(1)
        cost = sheet.col_values(2)
        cost[1:] = np.array([float(item.replace('\xa0', '').replace(' ', '')) for item in cost[1:]])
        data_cost_price = pd.DataFrame(cost, name)
        data_cost_price.reset_index(inplace=True)
        data_cost_price = data_cost_price.rename(columns=data_cost_price.iloc[0]).drop(data_cost_price.index[0])

        return data_cost_price

    def get_data(self, sheet_name):
        sheet = self.sh.worksheet(sheet_name)
        data = sheet.get_all_values()
        return data
