#!/Library/ManagedFrameworks/Python/Python3.framework/Versions/Current/bin/python3

import os, plistlib, subprocess

workingDir = '/usr/local/jamfps/'               # working directory for script
statusFile = 'MakeMeAdmin.Status.plist'         # compliancy check plist location

if os.path.exists(workingDir + statusFile):
    with open(workingDir + statusFile, 'rb') as fp:
        d = plistlib.load(fp)
        status = d["Status"]

        if status == 'Compliant':
            print('<result>' + status + '</result>')
        else:
            newAdm = d["newAdmins"]
            orgAdm = d["orgAdmin"]
            print('<result>' + status + ' - ' + newAdm + ' - ' + orgAdm + '</result>')
else:
    print('<result>' + 'Compliant' + '</result>')
