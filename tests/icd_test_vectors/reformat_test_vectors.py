import csv
import sys
import re
from datetime import datetime

csv.field_size_limit(sys.maxsize)
file_path = sys.argv[1]

GPS_START = datetime(1980,1,6)
DATE_PATTERN = r'([0-9]{2})_([A-Z]{3})_([0-9]{4})_GST_([0-9]{2})_([0-9]{2})_([0-9]{2}).csv'
month2num = {'JAN':1,'FEB':2,'MAR':3,'APR':4,'MAY':5,'JUN':6,'JUL':7,'AUG':8,'SEP':9,'OCT':10,'NOV':11,'DEC':12}

# Get WN and TOW from date in filename
try:
    regex_result = re.search(DATE_PATTERN, file_path)
    day, month, year, hour, minute, second = regex_result.groups()
except:
    print(f"No patterns: {file_path}")
    exit(1)

month = month2num[month]

epoch = datetime(int(year),int(month),int(day),int(hour),int(minute),int(second))
delta = epoch - GPS_START

wn = delta.days//7
tow = delta.seconds

# Define constants
bits_per_page = 240
hex_per_page = bits_per_page//4
max_pages = 0

nav_message_dict = {}

with open(file_path, 'r') as csv_file:
    csv_reader = csv.DictReader(csv_file)

    for line in csv_reader:
        nav_bits_hex = line['NavBitsHEX']
        number_of_pages = int(line['NumNavBits'])//240
        nav_message_dict[int(line['SVID'])] = [nav_bits_hex[i*hex_per_page:i*hex_per_page + hex_per_page] for i in range(number_of_pages)]

        if number_of_pages > max_pages:
            max_pages = number_of_pages


list_of_pages = []

for page in range(max_pages):
    for svid, nav_data in nav_message_dict.items():
        list_of_pages.append([tow,wn-1024,svid,nav_data[page]])
    tow += 2

with open(file_path[:file_path.rfind('.')]+'_fixed.csv', 'w') as out_file:
    csv_writer = csv.writer(out_file)
    csv_writer.writerows(list_of_pages)

