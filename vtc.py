"""

Basic Tests against the Skyscraper API
VMC API documentation available at https://vmc.vmware.com/swagger/index.html#/
CSP API documentation is available at https://saas.csp.vmware.com/csp/gateway-docs
vCenter API documentation is available at https://code.vmware.coms/191/vsphere-automation


You can install python 3.6 from https://www.python.org/downloads/windows/

You can install the dependent python packages locally (handy for Lambda) with:
pip install requests -t . --upgrade
pip install configparser -t . --upgrade

"""

import requests                         # need this for Get/Post/Delete
import configparser                     # parsing config file
import time
import json
import sys

config = configparser.ConfigParser()
config.read("./config.ini")
BaseURL         = config.get("vmcConfig", "BaseURL")
API_Token       = config.get("vmcConfig", "API_Token")
org_id          = config.get("vmcConfig", "org_id")
sddc_id         = config.get("vmcConfig", "sddc_id")





def getAccessToken(myKey):
    params = {'refresh_token': myKey}
    headers = {'Content-Type': 'application/json'}
    response = requests.post('https://console.cloud.vmware.com/csp/gateway/am/api/auth/api-tokens/authorize', params=params, headers=headers)
    json_response = response.json()
    access_token = json_response['access_token']
    return access_token
   
def get_task_status(task_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/operation/{}/core/operations/{}".format(BaseURL, org_id, task_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    status = json_response ['state']['name']
    print(status)
    start = time.time()
    while(status != "COMPLETED"):
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(2)
        response = requests.get(myURL, headers=myHeader)
        json_response = response.json()
        status = json_response ['state']['name']
        if status == "FAILED":
            print("\nTask FAILED ")
            print(json_response['error_message'])
            break
    elapse = time.time() - start
    minutes = elapse // 60
    seconds = elapse - (minutes * 60)
    print("\nFINISHED in", '{:02}min {:02}sec'.format(int(minutes), int(seconds)))
    return 



def create_sddc_group(name, deployment_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/core/network-connectivity-configs/create-group-network-connectivity".format(BaseURL, org_id)
    body = {
        "name": name,
        "description": name,
        "members": [
            {
                "id": deployment_id
            }
        ]
    }
    response = requests.post(myURL, json=body, headers=myHeader)
    json_response = response.json()
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
    task_id = json_response ['operation_id']
    return task_id 




# --------------------------------------------
# ---------------- Main ----------------------
# --------------------------------------------

# Get our access token
session_token = getAccessToken(API_Token)

# what does our user want us to do
if len(sys.argv) > 1:
    intent_name = sys.argv[1]
else:
    intent_name = ""

#------------------------
#--- execute the user's command
#------------------------

if intent_name == "create-sddc-group":
    print("\n=====Creating SDDC Group=========")
    group_name = sys.argv[2]
    task_id = create_sddc_group(group_name, sddc_id, org_id, session_token) 
    get_task_status(task_id, org_id, session_token)

else:
    print("\nPlease give an argument like:")
    print("    create-sddc-group [name]")
    








