import json
import os

LOG_PREFIX = "log"

class LogFile:
    def __init__(self, name, content):
        self.file_name = name
        self.json_obj = content

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