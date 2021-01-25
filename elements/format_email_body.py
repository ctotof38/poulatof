import re


open_close_actions = re.compile(r'(^[^,]+).*advanced_elements.*(INFO).*(close|open) door$')
warning_messages = re.compile(r'(^[^,]+).*advanced_elements.*(WARNING|ERROR) - (.*)')


def format_data(log_content, csv=False):
    found_data = {}
    max_size_level = 0
    max_size_message = 0

    for line in log_content:
        found = open_close_actions.findall(line)
        if found:
            date = found[0][0]
            level = found[0][1]
            message = found[0][2]
            if len(level) > max_size_level:
                max_size_level = len(level)
            if len(message) > max_size_message:
                max_size_message = len(message)
            found_data[date] = [level, message]
        found = warning_messages.findall(line)
        if found:
            date = found[0][0]
            level = found[0][1]
            message = found[0][2]
            if len(level) > max_size_level:
                max_size_level = len(level)
            if len(message) > max_size_message:
                max_size_message = len(message)
            found_data[date] = [level, message]

    if csv:
        formatted_data = __csv_format__(found_data)
    else:
        formatted_data = __str_format__(found_data, max_size_level, max_size_message)

    return '\n'.join(formatted_data)


def __get_space(word, max_size):
    if len(word) == max_size:
        return ""
    else:
        size = max_size - len(word)
        return " " * size


def __str_format__(found_data, max_level=4, max_message=5):
    formatted_data = []

    if len(found_data) > 0:
        for date in sorted(found_data.keys()):
            level = found_data[date][0]
            message = found_data[date][1]
            formatted_message = '| ' + date + ' | ' + level
            formatted_message += __get_space(level, max_level) + ' | ' + message
            formatted_message += __get_space(message, max_message) + ' |'
            formatted_data.append(formatted_message)

    return formatted_data


def __csv_format__(found_data):
    formatted_data = []

    if len(found_data) > 0:
        for date in sorted(found_data.keys()):
            level = found_data[date][0]
            message = found_data[date][1]
            formatted_data.append(date + ';' + level + ';' + message)

    return formatted_data


# just for test
if __name__ == "__main__":
    with open('/tmp/automatic_door.log', 'r') as file:
        data = file.readlines()
        result = format_data(data, False)
        print(result)
