#!/usr/bin/env python3
import getpass  ## import getpass is required if prompting for XIQ crednetials
import json
import requests
from colored import fg
import os
import smtplib
import pandas as pd
from pprint import pprint as pp
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders

########################################################################################################################
## written by:       Mike Rieben
## e-mail:           mrieben@extremenetworks.com
## date:             July, 2024
## version:          1.0
## tested versions:  Python 3.11.4, XIQ 24r4 (June 2024)
########################################################################################################################
## This script ...  See README.md file for full description 
########################################################################################################################
## ACTION ITEMS / PREREQUISITES
## Please read the README.md file in the package to ensure you've completed the required and optional settings below
## Also as a reminder, do not forget to install required modules:  pip install -r requirements.txt
########################################################################################################################
## - ## two pound chars represents a note about that code block or a title
## - # one pound char represents a note regarding the line and may provide info about what it is or used for
########################################################################################################################


#region - Begin user settings section
## AUTHENTICATION Options:  Uncomment the section you wish to use whie other sections remain commented out
## 1) Static Username and password, must have empty token variable (Uncomment 3 total lines below). Enter values for username and password after uncommenting.
# XIQ_Token = ""
# XIQ_username = "name@contoso.com"  # Enter your ExtremeCloudIQ Username "xxxx"
# XIQ_password = "<password>"  # Enter your ExtremeCLoudIQ password "xxxx"

## 2) Prompt user to enter credentials, must have empty token variable (Uncomment 4 total lines below), simply uncomment - no entries required
# XIQ_Token = ""
# print ("Enter your XIQ login credentials ")
# XIQ_username = input("Email: ")
# XIQ_password = getpass.getpass("Password: ")

## 3) TOKEN generation from api.extremecloudiq.com (Swagger). Must have empty username and password variables (Uncomment 3 total lines below).  Enter XIQ Toekn within "" only.
XIQ_Token = "XXXXXXX"
XIQ_username = ""
XIQ_password = ""
##Authentication Options END

##SMTP Settings - Optional Feature - Check your SPAM/Junk folder -------------------------------------------------------------------------------
emailFeature = 'DISABLE' # Default: 'DISABLE' to disable email feature.  'ENABLE' to enable feature.
username = 'XXXX'
password = 'XXXX'
sender_email = 'mike@contoso.com'
##example of multiple email addresses in a list: tolist = ['mike@contoso.com','alerts@contoso.com']
##example of single email address:  tolist = ['mike@contoso.com']
tolist = ['XXXX@XXXX.com']
email_subject = 'Telnet Checker Report'
##smtp_server = '' #If you are not using email feature then leave this variable empty '' and the script will skip sending emails
smtp_server = 'smtp.sendgrid.net'
smtp_port = 587 #<-- change port as required by your SMTP server
#end SMTP Settings------------------------------------------------------------------------------------------------------------------------------

##User defined variables as outlined in README documentation
cliCommand = 'show run | inc telnet'  #single command supported
printToScreenResults = 'YES'  #'YES' to print (default), 'NO' or '' to skip results to screen (might be too much depending on your total device count)
locateOfflineAPs = 'YES'  #'YES' (default) to add all offline APs to the CSV and/or screen, 'NO' or '' to skip gathering offline devices which are informational only
#endregion ##end user settings section


#region #************************* No user edits below this line required ************************************************************************************
##Global Variables-------------------------------------------------------------------------------------------------------------------------------------
URL = "https://api.extremecloudiq.com"  ##XIQ's API portal
headers = {"Accept": "application/json", "Content-Type": "application/json"}
PATH = os.path.dirname(os.path.abspath(__file__))  #Stores the current Python script directory to write the CSV file to
filename = 'device-list-telnet.csv' #<- file name that will be created in the current directory of the Python file
colorWhite = fg(255) ##DEFAULT Color: color pallete here: https://dslackw.gitlab.io/colored/tables/colors/
colorRed = fg(1) ##RED
colorGreen = fg(2) ##GREEN
colorPurple = fg(54) ##PURPLE
colorCyan = fg(6) ##CYAN
colorOrange = fg(94) ##ORANGE
colorGrey = fg(8)  ##GREY
telnetDeteced = False  #Global variable to set flag if Telnet was detected.
#endregion #end Global Variables---------------------------------------------------------------------------------------------------------------------------------

