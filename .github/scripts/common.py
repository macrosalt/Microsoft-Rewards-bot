import json
import os

LOG_PREFIX = "log_"

LOG_TO_INSTANCE = {
    "1": "o-ubuntu",
    "2": "o-opc",
    "3": "instance-1",
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

def get_account_verified(account):
    return account in ACCOUNT_REGION

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