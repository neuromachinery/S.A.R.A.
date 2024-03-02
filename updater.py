import gspread
from os import path
from sys import argv
import json
def append_and_index(value:str,dictionary:dict,value_type):
    index = str(len(dictionary[value_type]))
    dictionary[value_type][value]=index
    return index
def main(key,filename="DATA"):
    CWD = path.dirname(argv[0])
    try:gc = gspread.service_account(filename=path.join(CWD,"service_account.json"))
    except FileNotFoundError:
        print("Нет сервисного аккаунта. Спросите разраба :)")
        input()
        quit()
    sh = gc.open_by_key(key)

    GROUPS = ["CITIES","TYPE","JOBS","PROMO"]
    DATA = {}
    ENCODING_DICTIONARY = {}
    for group in GROUPS:
        ENCODING_DICTIONARY[group] = {}

    IncomeSheet = sh.get_worksheet(1)
    PromoSheet = sh.get_worksheet(2)

    Income_data = IncomeSheet.get_values()
    Promo_data = PromoSheet.get_values()

    Income_data = Income_data[1:]
    Promo_data = Promo_data[1:]

    getindex = lambda val,val_type:ENCODING_DICTIONARY[val_type][val.upper()] if val.upper() in ENCODING_DICTIONARY[val_type] else append_and_index(val.upper(),ENCODING_DICTIONARY,val_type)
    getindexlist = lambda vals,val_types:map(getindex,vals,val_types)

    cities = IncomeSheet.col_values(1)
    cities.pop(0)
    for city in cities:
        city_index = getindex(city,GROUPS[0]) # city
        DATA[city_index] = {}

    for row in Income_data:
        [city,job] = getindexlist([row[0],row[2]],[GROUPS[0],GROUPS[2]]) #city & job
        data = [getindex(row[1],GROUPS[1])] # TYPE
        data.extend(row[3:6])
        data.append({})
        DATA[city][job] = data

    for row in Promo_data:
        if(row[2] == "Пеший/вело курьер"): # its a bodge, because db is stupid
            job = getindex("Пеший курьер","JOBS")
            row[2] = "Пеший курьер"
            [city,_,_,promo] = getindexlist(row[:4],GROUPS) #all
            DATA[city][job][-1][promo] = row[4]
            job = getindex("Велокурьер","JOBS")
            row[2] = "Велокурьер"
            [city,_,_,promo] = getindexlist(row[:4],GROUPS) #all
            DATA[city][job][-1][promo] = row[4]
        else:
            [city,_,job,promo] = getindexlist(row[:4],GROUPS) #all
            DATA[city][job][-1][promo] = row[4]
    DATA["DECODE"]=ENCODING_DICTIONARY
    with open("{}\{}".format(CWD,"%s.json"%filename), "w", encoding="UTF-8") as f: 
        json.dump(DATA,f,ensure_ascii=False)
    return DATA
if __name__ == "__main__":
    print(main("KEY_HERE")) # for testing purposes
