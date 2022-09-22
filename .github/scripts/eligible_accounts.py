from common import read_logs_to

REGION_POINT_BAR = {
    "sg": 9100,
    "us": 13000,
}

ACCOUNT_REGION = {
    "saltleemsr052@outlook.com": "sg",
    "drbvwltl@outlook.com": "sg",
    "npmiygkue@outlook.com": "sg",
}

def get_account_region(account):
    if account in ACCOUNT_REGION:
        return ACCOUNT_REGION[account]
    return "us"

def get_eligible_accounts(obj):
    '''
    :input: LogFile
    '''
    json_obj = obj.json_obj
    for key, val in json_obj.items():
            region = get_account_region(key)
            if isinstance(val["Points"], int) and val["Points"] > REGION_POINT_BAR[region]:
                print(f'account: {key} -> points:{val["Points"]} in {region}')

read_logs_to(get_eligible_accounts)