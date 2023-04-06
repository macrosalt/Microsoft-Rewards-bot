import json
import os

LOG_PREFIX = "log_"

LOG_TO_INSTANCE = {
    "1": "o-ubuntu",
    "2": "o-opc",
    "3": "msr001",
    "4": "us2",
    "5": "us3",
    "6": "us32",
    "7": "us4",
    "8": "us42",
    "9": "us43",
    "10": "us5",
    "11": "us41",
    "12": "us51",
    "13": "us52",
    "14": "us53",
    "15": "us6",
    "16": "us61",
    "17": "msr_free",
    "18": "salt.li_free"
}

MACHINE_TO_ACCOUNT = {
    #template
    "": {           
        "edge":"",
        "chrome":"",
        "firefox":"",
        "yandex":"",
        "opera":"",
        "vivaldi":"",
        "comodo_icedragon":"",
        "slimbrowser":"",
        "maxthon":"",
        "waterfox":"",
        "brave":"",
        "seamonkey":"",
        "lunascape":"",
        "midori":"",
        "ur":"",
        "pale_moon":"",
        "srware_iron":"",
        "slimjet":"",
        "avg":"",
        "liebao":"",
        "cent":"",
        "theworld":"",
    },
    "macP_win1022H2": {           
        "edge":"lysdgrmr@outlook.com",
        "chrome":"ktlftboh@outlook.com",
        "firefox":"smcinqjj@outlook.com",
        "yandex":"bncpiwkk@outlook.com",
        "opera":"glggvmgc@outlook.com",
        "vivaldi":"gcxdrwqd@outlook.com",
        "comodo_icedragon":"qcumuyjj@outlook.com",
        "slimbrowser":"gimfumsk@outlook.com",
        "maxthon":"ookknadg@outlook.com",
        "waterfox":"pmceuitf@outlook.com",
        "brave":"tpsgjuvw@outlook.com",
        "seamonkey":"ynhudhwm@outlook.com",
        "lunascape":"ztbsqsft@outlook.com",
        "midori":"unfdhqgm@outlook.com",
        "ur":"vckoyirs@outlook.com",
        "pale_moon":"mlfyfjgw@outlook.com",
        "srware_iron":"tlwesqjg@outlook.com ",
        "slimjet":"oxutorhw@outlook.com",
        "avg":"dcpnzssa@outlook.com",
        "liebao":"ardjjelo@outlook.com",
        "cent":"elftxvvs@outlook.com",
        "theworld":"",
    },
    "miHyper_win1022H2": {           
        "edge":"pyizsvhy@outlook.com",
        "chrome":"fvevijqg@outlook.com",
        "firefox":"",
        "yandex":"huqafhdp@outlook.com",
        "opera":"rjkiwmjl@outlook.com",
        "vivaldi":"ejvkbmpr@outlook.com",
        "comodo_icedragon":"wdkdqndc@outlook.com",
        "slimbrowser":"bnhrqspr@outlook.com",
        "maxthon":"coprnbbt@outlook.com",
        "waterfox":"qnxwkvcs@outlook.com",
        "brave":"joothsto@outlook.com",
        "seamonkey":"wgdzzlnm@outlook.com",
        "lunascape":"dicxdycq@outlook.com",
        "midori":"pjysssqw@outlook.com",
        "ur":"vqkufecw@outlook.com",
        "pale_moon":"",
        "srware_iron":"fudxyrsc@outlook.com",
        "slimjet":"spxbtglt@outlook.com",
        "avg":"lfsqfgnp@outlook.com",
        "liebao":"rtwumktx@outlook.com",
        "cent":"nipexfsj@outlook.com",
        "theworld":"nhywkmfn@outlook.com",
    },
    "miHyper_win7": {           
        "edge":"fcbsqnjg@outlook.com",
        "chrome":"cthinvmh@outlook.com",
        "firefox":"hkxeycss@outlook.com",
        "yandex":"jboqcenv@outlook.com",
        "opera":"fxfyxblj@outlook.com",
        "vivaldi":"wcpxwrcn@outlook.com",
        "comodo_icedragon":"wigpbsoy@outlook.com",
        "slimbrowser":"rvyujeks@outlook.com",
        "maxthon":"iebtfdkf@outlook.com",
        "waterfox":"emqovroe@outlook.com",
        "brave":"iejvease@outlook.com",
        "seamonkey":"",
        "lunascape":"",
        "midori":"",
        "ur":"",
        "pale_moon":"",
        "srware_iron":"",
        "slimjet":"",
        "avg":"",
        "liebao":"",
        "cent":"",
        "theworld":"",
    },
    "mac_origin": {           
        "chrome":"ymizpwly@outlook.com",
        "chrome2":"wotfvcat@outlook.com",
        "safari":"jmbltatj@outlook.com",
        "brave":"febgcblg@outlook.com",
    },
}

MACHINE_PRIORITY = {
    "macP_win1022H2": 1,
    "miHyper_win1022H2": 2,
    "miHyper_win7":3,
    "mac_origin": 4,
}

ACCOUNT_TO_MACHINE = {}

def init_account_to_machine_for_once():
    if len(ACCOUNT_TO_MACHINE) != 0:
        return
    for machine, browser_to_account in MACHINE_TO_ACCOUNT.items():
        if len(machine) == 0:
            continue
        for browser, account in browser_to_account.items():
            ACCOUNT_TO_MACHINE[account] = {
                "browser": browser,
                "machine": machine,
            }



ACCOUNT_REGION = {
}

class LogFile:
    def __init__(self, name, content):
        self.file_name = name
        self.json_obj = content

def get_log_location(file_name):
    start = len(LOG_PREFIX)
    file_index = file_name[start:]
    if file_index in LOG_TO_INSTANCE:
        return f'instance: {LOG_TO_INSTANCE[file_index]}'
    return f'log: {file_name}'

def get_account_region(account):
    if account in ACCOUNT_REGION:
        return ACCOUNT_REGION[account]
    return "us"

def get_account_machine(account):
    init_account_to_machine_for_once()
    if account not in ACCOUNT_TO_MACHINE:
        return ""
    account_info = ACCOUNT_TO_MACHINE[account]
    return f'[{account_info["machine"]}][{account_info["browser"]}]'

def get_account_priority(account):
    init_account_to_machine_for_once()
    if account not in ACCOUNT_TO_MACHINE:
        return 0
    machine = ACCOUNT_TO_MACHINE[account]["machine"]
    if len(machine) == 0:
        print("[ERROR]", "account:", account, "has invalid 'machine' field configured in ACCOUNT_TO_MACHINE")
        return 0
    
    if machine not in MACHINE_PRIORITY:
        print("[ERROR]", "machine:", machine, "is not configured in MACHINE_PRIORITY")
        return 0
    return MACHINE_PRIORITY[machine]

def read_logs_to(func):
    '''
    call the internal func with LogFile
    '''
    log_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), "../../../logs"))
    files= os.listdir(log_dir)
    for file in files: 
        if os.path.isdir(file) or not file.startswith(LOG_PREFIX):
            continue
        with open(log_dir+"/"+file) as input:
            json_obj = json.load(input)
            func(LogFile(file, json_obj))