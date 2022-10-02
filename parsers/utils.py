import json


def write_file(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(data)


def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = f.read()
    return data


def write_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_dict_string(string):
    start_index = None
    end_index = None
    start_count = 0
    end_count = None
    for i in range(len(string)):
        val = string[i]
        if val == '{':
            if start_index is None:
                start_index = i
            start_count += 1
        if val == '}':
            if end_count is None:
                end_count = 0
            end_index = i
            end_count += 1
        if start_count == end_count:
            return string[start_index: end_index + 1]
