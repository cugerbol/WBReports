from lib import *

class Seller:
    
    
    def __init__(self):
        with open('config.yml', 'r') as file:
            self.configs = yaml.safe_load(file)
        self.set_cookie()
        self.set_name()
    
    
    def set_name(self,name = None):
        if name is None:
            self.name = self.configs["sellerName"]
        else:
            self.name = name
            
            
            
    def set_cookie(self,supplier_id = None):
        try:
            with open('cookie.p', 'rb') as file:
                data = pickle.load(file)  
                
            if supplier_id is None:
                supplier_id = data["x-supplier-id-external"]
               # supplier_id = self.configs["supplierId"]
    
            self.cookie = f"wbx-validation-key={data['wbx-validation-key']}; x-supplier-id-external={supplier_id}; WBTokenV3={data['WBTokenV3']};"
        
            self.cookie2= f"wbx-validation-key={data['wbx-validation-key']}; x-supplier-id={supplier_id}; WBTokenV3={data['WBTokenV3_2']};"
            
        except Exception as ex:
            self.update_cookie()
                
        
        
    def update_cookie(self):
        print("[INFO]: update cookie")
        cookieValues = self.__get_cookie()
        data = {"wbx-validation-key" : cookieValues['wbx-validation-key'], 
                "x-supplier-id-external" : cookieValues['x-supplier-id-external'],
                "WBTokenV3" : cookieValues['WBTokenV3'],
                "WBTokenV3_2": cookieValues['WBTokenV3_2']
               }
        with open('cookie.p', 'wb') as file:
            pickle.dump(data, file)
        self.set_cookie()
        
    
    def __get_cookie(self):
        sellersCookie = dict()
        cj = browsercookie.chrome()
        for cookie in cj:
            if cookie.domain == "seller.wildberries.ru" and "supplier" in cookie.name:
                sellersCookie["x-supplier-id-external"]= cookie.value
                
            if cookie.domain == "seller-weekly-report.wildberries.ru" and cookie.name == 'WBTokenV3':
                sellersCookie["WBTokenV3"] = cookie.value
                
            if cookie.domain == "seller.wildberries.ru" and cookie.name == 'WBTokenV3':
                sellersCookie["WBTokenV3_2"] = cookie.value
                
            if cookie.name == "wbx-validation-key":
                sellersCookie["wbx-validation-key"] = cookie.value
                
       # print(f'[INFO]: sup_id: {sellersCookie["x-supplier-id-external"]}')
        return sellersCookie
    
    
    def check_cookie(self, count_error = 0):
        url = f"https://seller-weekly-report.wildberries.ru/ns/reports/seller-wb-balance/api/v1/reports-weekly?limit=5&searchBy=&skip=0&type=5"
        response = requests.get(url = url, headers = {"cookie":self.cookie})
        if response.status_code == 200:
            print("[INFO]: Авторизация прошла успешно")
        elif count_error < 3:
            print("[ERROR]: Требуется обновить данные cookie")
            self.update_cookie()
            self.check_cookie(count_error = count_error + 1)
        else:
            print("[ERROR]: Ошибка авторизации")
                                
    