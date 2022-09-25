from common import read_logs_to, get_log_location,get_account_region

REGION_POINT_BAR = {
    "sg": 9100,
    "us": 13000,
}





def get_eligible_accounts(obj):
    '''
    :input: LogFile
    '''
    filename = obj.file_name
    json_obj = obj.json_obj
    location = get_log_location(filename)
    for key, val in json_obj.items():
            region = get_account_region(key)
            if isinstance(val["Points"], int) and val["Points"] > REGION_POINT_BAR[region]:
                print(f'account: {key} -> points:{val["Points"]} from {location} in {region}')

read_logs_to(get_eligible_accounts)