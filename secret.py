from datetime import datetime

str_0 = '19.01.2025 01:53:00.000001'
str_1 = datetime.strptime(str_0, '%d.%m.%Y %H:%M:%S.%f')

string = str(str_1)
new = datetime.strftime(str_1, '%Y-%m-%d %H:%M:%S')


print(string)
print(new)

str = '19.01.2025'
str2 = '19.11.2025'

print(datetime.strptime(str, '%d.%m.%Y'))

