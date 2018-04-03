
supported_commands = ['F', 'B', 'R', 'L',
                      'CF', 'CS', 'N', 'D', 'Q', 'ES', 'EE']

# "FFFFRRCF110" --> "F 4,R 2,CF 110"
def stringToList(command):
    start, end = 0, 1
    current_command = None
    command_list = []
    while start != len(command):
        current_command = command[start:end]
        if current_command in supported_commands:
            if current_command == 'CF':
                command_list.append('CF ' + command[end:end+3])
                start = end + 3
                end = start + 1
            elif current_command == 'CS':
                command_list.append('CS ' + command[end:end+3])
                start = end + 3
                end = start + 1
            elif current_command in supported_commands:
                n = len(current_command)
                count = 0
                while command[start:end] == current_command:
                    count += 1
                    start = end
                    end += n
                command_list.append(current_command + ' ' + str(count))
                end = start + 1
        else:
            end += 1
    return ','.join(command_list)


# "F 4,R 2" --> "FFFFRR"
def listToString(command):
    stringCommand = ''
    command_list = command.split(',')
    for command in command_list:
        sub_list = command.split(' ')
        if sub_list[0] == 'CF' or sub_list[0] == 'CS':
            stringCommand += sub_list[0]
            stringCommand += sub_list[1]
        else:
            for i in range(int(sub_list[1])):
                stringCommand += sub_list[0]
    return stringCommand


if __name__ == "__main__":
    while(1):
        command = input("command: ")
        converted_command = stringToList(command)
        command = listToString(converted_command)
        print(converted_command)
        print(command)