##Use provided credentials to acquire the access token if none was provided-------------------------
def GetaccessToken(XIQ_username, XIQ_password):
    url = URL + "/login"
    payload = json.dumps({"username": XIQ_username, "password": XIQ_password})
    response = requests.post(url, headers=headers, data=payload)
    if response is None:
        log_msg = "ERROR: Not able to login into ExtremeCloudIQ - no response!"
        raise TypeError(log_msg)
    if response.status_code != 200:
        log_msg = f"Error getting access token - HTTP Status Code: {str(response.status_code)}"
        try:
            data = response.json()
            if "error_message" in data:
                log_msg += f"\n\t{data['error_message']}"
        except:
            log_msg += ""
        raise TypeError(log_msg)
    data = response.json()
    if "access_token" in data:
        headers["Authorization"] = "Bearer " + data["access_token"]
        return 0
    else:
        log_msg = "Unknown Error: Unable to gain access token"
        raise TypeError(log_msg)
##end Use provided credentials to acquire the access token if none was provided-------------------------

##Get Device Hostnames if Real / Connected----------------------------------------------------------
def GetDeviceOnlineList():
    page = 1
    pageCount = 1
    pageSize = 100
    foundDevices = []
    onlineDeviceIDs = []
    while page <= pageCount:
        url = URL + "/devices?page=" + str(page) + "&limit=" + str(pageSize) + "&connected=true&adminStates=MANAGED&views=FULL&deviceTypes=REAL"
        try:
            rawList = requests.get(url, headers=headers, verify = True)
        except ValueError as e:
            print('script is exiting...')
            raise SystemExit
        except Exception as e:
            print('script is exiting...')
            raise SystemExit
        if rawList.status_code != 200:
            print('Error exiting script...')
            print(rawList.text)
            raise SystemExit
        jsonDump = rawList.json()
        for device in jsonDump['data']:
            if device['device_function'] == 'AP': #test to make sure all devices gathered are APs
                onlineDeviceIDs.append(device['id'])
                newData = {}
                newData['DEVICE ID'] = device['id']
                newData['HOSTNAME'] = device['hostname']
                newData['STATUS'] = 'Online'
                if device['locations']:
                    newData['BUILDING'] = device['locations'][-2]['name']
                    newData['FLOOR'] = device['locations'][-1]['name']
                else:
                    newData['BUILDING'] = 'No Location'
                    newData['FLOOR'] = 'No Floor'
                if device['ip_address']: 
                    newData['IP'] = device['ip_address']
                else:
                    newData['IP'] = 'Unknown'
                if device['network_policy_name']: 
                    newData['POLICY'] = device['network_policy_name']
                else:
                    newData['POLICY'] = 'Unknown'
                if device['product_type']: 
                    newData['MODEL'] = device['product_type']
                else:
                    newData['MODEL'] = 'Unknown'
                newData['TELNET ENABLED'] = 'Unknown'
                foundDevices.append(newData)
        pageCount = jsonDump['total_pages']
        print(f"\n{colorGreen}Completed page {page} of {jsonDump['total_pages']} collecting Online devices")
        page = jsonDump['page'] + 1
    if onlineDeviceIDs == []:
        print(f"\n{colorRed}No online devices found")
    return foundDevices,onlineDeviceIDs
##end Get Device Hostnames if Real / Connected----------------------------------------------------------

