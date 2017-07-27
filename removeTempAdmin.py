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
# a user to elevate their privelages to administrator once per day for 30 minutes. After 
# the 30 minutes if a user created a new admin account that account will have admin rights
# also revoked. If the user changed the organization admin account password, that will also
# be reset.
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
#           - orgAdmin encrypted password specified in Jamf Pro parameter #4
#
#
# Written by: Joshua Roskos | Professional Services Engineer | Jamf
#
# Created On: June 20th, 2017
# Updated On: July 26th, 2017
# 
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# IMPORTS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

import os, plistlib, grp, subprocess, time, sys
from datetime import datetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# VARIABLES
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

workingDir = '/usr/local/jamfps/'                   # working directory for script
launchdFile = 'com.jamfps.adminremove.plist'        # launch daemon file location
plistFile = 'MakeMeAdmin.plist'                     # working plist location
statusFile = 'MakeMeAdmin.Status.plist'             # compliancy check plist location
tempAdminLog = 'tempAdmin.log'                      # script log file
orgAdmins = {'orgadmin': sys.argv[4]}               # replace orgAdmin with your organizational admin / password passed via Jamf Pro Parameter #4
salt = '34599b64b8d44a7e'                           # decrypt salt 
passphrase = 'c0495bebbed8ce26115d66a2'             # decrypt passphrase

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# FUNCTIONS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

def DecryptString(inputString, salt, passphrase):
    '''Usage: >>> DecryptString("Encrypted String", "Salt", "Passphrase")'''
    p = subprocess.Popen(['/usr/bin/openssl', 'enc', '-aes256', '-d', '-a', '-A', '-S', salt, '-k', passphrase], stdin = subprocess.PIPE, stdout = subprocess.PIPE)
    return p.communicate(inputString)[0]

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
    newAdm = ''
    if not newAdmins:
        print '   No New Accounts Found!'
        # update compliancy plist
        status = { 'Status':'Compliant'}
        plistlib.writePlist(status, workingDir + statusFile)
    else:
        print '   New Admin Accounts Found!'
        log = open(workingDir + tempAdminLog, "a+")
        log.write("{} - MakeMeAdmin Discovered New Admin Accounts: {}\r\n".format(datetime.now(), list(newAdmins)))
        log.close()
        # update status plist
        status = { 'Status':'Remediated',
                   'newAdmins':'newAdmin Created',
                   'orgAdmin':'orgAdmin OK'}
        plistlib.writePlist(status, workingDir + statusFile)
        newAdm = plistlib.readPlist(workingDir + statusFile).newAdmins
        # loop through new admin accounts and remove admin rights
        print '   Removing Admin Rights for New Admin Accounts...'
        for user in newAdmins:
            subprocess.call(["dseditgroup", "-o", "edit", "-d", user, "-t", "user", "admin"])
            log = open(workingDir + tempAdminLog, "a+")
            log.write("{} - MakeMeAdmin Removed Admin Rights for: {}\r\n".format(datetime.now(), user))
            log.close()
            print '      Removed Admin Rights for ' + user
            time.sleep(1)
    # check if organization admin(s) are valid
    print 'Checking organizational admin passwords...'
    for admin, admpass in orgAdmins.iteritems():
        # decrypt password
        admpassDecrypted = DecryptString(admpass, salt, passphrase)
        time.sleep(1)
        valid = subprocess.call(["dscl", "/Local/Default", "-authonly", admin, admpassDecrypted])
        time.sleep(1)
        if valid == 0:
            log = open(workingDir + tempAdminLog, "a+")
            log.write("{} - orgAdmin Password is Valid \r\n".format(datetime.now()))
            log.close()
            print 'Password for orgAdmin: ' + admin + ' is valid!'
        else:
            log = open(workingDir + tempAdminLog, "a+")
            log.write("{} - orgAdmin Password is Invalid! \r\n".format(datetime.now()))
            log.close()
            result = subprocess.call(["dscl", ".", "passwd", "/Users/" + admin, admpassDecrypted])
            time.sleep(3)
            print 'Password for orgAdmin: ' + admin + ' was invalid!'
            if result == 0:
                log = open(workingDir + tempAdminLog, "a+")
                log.write("{} - orgAdmin Password Successfully Reset! \r\n".format(datetime.now()))
                log.close()
                print 'Password Successfully Reset for ' + admin + "!"
                if not newAdm:
                    # update status plist
                    status = { 'Status':'Remediated',
                               'newAdmins':'No newAdmins',
                               'orgAdmin':'orgAdmin OK'}
                    plistlib.writePlist(status, workingDir + statusFile)
                else:
                    # update status plist
                    status = { 'Status':'Remediated',
                               'newAdmins':'newAdmin Created',
                               'orgAdmin':'orgAdmin OK'}
                    plistlib.writePlist(status, workingDir + statusFile)
            else:
                log = open(workingDir + tempAdminLog, "a+")
                log.write("{} - Error Resetting orgAdmin Password! \r\n".format(datetime.now()))
                log.close()
                print 'Error Resetting Password for ' + admin + "!"
                if not newAdm:
                    # update status plist
                    status = { 'Status':'Violation',
                               'newAdmins':'No newAdmins',
                               'orgAdmin':'orgAdmin ERROR'}
                    plistlib.writePlist(status, workingDir + statusFile)
                else:
                    # update status plist
                    status = { 'Status':'Violation',
                               'newAdmins':'newAdmin Created',
                               'orgAdmin':'orgAdmin ERROR'}
                    plistlib.writePlist(status, workingDir + statusFile)
    os.remove(workingDir + plistFile)

if os.path.exists('/Library/LaunchDaemons/' + launchdFile):
    print 'Removing LaunchDaemon...'
    os.remove('/Library/LaunchDaemons/' + launchdFile)

# Submit Jamf Pro Inventory
subprocess.call(["/usr/local/jamf/bin/jamf", "recon"])
