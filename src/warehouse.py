from src.lib import *
from src.report import Report
from src.seller import Seller

class ReportWarehouse:
    
    data = []

    def __init__(self):
        self.url = f"https://seller.wildberries.ru/ns/balances/analytics-back/api/v1/balances-excel"
        self.body = {'filters': [
                    "brand",
                    "subject",
                    "supplierArticle",
                    "nmId",
                    "volume",
                    "barcode",
                    "techSize",
                    "quantityInTransitToClient",
                    "quantityInTransitFromClient",
                    "quantityForSaleTotal"], "dimension": 0}
        

    def get_data(self,seller,counter_error=1):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.1 Safari/605.1.15",
            "Cookie": seller.cookie2
            }
        
        while True:
            response = requests.post(url=self.url, json=self.body, headers=headers)
            sleep(2)
            
            if response.status_code == 200:
                print(response.status_code)
                data = base64.b64decode(response.json()['data']['file'], altchars=None)
                self.data = pd.read_excel(BytesIO(data) , engine="openpyxl")
                

            else:
                print(response.status_code, end = ' ')
                if counter_error > 5:
                    raise Exception("[ERROR]: Совершено более 5 неудачных запросов. Вызвано исключение!")
                    
                counter_error +=1
                self.get_data(seller,counter_error = counter_error).fillna(0)
           
            return self.data
                
def show_results(report):
    print("[INFO]: Итого")
    print("-"*65)
    print(report.report[["Цена розничная с учетом согласованной скидки",
               "К перечислению Продавцу за реализованный Товар",
               "Услуги по доставке товара покупателю",
               "Заказано,шт.",
               "Отказы,шт.",
               "Продано, шт.",
               "Хранение",
               "Прочие удержания",
               "Итого к оплате",
               "ОП"]].sum())
    print("-"*65)


def main(table, seller, show_erros, count_days, show_total_erros):
    print("Ввести даты в формате dd.mm.yyyy. Или нажать 2 раза на кнопку ENTER, тогда будут получены отчеты за неделю")
    sleep(1)
    dateFrom = input("Дата начала периода отчетов: ")
    dateTo = input("Дата конца периода отчетов: ")
    print("-"*50)
    if dateFrom == "" or dateTo == "":
        dateFrom = (date.today() - timedelta(days=count_days)).strftime("%d-%m-%Y").replace("-", ".")
        dateTo = (date.today() - timedelta(days=1)).strftime("%d-%m-%Y").replace("-", ".")
    
    report = Report(dateFrom = dateFrom, dateTo = dateTo) 
    cost_price = table.get_cost_price()

    report.get_data(sellers = seller, show_errors = show_erros, show_total_erros = show_total_erros)
    report.create_report(cost_price = cost_price)
    
    return report