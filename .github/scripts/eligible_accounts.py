from common import read_logs_to, get_log_location, get_account_region, get_account_priority, get_account_machine

REGION_POINT_BAR = {
    "sg": 9100,
    "us": 13000,
}

priority_print = {}

def append_ele_to_dict_of_list(map, key, value):
    to_set_list = []
    if key in map:
        to_set_list = map[key]
    to_set_list.append(value)
    map[key] = to_set_list


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
                priority = get_account_priority(key)
                # Region logic isn't used for now
                if priority == 0:
                    append_ele_to_dict_of_list(priority_print, priority, 
                    f'*need verify* account: {key} -> points:{val["Points"]} from {location}|{region}')
                    continue
                machine = get_account_machine(key)
                append_ele_to_dict_of_list(priority_print, priority,
                f'account: {key} -> points:{val["Points"]} from {location}| {machine}| {region}')

def print_logs_in_priority():
    for priority in sorted(priority_print.keys()):
        logs = priority_print[priority]
        for log in logs:
            print(log)

read_logs_to(get_eligible_accounts)
print_logs_in_priority()
