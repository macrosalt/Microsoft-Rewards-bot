from common import read_logs_to

POINT_BAR = 9100

def get_eligible_accounts(obj):
    '''
    :input: LogFile
    '''
    json_obj = obj.json_obj
    for key, val in json_obj.items():
            if val["Points"] > POINT_BAR:
                print(f'account: {key} -> points:{val["Points"]}')

read_logs_to(get_eligible_accounts)