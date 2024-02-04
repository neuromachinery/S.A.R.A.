from windows_toasts import Toast, WindowsToaster
from tkinter import Tk, Entry, Label, Button, StringVar, Frame#, Radiobutton
from tkinter.ttk import Combobox
import os
import json
import datetime
import threading

import updater
import BreakGrabber

DATE = datetime.datetime.now().strftime("%d.%m")
OPNAME = ""
CWD = os.path.realpath(os.path.dirname(__name__))
DATA_FILENAMES = ["DATA","client_secrets"]
DATA = {}
TIMER_DATA = []
DATA_FIELDS = [
    "тип позиции",
    "доход за час",
    "доход за смену",
    "доход за месяц",
    "гарант. доход",
    "акция"
]
QUESTIONS = [
    "Возраст",
    "Android",
    "Гражданство",
    "Авто",
    "Адрес"
]
ALIASES = {
    "МО":"Московская область",
    "МСК":"Москва",
    "НН":"Нижний Новгород",
    "СПБ":"Санкт-Петербург",
    "ЛО":"Ленинградская область"  
}
TAG_COLORS = {
    # Key to bind : tk color
    "<Button-1>":"lime",
    "<Button-2>":"yellow",
    "<Button-3>":"salmon",
    "<Button-4>":"lightgrey",
    "<Button-5>":"cyan"
}
def UpdateData():
    global DATA
    DATA = updater.main(GOOGLE_SHEETS_KEY)
def UpdateTimer():
    global TIMER_DATA
    TIMER_DATA = BreakGrabber.main(BREAK_SHEETS_KEY,OPNAME)
def JSONLoad(filename,cwd=CWD):	
    path = "{}\{}.json".format(cwd,filename)
    with open(path, "r",encoding="UTF-8") as f:
        data = json.load(f)
    return data
    
def JSONSave(filename,cwd=CWD,data=DATA):
    path = "{}\{}.json".format(cwd,filename)
    with open(path, "w", encoding="UTF-8") as f: 
        json.dump(data,f,ensure_ascii=False)
try:SECRETS = JSONLoad(DATA_FILENAMES[1])
except FileNotFoundError:
    client_secrets = {"installed":{},"GOOGLE_SHEETS_KEY":"","BREAK_SHEETS_KEY":""}
    for thing in ["GOOGLE_SHEETS_KEY","BREAK_SHEETS_KEY"]:
        print(f"Enter {thing}: ",end="")
        client_secrets[thing] = input()
    for thing in ["client_id","project_id","auth_uri","token_uri","auth_provider_x509_cert_url","client_secret"]:
        print(f"Enter {thing}: ",end="")
        client_secrets["installed"][thing] = input()
    client_secrets["installed"]["redirect_uris"] = ["http://localhost"]
    SECRETS = client_secrets
    JSONSave("client_secrets",data=client_secrets)
GOOGLE_SHEETS_KEY = SECRETS["GOOGLE_SHEETS_KEY"]
BREAK_SHEETS_KEY = SECRETS["BREAK_SHEETS_KEY"]

THREADS = set()
DataFlag = threading.Event()
TimerDataFlag = threading.Event()
DoneFlag = threading.Event()
KillFlag = threading.Event()
def UpdateThread(flag:threading.Event,func):
    while True:
        if(KillFlag.is_set()):break
        if(flag.wait(2.0)):
            func()
            flag.clear()
            DoneFlag.set()
        
DataThread = threading.Thread(target=UpdateThread,args=(DataFlag,UpdateData))
THREADS.add(DataThread)
TimerThread = threading.Thread(target=UpdateThread,args=(TimerDataFlag,UpdateTimer))
THREADS.add(TimerThread)
for thread in THREADS:
    thread.start()

try:DATA = JSONLoad(DATA_FILENAMES[0])
except FileNotFoundError:
    DataFlag.set() # signal for data update
    DoneFlag.wait() # wait for it to finish
    DoneFlag.clear()

ENCODE_DICTIONARY = DATA["DECODE"]
MUTED = False # Flag for being muted
TOASTER = WindowsToaster('S.A.R.A User Interface')
HIGHLIGHTED_FRAME = None

