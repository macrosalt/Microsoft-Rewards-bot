from common import read_logs_to, get_log_location
from datetime import date, timedelta

def get_illegal_tries(obj):
    '''
    :input: LogFile
    '''
    filename = obj.file_name
    json_obj = obj.json_obj
    today = str((date.today()))
    yesterday = str((date.today() - timedelta(days = 1)))
    location = get_log_location(filename)
    for key, val in json_obj.items():
            check_situation = val["Last check"]
            if len(check_situation) != 10 or check_situation[0] != "2":       
                print(f'abnormal operation: account: {key} -> check:{check_situation} of {filename} in {location}')
                continue
            if check_situation != yesterday and check_situation != today:
                print(f'outdated log: account: {key} -> last time updated:{check_situation} of {filename} in {location}')
                continue

read_logs_to(get_illegal_tries)