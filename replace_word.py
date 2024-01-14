import csv
import re

def load_conversion_dict(filename):
    conversion_dict = {}
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, quotechar='"')
        for row in reader:
            if len(row) == 2:
                conversion_dict[row[0]] = row[1]
    return conversion_dict

def replace_text(input_text, conversion_dict):
    for key, value in conversion_dict.items():
        input_text = re.sub(key, value, input_text)
    return input_text



        
