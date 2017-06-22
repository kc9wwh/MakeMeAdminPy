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
#           - A launch daemon will be put in place in order to remove admin rights
#           - Log will be written to tempAdmin.log
#           - This policy in Jamf will be set to only be allowed once per day
#
# REQUIREMENTS:
#           - Jamf Pro
#           - Policy for enabling tempAdmin via Self Service
#           - Policy to remove tempAdmin via custom trigger (adminremove)
#           - tempAdmin.sh & removeTempAdmin.sh Scripts
#
#
# Written by: Joshua Roskos | Professional Services Engineer | Jamf
#
# Created On: June 20th, 2017
# Updated On: June 22nd, 2017
# 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# IMPORTS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

import os, plistlib, grp, subprocess, time
from datetime import datetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# VARIABLES
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

workingDir = '/usr/local/jamfps/'               # working directory for script
launchdFile = 'com.jamfps.adminremove.plist'    # launch daemon file location
plistFile = 'MakeMeAdmin.plist'                 # working plist location
statusFile = 'MakeMeAdmin.Status.plist'         # compliancy check plist location
tempAdminLog = 'tempAdmin.log'                  # script log file

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# APPLICATION
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

if os.path.exists(workingDir + plistFile):
    # remove user admin rights
    user2Remove = plistlib.readPlist(workingDir + plistFile).User2Remove
    subprocess.call(["dseditgroup", "-o", "edit", "-d", user2Remove, "-t", "user", "admin"])
    # add log entry
    log = open(workingDir + tempAdminLog, "a+")
    log.write("{} - MakeMeAdmin Removed Admin Rights for {}\r\n".format(datetime.now(), user2Remove))
    log.close()
    print 'Revoked Admin Rights for ' + user2Remove
    # compre prior to current admin lists
    print 'Checking for newly created admin accounts...'
    priorAdmins = plistlib.readPlist(workingDir + plistFile).CurrentAdminUsers
    currentAdmins = grp.getgrnam('admin').gr_mem
    newAdmins = set(currentAdmins).difference(set(priorAdmins))
    if not newAdmins:
        print '   No New Accounts Found!'
        # update compliancy plist
        status = { 'Status':'Compliant'}
        plistlib.writePlist(status, workingDir + statusFile)
    else:
        log = open(workingDir + tempAdminLog, "a+")
        log.write("{} - MakeMeAdmin Discovered New Admin Accounts: {}\r\n".format(datetime.now(), list(newAdmins)))
        log.close()
        # update status plist
        status = { 'Status':'Non-Compliant',
                   'newAdmins':list(newAdmins)}
        plistlib.writePlist(status, workingDir + statusFile)
        print 'New Admin Accounts Found - ' + newAdmins
    os.remove(workingDir + plistFile)

if os.path.exists('/Library/LaunchDaemons/' + launchdFile):
    print 'Unloading LaunchDaemon...'
    subprocess.call(["launchctl", "unload", "-w", '/Library/LaunchDaemons/' + launchdFile])
    time.sleep(3)
    print 'Removing LaunchDaemon...'
    os.remove('/Library/LaunchDaemons/' + launchdFile)

# Submit Jamf Pro Inventory
subprocess.call(["jamf", "recon"])