MODE = False
window = Tk()
window.title("S.A.R.A User Interface")
window.geometry("560x170")
#window.geometry("1024x600")
MainFrame = Frame(window)
MainFrame.pack(fill="both",expand=1,padx=3,pady=3)
TopFrame = Frame(MainFrame,relief="solid",borderwidth=2)
TopFrame.pack(side="top",fill="both",expand=1)
UtilitiesFrame = Frame(MainFrame,relief="solid",borderwidth=2)
UtilitiesFrame.pack(side="top",anchor="s",fill="x",pady=(2,0))

def callback(event):
    MainFrame.focus_set()
MainFrame.bind("<Button-1>",callback)
LeftFrame = Frame(TopFrame)
RButtonsFrame = Frame(LeftFrame,relief="solid",borderwidth=2)
ButtonsFrame = Frame(LeftFrame)

RightFrame = Frame(TopFrame,relief="solid",borderwidth=1)
InfoFrame = Frame(RightFrame,relief="solid",borderwidth=1)
InfoTopFrame = Frame(InfoFrame,relief="solid",borderwidth=1)
InfoBottomFrame = Frame(InfoFrame,relief="solid",borderwidth=1)

InfoLabelFramesFrame = Frame(InfoBottomFrame)
InfoVars = []
for field in DATA_FIELDS:
    InfoVar = StringVar(value="пусто")
    InfoVars.append(InfoVar)
    InfoLabelFrame = Frame(InfoLabelFramesFrame)
    InfoLabel = Label(InfoLabelFrame,text=field,relief="solid",borderwidth=1)
    InfoVarLabel = Label(InfoLabelFrame,textvariable=InfoVar,relief="solid",borderwidth=1)
#InfoLabelFillFrame = Frame(InfoFrame,relief="solid",borderwidth=1)
InfoCityFrame = Frame(InfoTopFrame,relief="solid",borderwidth=1)
InfoCityLabel = Label(InfoCityFrame,text="Введите город",relief="solid",borderwidth=1)
InfoCityEntry = Entry(InfoCityFrame)
InfoJobFrame = Frame(InfoTopFrame,relief="solid",borderwidth=1)
InfoJobLabel = Label(InfoJobFrame,text="Выберите позицию",relief="solid",borderwidth=1)
InfoJobCombo = Combobox(InfoJobFrame,values=list(ENCODE_DICTIONARY["JOBS"].keys()))
InfoJobCombo["state"] = "readonly"


def Notify(text_fields:list):
    if(MUTED):return
    toast = Toast(text_fields)
    TOASTER.show_toast(toast)
def Mute():
    global MUTED
    if(not MUTED):
        MuteButton.configure(text="Включить уведомления")
    else:
        MuteButton.configure(text="Выключить уведомления")
    MUTED = not MUTED
def CheckAliases(text):
    try:return ALIASES[text]
    except KeyError:return text
def CheckCity(city):
    try:return str(ENCODE_DICTIONARY["CITIES"][city])
    except ValueError:return None
    except KeyError: return None
def InfoGet():
    City = CheckAliases(InfoCityEntry.get().upper()).upper()
    City = CheckCity(City)
    if(not City):
        for var in InfoVars:
            var.set("Нет города")
        return
    Job = InfoJobCombo.get()
    try:
        info = DATA[City][ENCODE_DICTIONARY["JOBS"][Job]]
    except KeyError:
        return
    else:
        #if("#N/A" in info):info[info.index("#N/A")]="Нет"
        if(len(info[-1])<len(ENCODE_DICTIONARY["PROMO"])):
            key = "0" if list(info[-1].keys())[0]=="1" else "1"
            info[-1][key] = "Нет"
        displayInfo = info.copy()
        displayInfo.append(displayInfo[4]["1"])
        displayInfo[4] = displayInfo[4]["0"]
        displayInfo[0] = list(ENCODE_DICTIONARY["TYPE"].keys())[int(displayInfo[0])]
    
    for i in range(len(displayInfo)):
        InfoVars[i].set(displayInfo[i])
def InfoPaste():
    InfoCityEntry.delete(0,len(InfoCityEntry.get()))
    InfoCityEntry.insert(0,window.clipboard_get())
def InfoUpdate():
    DataFlag.set() # signal for data update
    GenericCleanUI(RightFrame)
    PageOperationRightUI()
def InfoChangeColor(event=None,button=None,Color=None):
    button.configure(bg=Color)
