import gspread
import re
from datetime import datetime
DATE = datetime.now().strftime("%d.%m")
def append_and_index(value:str,dictionary:dict,value_type):
    index = str(len(dictionary[value_type]))
    dictionary[value_type][value]=index
    return index
def find_worksheet(sh):
    for worksheet in sh.worksheets():
        if(DATE in worksheet.title):
            return worksheet
    return 0
def main(key,name:str):
    try:gc = gspread.service_account()
    except FileNotFoundError:
        print("No service account.")
        input()
        quit()
    sh = gc.open_by_key(key)
    worksheet = find_worksheet(sh)
    if(not worksheet): 
        print("Worksheet have not been found")
        raise KeyError
    #pattern = name
    #pattern = re.compile("^(?=.*{0})(?=.*{1})(?=.*{2})".format(*name.split()))
    pattern = re.compile(f"^{''.join([f'(?=.*{word})' for word in name.split()])}")
    try:
        data = worksheet.row_values(worksheet.find(pattern,in_column=1).row)
    except AttributeError:
        print("Breaks have not been found")
        raise KeyError
    OFFSET = 4 # offset from 00:00

    breakIndexes = [i-2 for i, x in enumerate(data) if x == "0"]
    breakTime =  [divmod(i,4) for i in breakIndexes]
    breakTime = [(h+OFFSET,m*15) for h,m in breakTime if h*4+m/15]
    return breakTime

if __name__ == "__main__":
    print(main("KEY_HERE","NAME_HERE")) # for testing purposes