##Get Device Hostnames if Real / Disconnected------------------------------------------------------------------------------------
def GetDeviceOfflineList():
    page = 1
    pageCount = 1
    pageSize = 100
    foundDevices = []
    while page <= pageCount:
        url = URL + "/devices?page=" + str(page) + "&limit=" + str(pageSize) + "&connected=false&adminStates=MANAGED&views=FULL&deviceTypes=REAL"
        try:
            rawList = requests.get(url, headers=headers, verify = True)
        except ValueError as e:
            print('script is exiting...')
            raise SystemExit
        except Exception as e:
            print('script is exiting...')
            raise SystemExit 
        if rawList.status_code != 200:
            print('Error exiting script...')
            print(rawList.text)
            raise SystemExit
        jsonDump = rawList.json()
        for device in jsonDump['data']:
            newData = {}
            newData['DEVICE ID'] = device['id']
            newData['HOSTNAME'] = device['hostname']
            newData['STATUS'] = 'Offline'
            if device['locations']:
                newData['BUILDING'] = device['locations'][-2]['name']
                newData['FLOOR'] = device['locations'][-1]['name']
            else:
                newData['BUILDING'] = 'No Location'
                newData['FLOOR'] = 'No Floor'
            if device['ip_address']: 
                newData['IP'] = device['ip_address']
            else:
                newData['IP'] = 'Unknown'
            if device['network_policy_name']: 
                newData['POLICY'] = device['network_policy_name']
            else:
                newData['POLICY'] = 'Unknown'
            if device['product_type']: 
                newData['MODEL'] = device['product_type']
            else:
                newData['MODEL'] = 'Unknown'
            newData['TELNET ENABLED'] = 'Unknown'
            foundDevices.append(newData)
        pageCount = jsonDump['total_pages']
        print(f"\n{colorGrey}Completed page {page} of {jsonDump['total_pages']} collecting Offline devices (option is enabled)")
        page = jsonDump['page'] + 1
    return foundDevices
##end Get Device Hostnames if Real / Disconnected--------------------------------------------------------------------------------

##Send email
def SendMail(fromaddr, toaddr, email_body, email_subject, smtpsrv, smtpport, reportName):
        # Build the email
        toHeader = ", ".join(toaddr)
        msg = MIMEMultipart()
        msg['Subject'] = email_subject
        msg['From'] = fromaddr
        msg['To'] = toHeader
        msg.attach(MIMEText(email_body))
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f"{PATH}/{filename}", "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{reportName}"')
        msg.attach(part)
        try:
            server = smtplib.SMTP(smtpsrv, smtpport)
            server.starttls()
            server.login(username,password)
            server.send_message(msg)
            server.quit()
            #debug_print "email sent: %s" % fromaddr
        except Exception as e:
                logmsg = "Something went wrong when sending the email to {}".format(fromaddr)
                raise TypeError(f"{logmsg}\n   {e}")
##end SMTP Relay for email alerts section ---------------------------------------------------------

##Execute action for online APs only
def SendCLI(onlineDeviceIDsLocal,cliCommandLocal):
    global telnetDeteced
    telnetResultsIdValue = []
    print(f'{colorPurple}\nAttempting to send CLI command : #' + cliCommand)
    url = URL + "/devices/:cli?async=false"
    payload = json.dumps({
    "devices": {
        "ids": onlineDeviceIDsLocal
    },
    "clis": [
        cliCommandLocal
    ]
    })
    response = requests.request("POST", url, headers=headers, data=payload)    
    if response is None:
        log_msg = "ERROR: POST call to send CLI command - no response!"
        print(f'{colorRed}{log_msg}')
    if response.status_code != 200:
        log_msg = f"Error - HTTP Status Code: {str(response.status_code)}"
        try:
            data = response.json()
            if "error_message" in data:
                log_msg += f"\n\t{data['error_message']}"
        except:
            log_msg += ""
        print(f'{colorRed}{log_msg}')
    else:
        print(f'{colorPurple}CLI executed!')
        jsonDump = response.json()
        results = (jsonDump['device_cli_outputs'])
        newData = {}
        for device in results:
            if results[device][0]['output'] == '':
                telnetResults = 'Disabled'
            else:
                telnetResults = 'Enabled - hive <name> manage telnet'
                telnetDeteced = True
            newData = {
                'DEVICE ID': device,
                'TELNET ENABLED': telnetResults
            }
            telnetResultsIdValue.append(newData)
    for item in telnetResultsIdValue:
        item['DEVICE ID'] = int(item['DEVICE ID']) #convert from the ID value from string to integer to match Online Devices
    return telnetResultsIdValue


