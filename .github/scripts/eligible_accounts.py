from common import read_logs_to

POINT_BAR = 13000

def get_eligible_accounts(obj):
    '''
    :input: LogFile
    '''
    json_obj = obj.json_obj
    for key, val in json_obj.items():
            if isinstance(val["Points"], int) and val["Points"] > POINT_BAR:
                print(f'account: {key} -> points:{val["Points"]}')

read_logs_to(get_eligible_accounts)