InfoGetButtonFrame = Frame(InfoTopFrame,relief="solid",borderwidth=1)
InfoGetButton = Button(InfoGetButtonFrame,text="Обновить значения",command=InfoGet)
InfoButtonsFrame = Frame(RightFrame,relief="solid",borderwidth=1)
InfoClearPasteButonsFrame = Frame(InfoButtonsFrame,relief="solid",borderwidth=1)
InfoPasteButton = Button(InfoClearPasteButonsFrame,text="Вставить",command=InfoPaste)
InfoClearButton = Button(InfoClearPasteButonsFrame,text="Очистить",command=lambda:InfoCityEntry.delete(0,len(InfoCityEntry.get())))
InfoFillFrame = Frame(InfoButtonsFrame,relief="solid",borderwidth=1)
InfoUpdateButtonFrame = Frame(InfoTopFrame,relief="solid",borderwidth=1)
InfoUpdateButton = Button(InfoUpdateButtonFrame,text="Обновить базу данных",command=InfoUpdate)
InfoTagButtonsFrame = Frame(InfoButtonsFrame,relief="solid",borderwidth=1)
for question in QUESTIONS:
    InfoTagButton = Label(InfoTagButtonsFrame,text=question,bg="lime")
    for key, color in TAG_COLORS.items():
        InfoTagButton.bind(key, lambda event,button=InfoTagButton,color=color:InfoChangeColor(event,button=button,Color=color))
    

FillFrame = Frame(RightFrame,relief="solid",borderwidth=1)

StatusFrame = Frame(ButtonsFrame,relief="solid",borderwidth=2)

RBLabel = Label(StatusFrame,text="Выберите статус в меню слева")

MuteButtonFrame = Frame(UtilitiesFrame,relief="solid",borderwidth=1)
MuteButtonFrame.pack(side="right",anchor="s")
MuteButton = Button(MuteButtonFrame,text="Выключить уведомления", command=Mute)
MuteButton.pack(side="right",anchor="s",padx=2,pady=2)

def GetTime():
    now = datetime.datetime.now()
    date = now.date()
    time = now.time()
    window.clipboard_clear()
    window.clipboard_append("{}-{} {}:{}".format(date.day,date.month,time.hour,time.minute))
TimeGetFrame = Frame(UtilitiesFrame,relief="solid",bd=1)
TimeGetButton = Button(TimeGetFrame,text="Скопировать время",command=GetTime)
TimeGetFrame.pack(side="right",anchor="s")
TimeGetButton.pack(side="right",anchor="s",padx=2,pady=2)

def PageTimersUI():
    global TIMER_DATA
    GenericCleanUI(RightFrame)
    TimerSettingsFrame.pack(side="top",fill="both",expand=1)
    if(not TimerSettingsFrame.winfo_children()):
        if(len(TIMER_DATA)==0):
            Label(TimerSettingsFrame,text=f"Перерывы сотрудника '{OPNAME}' не найдены на {DATE}").pack(side="top",anchor="w")
            return
        for i in range(len(TIMER_DATA)):
            TimerAdd(i)
        Button(TimerSettingsFrame,text="Обновить",command=TimerUpdate).pack(side="top",anchor="w")

def TimerUpdate():
    TimerDataFlag.set() # signal for timer update
    GenericCleanUI(TimerSettingsFrame, soft=False)
    PageTimersUI()
    
TimerSetupFrame = Frame(UtilitiesFrame,relief="solid",bd=1)
TimerSetupFrame.pack(side="right",anchor="s")
TimerSettingsFrame = Frame(RightFrame)
def TimerAdd(index):
    TimerFrame = Frame(TimerSettingsFrame)
    TimerFrame.pack(side="top",anchor="w")
    Label(TimerFrame,text=f"Начало перерыва в {TIMER_DATA[index][0]}:{TIMER_DATA[index][1] if TIMER_DATA[index][1]>9 else f'0{TIMER_DATA[index][1]}'}.").pack(side="left",anchor="s")

def Clocks():
    global TIMER_DATA
    time = datetime.datetime.now().time()
    string = time.strftime('%H:%M:%S')
    Clock.config(text=string)
    if(string in set([datetime.time(hours,minutes).isoformat("seconds") for hours, minutes in TIMER_DATA])):
        Notify(["ПЕРЕРЫВ","На 15 минут"]) 
        Clock.after(900000,Notify,["ПЕРЕРЫВ","Ваш перерыв закончился!"])
    Clock.after(1000,Clocks)
