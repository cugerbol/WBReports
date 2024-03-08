from src.lib import *

class Report:
    
    
    def __init__(self,dateFrom,dateTo):
        
        self.dateFrom = dateFrom
        self.dateTo = dateTo
        self.data_aggregate = pd.DataFrame()
        self.data_details = pd.DataFrame()
        self.report = pd.DataFrame()

    
    def create_report(self,check_report = False):
        print("-"*65)
        self.report = pd.DataFrame()
        self.data_details = pd.DataFrame()
        
        for ID in self.data_aggregate["id"]:
            
            df_report = self.create_one_report(ID)
            self.report = pd.concat([self.report,df_report], ignore_index = True)
            
            if check_report == True:
                self.__check_one_report(df_r = df_report, df_a = self.data_aggregate, ID = ID)
                print("-"*65)

        self.__check_one_report(df_r = self.report, df_a = self.data_aggregate)
        return self.report

    
    
    def add_cost_price(self, cost_price):
        data = self.report.copy()
        data.rename(columns = {"Кол-во":"Продано, шт.", 
                           "Количество возврата":"Отказы,шт.",
                           "Количество доставок":"Заказано,шт."}, inplace = True)
    
        data_cp = cost_price.rename(columns = {cost_price.columns[0]:"Артикул поставщика"}).copy()
    
        dataframe = pd.merge(data, data_cp, on = "Артикул поставщика", how = "left")
        dataframe["Себестоимость"] = dataframe["Себестоимость"].infer_objects(copy=False).fillna(0)
      
        dataframe["Себестомость проданного товара"] = dataframe["Продано, шт."] * dataframe["Себестоимость"]
        dataframe['ОП'] = dataframe["Итого к оплате"] - dataframe["Себестомость проданного товара"]
      
        self.report2 = dataframe.sort_values(by = "ОП", ascending = False)
        return self.report2 


      
    
    def create_one_report(self,ID):
        data = pd.read_csv(f"data/{ID}.csv").fillna(0)
       # self.data_details = pd.concat([self.data_details,data], ignore_index = True)
        
        data.loc[data["Виды логистики, штрафов и доплат"] == "Возврат брака (К продавцу)",'Склад']  = "Возврат брака (К продавцу)"
      
        
        paidStorageSum = data["Хранение"].sum()
        penalty = data['Общая сумма штрафов'].sum()
        paidAcceptanceSum = data['Платная приемка'].sum()
        paidWithholdingSum = data['Удержания'].sum()
        
        columns = ['Цена розничная с учетом согласованной скидки',
                   'К перечислению Продавцу за реализованный Товар',
                   'Кол-во']

        data.loc[data["Тип документа"] == "возврат", 
                 columns] = data.loc[data["Тип документа"] == "возврат", columns].mul(-1)
        data.loc[data["Обоснование для оплаты"] == "логистика", 'Кол-во'] = 0

        dataframe = data[(data["Обоснование для оплаты"] == "логистика") |
                         (data["Обоснование для оплаты"] == "продажа") |
                         (data["Обоснование для оплаты"] == "возврат")].copy()

        ColumnsGroupBy = ['Поставщик','Дата продажи','Бренд','Артикул поставщика','Размер','Склад']
        
        ColumnsAgg = {'Цена розничная с учетом согласованной скидки':"sum",
                      'К перечислению Продавцу за реализованный Товар':"sum",
                      'Услуги по доставке товара покупателю':"sum",
                      'Количество доставок':"sum",
                      "Количество возврата":"sum",
                      "Кол-во":"sum"}
    
        dataframe = dataframe.groupby(ColumnsGroupBy).agg(ColumnsAgg).reset_index()
        
        quantity = dataframe[dataframe['Кол-во'] > 0]['Кол-во']
        TotalQuantity = dataframe[dataframe['Кол-во'] > 0]['Кол-во'].sum()
        
        dataframe["Хранение"] =  quantity / TotalQuantity * paidStorageSum
        dataframe['Прочие удержания'] = quantity / TotalQuantity * (penalty + paidAcceptanceSum + paidWithholdingSum)
        dataframe.fillna(0,inplace = True)
        
        defects_data = self.__defects(data)
        dataframe = pd.concat([dataframe,defects_data], ignore_index = True).fillna(0)
        
        dataframe['Итого к оплате'] = dataframe['К перечислению Продавцу за реализованный Товар'].sub(
            dataframe['Услуги по доставке товара покупателю']).sub(
            dataframe['Хранение']).sub(dataframe['Прочие удержания']).fillna(0)
        return dataframe

    
    
    def __defects(self,df):
        dataframe = pd.DataFrame()
        for col in ["Авансовая оплата за товар без движения","Частичная компенсация брака"]:
            data = df[(df['Обоснование для оплаты'] == col)].copy()
            ColumnsGroupBy = ["Бренд", "Артикул поставщика", "ШК", "Тип документа", "Дата продажи"]
            ColumnsAgg = {"Цена розничная с учетом согласованной скидки":"sum",
                      "К перечислению Продавцу за реализованный Товар":"sum",
                      "Кол-во":"mean"}
    
            data = data.groupby(ColumnsGroupBy).agg(ColumnsAgg).reset_index()
    
            ColumnsGroupBy = ["Бренд", "Артикул поставщика", "Дата продажи"]
            ColumnsAgg["Кол-во"] = "sum"
            columns = ['Бренд', 'Артикул поставщика', 'Склад','Дата продажи',
               'Цена розничная с учетом согласованной скидки',
               'К перечислению Продавцу за реализованный Товар','Кол-во'] 
        
            data = data.groupby(ColumnsGroupBy).sum(ColumnsAgg).reset_index()
            data['Склад'] = col
            dataframe = pd.concat([dataframe,data],ignore_index = True)
        return dataframe[columns]


    
    def get_data(self, sellers):
        if type(sellers) != list:
            sellers = [sellers]   
        print(f"[INFO]: Период: {self.dateFrom} - {self.dateTo}")
        for seller in sellers:
            print(f"[INFO]: {seller.name}","-"*65, sep = "\n")
            self.get_data_one_seller(seller)
            
        
    def get_data_one_seller(self,seller):
        NAME = seller.name
        COOKIE = seller.cookie
        URL = self.__create_url()
        
        print(f"[INFO]: get reports list",end = " - ")
        response = self.__send_get_request(url = URL, cookie = COOKIE)
        self.data_aggregate = self.__to_df_aggregate(response, NAME)
       
        for ID in self.data_aggregate["id"]:
            
            print(f"[INFO]: report id {ID}",end = " - ")
            self.__get_data_one_report(ID,COOKIE,NAME)
         
    
    def __get_data_one_report(self,ID,cookie,name):
        URL = self.__create_url(report_id = ID)
        if self.__check_data(ID) == True:
            dataframe = pd.read_csv(f"data/{ID}.csv")
            print("report exists")
        else:
            response = self.__send_get_request(url = URL,cookie = cookie)
            dataframe = self.__to_df_details(response,name)
            dataframe.to_csv(f'data/{ID}.csv', index=False)
        return dataframe

    
    def __check_data(self,ID):
        result = False
        file_list = os.listdir('data')
        if f"{ID}.csv" in file_list:
            result = True
        return result
    
    
    def __send_get_request(self, url, cookie, errors = 0):
        response = requests.get(url = url, headers = {"cookie" : cookie})
        sleep(2)
        if response.status_code != 200:
            print(response.status_code, end = " ")
            if errors > 5:
                print(f"\n{response.text}")
                exit(1)
            else:
                self.__send_get_request(url, cookie, errors = errors + 1)
        else:
            print(response.status_code)
        return response
        
        
    def __create_url(self,report_id = None):
        if report_id is None:
            url = f"https://seller-weekly-report.wildberries.ru/ns/reports/seller-wb-balance/api/v1/reports?dateFrom={self.dateFrom}&dateTo={self.dateTo}&limit=10&searchBy=&skip=0&type=5"
        else:
            url = f"https://seller-weekly-report.wildberries.ru/ns/reports/seller-wb-balance/api/v1/reports/{report_id}/details/archived-excel"
        return url
        
        
    def __to_df_details(self,response,seller_name):
        try:
            b = base64.b64decode(response.json()["data"]["file"], altchars=None)
            zf = zipfile.ZipFile(io.BytesIO(b), 'r')
            excel_file = zf.namelist()[0]
            with zf.open(excel_file) as f:
                dataframe = pd.read_excel(f)
                dataframe["Поставщик"] = seller_name
        except Exception as ex:
            print(f"[ERROR]: {ex}")
            exit()
        return dataframe
    
    
    def __to_df_aggregate(self,response,seller_name):
        try:
            dataframe = pd.DataFrame(response.json()["data"]["reports"])
            dataframe["dateFrom"] = dataframe["dateFrom"].apply(lambda x: x[:10])
            dataframe = self.__rename_df_aggregate(dataframe)
        except Exception as ex:
            print(f"[ERROR]: {ex}")
            exit()
        return dataframe
    
    
    def __rename_df_aggregate(self,dataframe):
        columns = {
          "createDate":"Дата формирования",
          "dateFrom" : "Дата начала",
          "dateTo" : "Дата конца",
          "totalSale" : "Продажа",
          "forPay" : "К перечислению за товар",
          "deliveryRub" : "Стоимость логистики",
          "paidStorageSum" : "Стоимость хранения",
          "penalty" : "Общая сумма штрафов",
          "paidWithholdingSum" : "Прочие удержания/выплаты",
          "paidAcceptanceSum" : "Стоимость платной приемки",
          "bankPaymentSum" : "Итого к оплате"
           }
        return dataframe.rename(columns = columns)
        
        
    def __check_one_report(self,df_r, df_a, ID = None):

        r = df_r.copy()
        a = df_a.copy()
        
        if ID is not None:
            print(f"[INFO]: report ID = {ID}")
        col_r = ["К перечислению Продавцу за реализованный Товар",
                 "Услуги по доставке товара покупателю",
                 "Хранение",
                 "Итого к оплате"]
        col_a = ["К перечислению за товар",
                 "Стоимость логистики",
                 "Стоимость хранения",
                 "Итого к оплате"]
        
        for i in range(len(col_r)):    
            if ID is None:
                va = round(a[col_a[i]].sum())
            else:
                va = round(a[a["id"] == ID][col_a[i]].sum())          
            vr = round(r[col_r[i]].sum())
            print(f" >> {col_a[i]}: [agg:{va}-rep:{vr}] = {round(va - vr)}") 

