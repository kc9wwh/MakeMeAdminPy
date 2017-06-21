#!/usr/bin/env python

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
#
# Copyright (c) 2017 Jamf.  All rights reserved.
#
#       Redistribution and use in source and binary forms, with or without
#       modification, are permitted provided that the following conditions are met:
#               * Redistributions of source code must retain the above copyright
#                 notice, this list of conditions and the following disclaimer.
#               * Redistributions in binary form must reproduce the above copyright
#                 notice, this list of conditions and the following disclaimer in the
#                 documentation and/or other materials provided with the distribution.
#               * Neither the name of the Jamf nor the names of its contributors may be
#                 used to endorse or promote products derived from this software without 
#                 specific prior written permission.
#
#       THIS SOFTWARE IS PROVIDED BY JAMF SOFTWARE, LLC "AS IS" AND ANY
#       EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#       WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#       DISCLAIMED. IN NO EVENT SHALL JAMF SOFTWARE, LLC BE LIABLE FOR ANY
#       DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#       (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#       LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#       ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#       (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#       SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# 
# This script was modified from Andrina Kelly's version presented at JNUC2013 for allowing
# a user to elevate their privelages to administrator once per day for 60 minutes.
#
# To accomplish this the following will be performed:
#			- A launch daemon will be put in place in order to remove admin rights
#			- Log will be written to tempAdmin.log
#			- This policy in Jamf will be set to only be allowed once per day
#
# REQUIREMENTS:
#			- Jamf Pro
#			- Policy for enabling tempAdmin via Self Service
#			- Policy to remove tempAdmin via custom trigger
#			- tempAdmin.sh & removeTempAdmin.sh Scripts
#
#
# Written by: Joshua Roskos | Professional Services Engineer | Jamf
#
# Created On: June 20th, 2017
# Updated On: June 21st, 2017
# 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# IMPORTS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

import os, plistlib, pwd, grp, subprocess
from datetime import datetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# VARIABLES
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

userName = os.getlogin()                        # get the logged in user's name
workingDir = '/usr/local/jamfps/'               # working directory for script
launchdFile = 'com.jamfps.adminremove.plist'    # launch daemon file location
plistFile = 'MakeMeAdmin.plist'                 # launch daemon file location
tempAdminLog = 'tempAdmin.log'                  # script log file
adminTimer = 900                                # how long should they have admin rights for (in seconds)
policyCustomTrigger = 'adminremove'             # custom trigger specified for removeTempAdmin.py policy

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# LAUNCH DAEMON
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# place launchd plist to call JSS policy to remove admin rights.
launchDaemon = { 'Label':'com.jamfps.adminremove',
                 'ProgramArguments':['/usr/local/jamf/bin/jamf', 'policy', '-trigger', policyCustomTrigger],
                 'StartInterval':adminTimer,
                 }
plistlib.writePlist(launchDaemon, '/Library/LaunchDaemons/' + launchdFile)

# set the permission on the file just made.
userID = pwd.getpwnam("root").pw_uid
groupID = grp.getgrnam("wheel").gr_gid
os.chown('/Library/LaunchDaemons/' + launchdFile, userID, groupID)
os.chmod('/Library/LaunchDaemons/' + launchdFile, 0644)

# load the removal plist timer. 
subprocess.call(["launchctl", "load", "-w", '/Library/LaunchDaemons/' + launchdFile])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# APPLICATION
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# build log files
if not os.path.exists("/usr/local/jamfps/"):
    os.makedirs("/usr/local/jamfps/")

log = open(workingDir + tempAdminLog, "a+")
log.write("{} - MakeMeAdmin Granted Admin Rights for {}\r\n".format(datetime.now(), userName))
log.close()

# record user that will need to have admin rights removed
# record current existing admins
currentAdmins = grp.getgrnam('admin').gr_mem
plist = { 'User2Remove':userName,
          'CurrentAdminUsers':currentAdmins}
plistlib.writePlist(plist, workingDir + plistFile)

# give current logged user admin rights
subprocess.call(["dseditgroup", "-o", "edit", "-a", userName, "-t", "user", "admin"])