ClockFrame = Frame(UtilitiesFrame,relief="solid",bd=1)
Clock = Label(ClockFrame,font=("Times New Roman",14,"bold"))
ClockFrame.pack(side="left",anchor="s",fill="y")
Clock.pack(side="left",anchor="center")

EmptySpaceFrame = Frame(UtilitiesFrame,relief="solid",bd=1)
EmptySpaceFrame.pack(side="left",fill="both",expand=1)

NameLabel = Label(TopFrame,text="Имя оператора в чате")
NameEntry = Entry(TopFrame,width=50)
GroupLabel = Label(TopFrame, text="Группа оператора")
GroupCombobox = Combobox(TopFrame,width=15)
GroupCombobox["values"] = ["группа-1","группа-2"]
GroupCombobox['state'] = 'readonly'
""" # reserved for telegram integration
def StatusClearUI():
    for widget in StatusFrame.winfo_children():
        widget.pack_forget()
def TroubleShooting():
    StatusClearUI()
    PageOperationDescriptionUI()
def Post():
    StatusClearUI()
    PageOperationDescriptionUI()
def Break():
    StatusClearUI()
    PageOperationBreakUI()
def Manual():
    StatusClearUI()
    PageOperationDescriptionUI()
def StatusBreakComboCallback(event):
    if(StatusBreakCombo.get()==StatusBreakCombo['values'][-1]):
        StatusBreakEntry.pack(side="left",anchor="n")
    else:
        StatusBreakEntry.pack_forget()
Statuses = {"тех":TroubleShooting, "пост":Post, "перерыв":Break, "руч":Manual}
Status = StringVar()
StatusSendFrame = Frame(ButtonsFrame,relief="solid",borderwidth=2)
StatusSend = Button(StatusSendFrame,text="Отправить статус")

StatusDescriptionFrame = Frame(StatusFrame)
StatusDescriptionLabel = Label(StatusDescriptionFrame,text="Описание статуса")
StatusDescriptionEntry = Entry(StatusDescriptionFrame)

StatusBreakLabel = Label(StatusFrame,text="Период перерыва")
StatusBreakFrame = Frame(StatusFrame)
StatusBreakCombo = Combobox(StatusBreakFrame,width=7)
StatusBreakCombo["values"] = [5,10,15,20,30,40,"другое"]
StatusBreakCombo["state"] = 'readonly'
StatusBreakCombo.bind('<<ComboboxSelected>>', StatusBreakComboCallback)
StatusBreakEntry = Entry(StatusBreakFrame)
"""



def PageCleanUI():
    for widget in TopFrame.winfo_children():
        widget.pack_forget()
def PageSetupUI():
    NameLabel.pack(side="top",anchor="w",padx=2,pady=2)
    NameEntry.pack(side="top",anchor="w",padx=2,pady=2)
    GroupLabel.pack(side="top",anchor="w",padx=2,pady=2)
    GroupCombobox.pack(side="top",anchor="w",padx=2,pady=2)
    OperationButton.pack(side="top",anchor="w",padx=2,pady=2)
def PageOperationRightUI():
    InfoButtonsFrame.pack(side="top",fill="x")
    InfoClearPasteButonsFrame.pack(side="left",anchor="n",fill="y")
    InfoPasteButton.pack(side="left",anchor="n",padx=2,pady=2)
    InfoClearButton.pack(side="left",anchor="n",padx=2,pady=2)
    InfoTagButtonsFrame.pack(side="left",anchor="n",fill="y")
    for button in InfoTagButtonsFrame.winfo_children():
        button.pack(side="left",anchor="n",padx=2,pady=2,fill="y")
    InfoFillFrame.pack(side="left",anchor="n",fill="both",expand=1)
    FillFrame.pack(side="top",anchor="w",fill="both",expand=1)
    
    InfoFrame.pack(side="top",anchor="w",fill="both")
    InfoTopFrame.pack(side="top",anchor="w",fill="both")
    InfoBottomFrame.pack(side="top",anchor="w",fill="both")
    InfoCityFrame.pack(side="left",anchor="s",fill="y")
    InfoCityLabel.pack(side="top",anchor="s",fill="both",ipadx=1)
    InfoCityEntry.pack(side="top",anchor="s",ipadx=1)
    InfoJobFrame.pack(side="left",anchor="s",fill="y")
    InfoJobLabel.pack(side="top",anchor="s",fill="both",ipadx=1)
    InfoJobCombo.pack(side="top",anchor="s",fill="both",ipadx=1)
    InfoGetButtonFrame.pack(side="left",anchor="s",fill="y")
    InfoGetButton.pack(side="left",anchor="s",padx=2,pady=2,fill="y")
    InfoUpdateButtonFrame.pack(side="left",anchor="n",fill="y")
    InfoUpdateButton.pack(side="left",anchor="n",padx=2,pady=2,fill="y")

    InfoLabelFramesFrame.pack(side="left",anchor="n",fill="both",expand=1)
    for frame in InfoLabelFramesFrame.winfo_children():
        frame.pack(side="left",anchor="n",fill="both",expand=1)
        frame.winfo_children()[0].pack(side="top",anchor="n",fill="both",expand=1)
        frame.winfo_children()[1].pack(side="top",anchor="n",fill="both",expand=1)
    #InfoLabelFillFrame.pack(side="left",anchor="n",fill="both",expand=1)