##This is the start of the program
def main():
    ##Test if a token is provided.  If not, use credentials.
    if not XIQ_Token:
        try:
            login = GetaccessToken(XIQ_username, XIQ_password)
        except TypeError as e:
            print(e)
            raise SystemExit
        except:
            log_msg = "Unknown Error: Failed to generate token"
            print(log_msg)
            raise SystemExit
    else:
        headers["Authorization"] = "Bearer " + XIQ_Token
    deviceOnlineList,onlineDeviceIDs = GetDeviceOnlineList() # go get online devices via a function
    if onlineDeviceIDs != []:
        telnetResultsList = SendCLI(onlineDeviceIDs,cliCommand) # send online devices to a function including the user definable variable for the CLI command
    df1 = pd.DataFrame(deviceOnlineList) # convert online device list to a dataframe
    df2 = pd.DataFrame(telnetResultsList) # convert online device list with SendCLI results to a dataframe
    ##test the user definable variable that allows the user to add or skip gathering offline devices
    if locateOfflineAPs == 'YES':
        deviceOfflineList = GetDeviceOfflineList() # go get offline devices via a function
        df3 = pd.DataFrame(deviceOfflineList) # convert offline device list to a dataframe
    ##Create a mapping from DEVICE ID to TELNET value in df2
    telnet_map = df2.set_index('DEVICE ID')['TELNET ENABLED']
    ##Use map function to update the TELNET column in df1 based on DEVICE ID
    df1['TELNET ENABLED'] = df1['DEVICE ID'].map(telnet_map)
    ##Sort rows by TELNET ENABLED column so any APs that have Telnet enabled rise to the top
    df1.sort_values(by=['TELNET ENABLED'], inplace=True, ascending=False)
    ##Test the user definable variable that allows the user to add or skip gathering offline devices
    if locateOfflineAPs == 'YES':
        df4 = pd.concat([df1, df3], ignore_index=True) # Combine the Online dataframe (df1) with the Offline dataframe (df3)
        df5 = df4.drop(columns=['DEVICE ID']) # Delete the DEVICE ID column from the final DataFrame
    else:
        df5 = df1.drop(columns=['DEVICE ID']) # Delete the DEVICE ID column from the final DataFrame
    ##Display the updated DataFrame to screen (optional via the user variables)
    if printToScreenResults == 'YES':
        if telnetDeteced:
            print(f"{colorRed}\n***Telnet has been DETECTED on one or more located online APs*** \n")
        else:
            print(f"{colorGreen}\nTelnet has been DISABLED on all located online APs \n")
        pp(df5)
    print(f'\n{colorPurple}Populating CSV file with found devices: "' + filename + '" <-- Check script directory for file.\n')
    df5.to_csv(filename, index=False) # Create CSV file int he same directory as the script based on the final DataFrame
    ##Email section
    email_msg = "See attachment for device report."
    if smtp_server != '' and emailFeature == 'ENABLE':
        if len(deviceOnlineList) != 0:
            try:
                SendMail(sender_email, tolist, email_msg, email_subject, smtp_server, smtp_port, filename)
            except TypeError as e:
                print(e)
            print(f'{colorWhite}Email includes CSV and sent to: ' + ','.join(str(e) for e in (tolist)) + '\n')
        else:
            print(f'{colorWhite}No email was sent due to all online devices having current configurations. Check CSV for offline devices. \n')
    elif emailFeature != 'ENABLE':
        print(f'{colorWhite}***Email feature is disabled, skipping email. \n')
    elif smtp_server == '':
        print(f'{colorWhite}No SMTP server defined, skipping email. \n')
    else:
        print(f'{colorRed}Unknown issue... Verify all User Settings Section variables: smtp_server, emailFeature, etc.')
        
##Python will see this and run whatever function is provided: xxxxxx(), should be the last items in this file
if __name__ == '__main__':
    main() ##Go to main function

##***end script***


