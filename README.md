# XIQ Telnet Checker
## Purpose
ExtremeCloud IQ (XIQ) UI currently does not show if an Access Point has Telnet enabled on a device.  You may have a security audit and you want to ensure Telnet is not enabled either by XIQ or manual CLI override.  This script uses an API call to send a CLI command: `show run | inc telnet`
- The output of `""` means telnet is disabled
- The output of `"hive VHM-XXXXXX manage telnet"` means telnet is enabled

Great example of how to use API: POST - /devices/:cli then export to a CSV using Pandas module.

### Overview 
This locates only access points and uses the SendCLI API to send a *show run* command to each online AP.  The output is a CSV file containing the results of every AP, optionally noting which are offline.  The CSV file is stored in the current directory where the Python script resides and can optionally be emailed if SMTP is setup.

## Actions & Requirements
You must update the user controllable variables within `XIQ-TelnetChecker_v#.py` which are outlined below.  Install the required modules and generate an API Token to run script without user prompts.  If you need assistance setting up your computing environment, see this guide: https://github.com/ExtremeNetworksSA/API_Getting_Started (Note: the guide does not cover how to run scripts on a schedule but may in the future)

### Install Modules
There are additional modules that need to be installed in order for this script to function.  They're listed in the *requirements.txt* file and can be installed with the command `pip install -r requirements.txt` if using `PIP`.  Store the *requirements.txt* file in the same directory as the Python script file.

## User Settings
Locate in the script "Begin user settings section" (around  line 34)
  - **Authentication Options**:  [Token](#api-token) (Recommended), static entry for user/password, or prompt for credentials.
  - **CLI Command**:  Variable you can edit if something changes in the future.  This script is built around if Telnet is enabled / disabled.
  - **printToScreenResults**:  Default: **'YES'** - a variable that allows you to disable the output to screen.  If you have thousands of online devices this may not be usable.
  - **locateOfflineAPs**:  Default: **'YES'** - Allows you to disable screen & CSV output.
  - [SMTP Settings](#smtp-relay-optional-feature):  Default: `emailFeature = "DISABLE"` , Complete the fields for SMTP relay server if you want to enable email notifications.

### API Token
The default setup uses tokens for authentication to run without user prompts. Other options include hard-coded credentials (less secure) or prompting for credentials each time.

To run this script without user prompts, generate a token using `api.extremecloudiq.com`. Follow this [KB article](https://extreme-networks.my.site.com/ExtrArticleDetail?an=000102173) for details.

Brief instructions:

  1) Navigate to [API Swagger Site - api.extremecloudiq.com](https://api.extremecloudiq.com)
  2) Use the Authentication: /login API (Press: Try it out) to authenticate using a local administrator account in XIQ
  ```json
    {
    "username": "username@company.com",
    "password": "ChangeMe"
    }
  ```
  3) Press the Execute button
  4) Copy the `access_token` value (excluding the "" characters).  Note the expiration, it's 24 hours.
  ```json
    {
    "access_token": "---CopyAllTheseCharacters---",
    "token_type": "Bearer",
    "expires_in": 86400
    }
  ```
  5) Scroll to the top and press the Authorize button
  6) Paste contents in the Value field then press the **Authorize** button.  You can now execute any API's listed on the page.  **WARNING!** - You have the power to run all POST/GET/PUT/DELETE/UPDATE APIs and affect your live production VIQ environment.
  7) Scroll down to Authorization section > `/auth/apitoken` API (Press: Try it out)
  8) You need to convert a desired Token expiration date and time to EPOCH time:  Online time EPOCH converter:  https://www.epochconverter.com/
  
    EPOCH time 1717200000 corresponds to June 1, 2024, 00:00:00 UTC
  
  9) Update the `description` and `expire_time` as you see fit.  Update the permissions as shown for minimal privileges to run only specific APIs for this script.
  ```json
    "description": "Token for API Script",
    "expire_time": 1717200000,
    "permissions": [
    "auth:r","logout","device:list","device:cli"
    ]
  ```
  10) Press the **Execute** button
  11) Scroll down and copy the contents of the `access_token`:
  ```json
    "access_token": "---ThisIsYourScriptToken---",
    ^^^ Use this Token in your script ^^^
    
    Locate in your Python script and paste your token:
    XIQ_Token = "---ThisIsYourScriptToken---"
  ```

### SMTP Relay (Optional Feature)
This script uses an SMTP relay to email alerts.  Tested with a local SMTP relay server.  A free 100 messages per day cloud service called Sendgrid was used for the example but does not function without you creating an account and updating your API key, To address, and From address variables.
https://app.sendgrid.com/ (not affiliated)
- Default:  `emailFeature = "DISABLE" or ""`
- To enable change:  `emailFeature = "ENABLE"` then complete the remaining variable for your SMTP server

## Screen Output & CSV Report
1) The script outputs a report onscreen (optional) indicating which APs have Telnet enabled/disabled. Optionally includes offline APs.
2) Creates a `device-list-telnet.csv` in the same directory as the script. Write access to the directory is required.
3) If the email feature is enabled, the CSV will be included as an attachment.

>**Note:  The CSV file is overritten each time the script is ran.**

### Example CSV Output:

| HOSTNAME | STATUS | BUILDING | FLOOR | IP | POLICY | MODEL | TELNET ENABLED |
| -------: | ------:| --------:| -----:| --:| ------:| -----:| --------------:|
| AP1 | Online | Bldg | Floor | 10.10.10.10 | MyNetworkPolicy | AP_3000 | Enabled - hive <name> manage telnet | 
| AP2 | Online | Bldg | Floor | 10.10.10.11 | MyNetworkPolicy | AP_4000 | Disabled |
| AP4 | Offline | Bldg | Floor | 10.10.10.12 | MyNetworkPolicy | AP_5010 | Unknown |

Chart Explanation:
- AP1 is online and Telnet is enabled.
- AP2 is online and Telnet is disabled.
- AP3 is offline and Telnet is unknown (APIs can't run against offline devices).