def PageOperationRBUI():
    LeftFrame.pack(side="left",anchor="n",fill="both")
    RightFrame.pack(side="left",anchor="n",fill="both",expand=1)
    """ # reserved for later telegram integration
    RButtonsFrame.pack(side="top",fill="x")
    ButtonsFrame.pack(side="top",fill="both",expand=1)
    for RButton in Statuses:
        StatusRadiobutton = Radiobutton(RButtonsFrame, text=RButton,value=RButton,variable=Status,command=Statuses[RButton])
        StatusRadiobutton.pack(side="top",anchor="w",padx=(5,2))
    StatusSendFrame.pack(side="top",anchor="w",fill="x")
    StatusSend.pack(side="top",anchor="w",padx=2,pady=2)
    StatusFrame.pack(side="top",anchor="w",fill="both",expand=1)
    RBLabel.pack(side="top",anchor="w")
    """
    PageOperationRightUI()
""" # reserved for later telegram integration
def PageOperationDescriptionUI():
    StatusDescriptionFrame.pack(side="left",anchor="n",fill="both",expand=1)
    StatusDescriptionLabel.pack(side="top",anchor="w",padx=2,pady=2)
    StatusDescriptionEntry.pack(side="top",anchor="w",padx=2,pady=2)
def PageOperationBreakUI():
    StatusBreakLabel.pack(side="top",anchor="w",padx=2,pady=2)
    StatusBreakFrame.pack(side="top",anchor="w",padx=2,pady=2,fill="both",expand=1)
    StatusBreakCombo.pack(side="top",anchor="w",padx=2,pady=2)
"""
def OperationUI():
    global OPNAME
    global DATA
    OPNAME = NameEntry.get()
    DATA["USER"] = [OPNAME]
    JSONSave(DATA_FILENAMES[0],data=DATA)
    TimerDataFlag.set() # signal for timer update
    PageCleanUI()
    PageOperationRBUI()
OperationButton = Button(TopFrame,text="Начать",command=OperationUI)

def GenericCleanUI(widget,soft=True):
    if(soft): 
        for child in widget.winfo_children():child.pack_forget()
    else: 
        for child in widget.winfo_children():child.destroy()
def ChangeModeUI():
    global MODE
    GenericCleanUI(RightFrame)
    if(MODE):
        ModeStringVar.set("Посмотреть перерывы")
        PageOperationRightUI()
    else:
        ModeStringVar.set("Режим доходов")
        PageTimersUI()
    MODE = not MODE
ModeStringVar = StringVar(value="Посмотреть перерывы")
ModeFrame = Frame(UtilitiesFrame,relief="solid",bd=1)
ModeButton = Button(ModeFrame,command=ChangeModeUI,textvariable=ModeStringVar)
ModeFrame.pack(side="right",anchor="s")
ModeButton.pack(side="right",anchor="s",padx=2,pady=2)
Clocks()
try: 
    OPNAME = DATA["USER"][0]
    TimerDataFlag.set() # signal for timer update
    PageOperationRBUI()
except KeyError: PageSetupUI()

def Exit():
    KillFlag.set()
    for thread in THREADS:
        thread.join()
try:window.mainloop()
except KeyboardInterrupt: 
    Exit()
    quit()
except Exception as E:
    Exit()
    raise E
finally:
    Exit()
    quit()
