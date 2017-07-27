# MakeMeAdminPy
###### Updated MakeMeAdmin workflow from Andrina Kelly's JNUC2013 presentation now converted to Python with violation checking and remediation if additional accounts get created during the users time as a temporary admin.
___
This script was designed to be used in a Self Service policy to allow users to become temporary administrators on their system for the time specifed as 'adminTimer'. Once the timer reaches zero, the users admin rights will be revoked and the system will be checked for any admin accounts that may have been created during the 'adminTimer'. If a user created an admin account it will be logged and reported back to Jamf Pro and then the admin rights will be revoked for those newly created accounts. We've also added the ability to enter your orgAdmin account(s) and verify those accounts are still valid and haven't been changed.

Requirements:
* Jamf Pro
* Policy for enabling tempAdmin via Self Service
* Policy to remove tempAdmin via custom trigger
* Scripts: grantTempAdmin.py & removeTempAdmin.py
* EA's: EA-MakeMeAdmin_ComplianceCheck.py

Please reference https://github.com/brysontyrrell/EncryptedStrings for generating the encrypting password, salt, and passphrase strings.


Written By: Joshua Roskos | Professional Services Engineer | Jamf

Created On: June 20th, 2017 | Updated On: July 26th, 2017
___

### Why is this needed?

This workflow has long been used by many organizations, however one issue always remained..."What if the user creates another admin account while they have admin rights?" Well, fear no more, as this script will capture the current admin users before granting temporary admin rights and then after it revokes the rights, it will check again and compare to see if any new accounts were created. If so, the status will be written to a plist and can then be captured via the EA (Extension Attribute) which can then be scoped via a Smart Computer Group.


### Implementation

**Step 1 - Configure the Scripts**

When you open the scripts you will find some user variables that will need to be defined as specified below:
* grantTempAdmin.py - Lines 72-79
* removeTempAdmin.py - Lines 70-77
* EA-MakeMeAdmin_ComplianceCheck.py - Lines 5-6

**Step 2 - Upload the EA**

* Display Name: MakeMeAdmin - Compliance Status
* Data Type: String
* Inventory Display: {Your Choice}
* Input Type: Script
* Script: {Paste Contents of EA-MakeMeAdmin_ComplianceCheck.py}

**Step 3 - Configure the Smart Group**

*Create a Smart Group named "MakeMeAdmin - Violations" and ensure "Send email notification on membership change" is enabled.*

| And/Or | Criteria | Operator | Value |
| :---: | :---: | :---: | :---: |
|   | MakeMeAdmin - Compliance Status | Like | Remediated |
| Or | MakeMeAdmin - Compliance Status | Like | Violation |

**Step 4 - Create your policies**

* Policy: MakeMeAdmin
  * Payload - General
    * Display Name: *MakeMeAdmin*
    * Enabled: *Checked*
    * Category: {Your Choice}
    * Trigger(s): *None*
    * Execution Frequency: *Once every day (recommended)*
  * Payload - Scripts
    * Scripts: *grantTempAdmin.py*
  * Scope
    * *Configure to your requirements*
  * Self Service
    * *Configure to your requirements*
  * User Interaction
    * Complete Message: *You have been granted admin rights for the next 30 minutes.*
* Policy: MakeMeAdmin - Remove Admin Rights
  * Payload - General
    * Display Name: *MakeMeAdmin - Remove Admin Rights*
    * Enabled: *Checked*
    * Category: {Your Choice}
    * Trigger(s): Custom w/ Event *adminremove*
    * Execution Frequency: *Ongoing*
  * Payload - Scripts
    * Scripts: *removeTempAdmin.py*
  * Scope
    * Targets: *All Computers*
  * User Interaction
    * Complete Message: *Time up! Your admin rights have been revoked.*
    
