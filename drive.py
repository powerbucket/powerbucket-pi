import subprocess
import datetime

TIME=str(datetime.datetime.now()) #"2020-09-18 20:32:35"
print(TIME)
FIRST_NUM="0"
SECOND_NUM="0"
THIRD_NUM="0"
FOURTH_NUM="0"
FIFTH_NUM=str(0)

subprocess.check_call(['./login.sh',
                       TIME,
                       FIRST_NUM,
                       SECOND_NUM,
                       THIRD_NUM,
                       FOURTH_NUM,
                       FIFTH_NUM])
