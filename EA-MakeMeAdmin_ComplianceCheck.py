#!/usr/bin/env python

import os, plistlib, subprocess

workingDir = '/usr/local/jamfps/'               # working directory for script
statusFile = 'MakeMeAdmin.Status.plist'         # compliancy check plist location

if os.path.exists(workingDir + statusFile):
    status = plistlib.readPlist(workingDir + statusFile).Status
    if status == 'Compliant':
        print '<result>' + status + '</result>'
    else:
        newAdm = plistlib.readPlist(workingDir + statusFile).newAdmins
        orgAdm = plistlib.readPlist(workingDir + statusFile).orgAdmin
        print '<result>' + status + ' - ' + newAdm + ' - ' + orgAdm + '</result>'
else:
    print '<result>' + 'Compliant' + '</result>'