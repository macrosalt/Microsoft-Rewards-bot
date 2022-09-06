import json
import os

point_bar = 9100
log_prefix = "log"

log_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), "../../../logs"))
files= os.listdir(log_dir)
for file in files: 
    if os.path.isdir(file) or not file.startswith(log_prefix):
        continue
    with open(log_dir+"/"+file) as input:
        dict = json.load(input)
        for key, val in dict.items():
            if val["Points"] > point_bar:
                print(f'account: {key} -> points:{val["Points"]}')
    