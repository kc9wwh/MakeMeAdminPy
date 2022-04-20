#!/Library/ManagedFrameworks/Python/Python3.framework/Versions/Current/bin/python3

from datetime import date, timedelta, datetime

workingDir = '/usr/local/jamfps/'                   # working directory for script
tempAdminLog = 'tempAdmin.log'                      # script log file

fmt = '%Y-%m-%d %H:%M:%S.%f'

stop = datetime.now()
start = stop - timedelta(days=1)

elevationCount=0

try:
    with open(workingDir + tempAdminLog, 'r') as file:
        for line in file:
            line = line.strip()

            try:
                ts = datetime.strptime(' '.join(line.split()[:2]), fmt)

                if start <= ts <= stop:
                    if "Granted" in line:
                        elevationCount=elevationCount+1

            except:
                pass
except:
    pass

print(('<result>' + str(elevationCount) + '</result>'))
