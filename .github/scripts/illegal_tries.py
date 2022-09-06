from common import read_logs_to

def get_illegal_tries(obj):
    '''
    :input: LogFile
    '''
    filename = obj.file_name
    json_obj = obj.json_obj
    for key, val in json_obj.items():
            check_situation = val["Last check"]
            if len(check_situation) != 10 or check_situation[0] != "2":
                print(f'account: {key} -> check:{check_situation} in {filename}')

read_logs_to(get_illegal_tries)