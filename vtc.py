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
    task_id = json_response ['operation_id']
    return task_id 

def get_deployments(org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/inventory/{}/core/deployments".format(BaseURL, org_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    if (json_response['empty'] == True):
        print("\n=====No SDDC found=========")
    else:  
        for i in range(json_response['total_elements']):
            print(str(i+1) + ": " + json_response['content'][i]['name'])
    return

def get_deployment_id(sddc, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/inventory/{}/core/deployments".format(BaseURL, org_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    deployment_id = json_response['content'][int(sddc)-1]['id']
    return deployment_id

def get_group_id(group, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/inventory/{}/core/deployment-groups".format(BaseURL, org_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    group_id = json_response['content'][int(group)-1]['id']
    return group_id

def get_sddc_groups(org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/inventory/{}/core/deployment-groups".format(BaseURL, org_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    if (json_response['empty'] == True):
        print("     No SDDC Group found\n")
    else:  
        for i in range(json_response['total_elements']):
            print(str(i+1) + ": " + json_response['content'][i]['name'] + ": " + json_response['content'][i]['id'])
    return

def get_group_info(group_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/inventory/{}/core/deployment-groups/{}".format(BaseURL, org_id, group_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    print("Group Name: " + json_response['name'])
    print("Group ID  : " + json_response['id'])
    for i in range(len(json_response['membership']['included'])):
        print("Member    : " + json_response['membership']['included'][i]['deployment_id'])
    return  

def get_resource_id(group_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/core/network-connectivity-configs/?group_id={}".format(BaseURL, org_id, group_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()   
    resource_id = json_response[0]['id']
    return resource_id

def remove_sddc(deployment_id, resource_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/aws/operations".format(BaseURL, org_id)
    body = {
        "type": "UPDATE_MEMBERS",
        "resource_id": resource_id,
        "resource_type": "network-connectivity-config",
        "config" : {
            "type": "AwsUpdateDeploymentGroupMembersConfig",
            "add_members": [],
            "remove_members": [
                {
                 "id": deployment_id
                }
            ]
        }
    }
    response = requests.post(myURL, json=body, headers=myHeader)
    json_response = response.json()
    task_id = json_response ['config']['operation_id']
    return task_id 

def attach_sddc(deployment_id, resource_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/aws/operations".format(BaseURL, org_id)
    body = {
        "type": "UPDATE_MEMBERS",
        "resource_id": resource_id,
        "resource_type": "network-connectivity-config",
        "config" : {
            "type": "AwsUpdateDeploymentGroupMembersConfig",
            "add_members": [
                {
                 "id": deployment_id
                }
            ],
            "remove_members": []
        }
    }
    response = requests.post(myURL, json=body, headers=myHeader)
    json_response = response.json()
    task_id = json_response ['config']['operation_id']
    return task_id  

def check_empty_group(group_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/inventory/{}/core/deployment-groups/{}".format(BaseURL, org_id, group_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    print(len(json_response['membership']['included']))
    if (len(json_response['membership']['included']) != 0):
        return False
    return True   

def delete_sddc_group(resource_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/aws/operations".format(BaseURL, org_id)
    body = {
        "type": "DELETE_DEPLOYMENT_GROUP",
        "resource_id": resource_id,
        "resource_type": "network-connectivity-config",
        "config" : {
            "type": "AwsDeleteDeploymentGroupConfig"
        }
    }
    response = requests.post(myURL, json=body, headers=myHeader)
    json_response = response.json()
    task_id = json_response ['id']
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
    get_deployments(org_id, session_token)
    sddc = input('   Select one SDDC to attach: ')
    deployment_id = get_deployment_id(sddc, org_id, session_token)
    task_id = create_sddc_group(group_name, deployment_id, org_id, session_token) 
    get_task_status(task_id, org_id, session_token)   

elif intent_name == "delete-sddc-group":
    print("=====Deleting SDDC Group=========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)
    if (check_empty_group(group_id, org_id, session_token)):
        resource_id = get_resource_id(group_id, org_id, session_token)
        task_id = delete_sddc_group(resource_id, org_id, session_token)
        get_task_status(task_id, org_id, session_token)
    else:
        print("SDDC Group not empty: detach all members")      

elif intent_name == "get-group-info":
    print("===== SDDC Group info =========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)
    get_group_info(group_id, org_id, session_token)  

elif intent_name == "attach-sddc":
    print("===== Connecting SDDC =========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)    
    get_deployments(org_id, session_token)
    sddc = input('   Select one SDDC to attach: ')
    deployment_id = get_deployment_id(sddc, org_id, session_token)
    resource_id = get_resource_id(group_id, org_id, session_token)
    task_id = attach_sddc(deployment_id, resource_id, org_id, session_token)     
    get_task_status(task_id, org_id, session_token)       

elif intent_name == "detach-sddc":
    print("===== Removing SDDC =========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)    
    get_deployments(org_id, session_token)
    sddc = input('   Select one SDDC to detach: ')
    deployment_id = get_deployment_id(sddc, org_id, session_token)
    resource_id = get_resource_id(group_id, org_id, session_token)
    task_id = remove_sddc(deployment_id, resource_id, org_id, session_token)     
    get_task_status(task_id, org_id, session_token)

elif intent_name == "get-sddc-info":
    print("===== SDDC Info =========")
    get_deployments(org_id, session_token)

elif intent_name == "get-group-info":
    print("===== SDDC Group info =========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)
    get_group_info(group_id, org_id, session_token)    

else:
    print("\nPlease give an argument like:")
    print("    create-sddc-group [name]")
    print("    delete-sddc-group")
    print("    get-group-info\n")
    print("    get-sddc-info")
    print("    attach-sddc")
    print("    detach-sddc \n")








