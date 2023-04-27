import random
import itertools

import json

def json_load_from_filename(filename):
    print('Reading json from file: ' + filename)
    file = open(filename, encoding = 'utf-8')
    results = json.load(file)
    return(results)
    
def json_dump_to_filename(data, filename):
    print('Writing json to file: ' + filename)
    file = open(filename, 'w', encoding = 'utf-8')
    results = json.dump(data, file, indent = 4, sort_keys = True)
    file.close()
    return

def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while (batch := list(itertools.islice(it, n))):
        yield batch


in_filename = "minecraft_synthetic_chat_with_numbers.txt"
out_filename = "minecraft_synthetic_chat_with_numbers_snippets.json"

in_file = open(in_filename, encoding = "utf-8")
in_data = list(in_file)
in_file.close()

comment_0 = in_data.pop(0)
print(comment_0)
# Chunk

out_data = list(batched(in_data, 50))
out_data_2 = []
for i, x in enumerate(out_data):
    y = x
    y = "".join(y)
    y = {"review_text" : y,
        "profile_name" : "batch_" + str(i),
        "location" : "Minecraft"}
    out_data_2.append(y)

json_dump_to_filename(out_data_2, out_filename)
