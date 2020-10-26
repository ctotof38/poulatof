import re


fields_to_look_for = re.compile(r'(^[^,]+).*advanced_elements.*INFO.*(close|open)')


def format_data(log_content, csv=False):
    found_data = []

    for line in log_content:
        found = fields_to_look_for.findall(line)
        if found:
            found_data.append(found)

    if csv:
        formatted_data = __csv_format__(found_data)
    else:
        formatted_data = __str_format__(found_data)

    return '\n'.join(formatted_data)


def __str_format__(found_data):
    formatted_data = []

    if len(found_data) > 0:
        current_date, action = found_data[0][0]
        # calculate length of field + space before and after
        date_length = len(current_date) + 2
        action_length = len('close') + 2
        begin_end = '+'.ljust(date_length + 1, '-') + '+'.ljust(action_length + 1, '-') + '+'
        formatted_data.append(begin_end)
        for found_fields in found_data:
            current_date, action = found_fields[0]
            # close has greater length than open
            if len(action) == 5:
                end = ' |'
            else:
                end = '  |'
            formatted_data.append("| " + current_date + " | " + action + end)
        formatted_data.append(begin_end)

    return formatted_data


def __csv_format__(found_data):
    formatted_data = []

    if len(found_data) > 0:
        for found_fields in found_data:
            current_date, action = found_fields[0]
            formatted_data.append(current_date + ';' + action)
    return formatted_data


# just for test
if __name__ == "__main__":
    with open('/tmp/automatic_door.log', 'r') as file:
        data = file.readlines()
        result = format_data(data, False)
        print(result)
