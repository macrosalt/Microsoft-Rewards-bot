from common import read_logs_to, get_log_location, get_account_region, get_account_verified

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
    priority_print = [[],[]]
    for key, val in json_obj.items():
            region = get_account_region(key)
            if isinstance(val["Points"], int) and val["Points"] > REGION_POINT_BAR[region]:
                if get_account_verified(key):
                    priority_print[0].append(f'*verified* account: {key} -> points:{val["Points"]} from {location} in {region}')
                    continue
                priority_print[1].append(f'account: {key} -> points:{val["Points"]} from {location} in {region}')

    for logs in priority_print:
        for log in logs:
            print(log)
read_logs_to(get_eligible_accounts)