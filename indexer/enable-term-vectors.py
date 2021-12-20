# 

import re

infile = open('src/main/resources/elastic_mappings.json', 'r')
outfile = open('src/main/resources/out.txt', 'w')

for line in infile:
    if "\"type\" : \"text\"" in line.strip():
        thing = line.rstrip() + '\n \t\t\t\t"term_vector": "with_positions_offsets_payloads",\n'
        outfile.write(thing)
    else:
        outfile.write(line)

print('Output written to src/main/resources/out.txt.')