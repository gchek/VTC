"""

Basic Tests against the Skyscraper API
VMC API documentation available at https://vmc.vmware.com/swagger/index.html#/
CSP API documentation is available at https://saas.csp.vmware.com/csp/gateway-docs
vCenter API documentation is available at https://code.vmware.coms/191/vsphere-automation


You can install python 3.9 from https://www.python.org/downloads/windows/

You can install the dependent python packages locally (handy for Lambda) with:
pip install requests -t . --upgrade
pip install configparser -t . --upgrade

OR

use pip install -r requirements.txt

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
aws_acc         = config.get("vmcConfig", "MyAWS")
region          = config.get("vmcConfig", "AWS_region")
dxgw_id         = config.get("vmcConfig", "DXGW_id")
dxgw_owner      = config.get("vmcConfig", "DXGW_owner")





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
    new_session_token = ""
    while(status != "COMPLETED"):
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(2)
        elapse = time.time() - start
        if elapse >= 1700 : # session_token is only valid for 1800 sec. Over 1700, will need a new token.
            if not new_session_token :
                sys.stdout.write("Generating a new session_token")
                new_session_token = getAccessToken(refresh_Token)
                myHeader = {'csp-auth-token': new_session_token}    #update the header with new session_token
        response = requests.get(myURL, headers=myHeader)
        json_response = response.json()
        # pretty_data = json.dumps(response.json(), indent=4)
        # print(pretty_data)
        status = json_response ['state']['name']
        if status == "FAILED":
            print("\nTask FAILED ")
            print("error message: " + json_response['state']['error_msg'])
            print("error code: " + json_response['state']['error_code'])
            print("message key: " + json_response['state']['name_message']['message_key'])
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

def get_deployments(org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/inventory/{}/core/deployments".format(BaseURL, org_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
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
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
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
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
    if (json_response['empty'] == True):
        print("     No SDDC Group found\n")
    else:  
        for i in range(json_response['total_elements']):
            print(str(i+1) + ": " + json_response['content'][i]['name'] + ": " + json_response['content'][i]['id'])
    return

def get_group_info(group_id, resource_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}

    myURL = "{}/inventory/{}/core/deployment-groups/{}".format(BaseURL, org_id, group_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data) 
    print("\nORG ID      : " + json_response['org_id'])
    print("SDDC Group")
    print("==========")
    print("    Name      : " + json_response['name'])
    print("    Group ID  : " + json_response['id'])
    print("    Creator   : " + json_response['creator']['user_name'])
    print("    Date/Time : " + json_response['creator']['timestamp'])

    myURL = "{}/network/{}/core/network-connectivity-configs/{}/?trait=AwsVpcAttachmentsTrait,AwsRealizedSddcConnectivityTrait,AwsDirectConnectGatewayAssociationsTrait,AwsNetworkConnectivityTrait".format(BaseURL, org_id, resource_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data) 
    print("SDDCs")
    print("=====")    
    if 'AwsRealizedSddcConnectivityTrait' in json_response['traits'] : 
        if json_response['traits']['AwsRealizedSddcConnectivityTrait']['sddcs'] != []:
            for i in range(len(json_response['traits']['AwsRealizedSddcConnectivityTrait']['sddcs'])):
                print("    SDDC_ID " + str(i+1) + ": " + json_response['traits']['AwsRealizedSddcConnectivityTrait']['sddcs'][i]['sddc_id'])  #loop here
        else:
            print("    No SDDC attached")  

    print("Transit Gateway")
    print("===============")
    if 'AwsNetworkConnectivityTrait' in json_response['traits'] : 
        print("    TGW_ID    : " + json_response['traits']['AwsNetworkConnectivityTrait']['l3connectors'][0]['id'])
        print("    Region    : " + json_response['traits']['AwsNetworkConnectivityTrait']['l3connectors'][0]['location']['name'])  
    else:
        print("    No TGW")    

    print("AWS info")
    print("========")
    if 'AwsVpcAttachmentsTrait' in json_response['traits'] : 
        if not json_response['traits']['AwsVpcAttachmentsTrait']['accounts']:
            print("    No AWS account attached")    
        else:
            print("    AWS Account  : " + json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][0]['account_number'])
            print("    RAM Share ID : " + json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][0]['resource_share_name'])
            print("    Status       : " + json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][0]['state'])
            if json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][0]['state'] == "ASSOCIATING":
                print("        Go to AWS console/RAM and accept the share and wait for Status ASSOCIATED (5-10 mins)")
            else:   
                print("VPC info")
                print("========")
                if json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][0]['attachments'] == None:
                    print("    No VPC attached")
                else:    
                    for i in range(len(json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][0]['attachments'])):
                        print("    VPC " + str(i+1) + "        :" + json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][0]['attachments'][i]["vpc_id"])
                        print("        State         : " + json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][0]['attachments'][i]["state"])
                        print("        Attachment    : " + json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][0]['attachments'][i]["attach_id"])
                        print("        Static Routes : " + (', '.join(json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][0]['attachments'][i]["configured_prefixes"])))
    else:
        print("    No AWS account attached")    

    print("DX Gateway")
    print("==========")
    if 'AwsDirectConnectGatewayAssociationsTrait' in json_response['traits'] : 
        if not json_response['traits']['AwsDirectConnectGatewayAssociationsTrait']['direct_connect_gateway_associations']:
            print("    No DXGW Association")
        else:
            print("    DXGW ID   : " +  json_response['traits']['AwsDirectConnectGatewayAssociationsTrait']['direct_connect_gateway_associations'][0]['direct_connect_gateway_id'])
            print("    DXGW Owner: " +  json_response['traits']['AwsDirectConnectGatewayAssociationsTrait']['direct_connect_gateway_associations'][0]['direct_connect_gateway_owner'])
            print("    Status    : " +  json_response['traits']['AwsDirectConnectGatewayAssociationsTrait']['direct_connect_gateway_associations'][0]['state'])
            print("    Prefixes  : " +  (', '.join(json_response['traits']['AwsDirectConnectGatewayAssociationsTrait']['direct_connect_gateway_associations'][0]['peering_regions'][0]['allowed_prefixes'])))

    else:
        print("    No DXGW Association")  
    return  

def get_resource_id(group_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/core/network-connectivity-configs/?group_id={}".format(BaseURL, org_id, group_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)    
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
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
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
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
    task_id = json_response ['config']['operation_id']
    return task_id  

def check_empty_group(group_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/inventory/{}/core/deployment-groups/{}".format(BaseURL, org_id, group_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    # print(len(json_response['membership']['included']))
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
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
    return task_id        

def connect_aws_account(account, region, resource_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/aws/operations".format(BaseURL, org_id)
    body = {
    "type": "ADD_EXTERNAL_ACCOUNT",
    "resource_id": resource_id,
    "resource_type": "network-connectivity-config",
    "config" : {
            "type": "AwsAddExternalAccountConfig",
            "account" : {
                "account_number": account,
                "regions" : [region],
                "auto_approval": "true"
            }
        }
    }
    response = requests.post(myURL, json=body, headers=myHeader)  
    json_response = response.json()
    task_id = json_response ['id']
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
    return task_id    

def get_pending_att(resource_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/core/network-connectivity-configs/{}?trait=AwsVpcAttachmentsTrait".format(BaseURL, org_id, resource_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data) 
    vpcs=[]
    n=1
    if 'AwsVpcAttachmentsTrait' in json_response['traits'] : 
        for i in range(len(json_response['traits']['AwsVpcAttachmentsTrait']['accounts'])):
            print("Account: " + json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][int(i)]['account_number'])
            if json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][int(i)]['attachments'] == None:        #'attachements' doesnt exists
                print("   No VPCs Pending Acceptance")
            else:    
                for j in range(len(json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][int(i)]['attachments'])):
                    if json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][int(i)]['attachments'][int(j)]['state'] == "PENDING_ACCEPTANCE":
                        print(str(n) +": " + "VPC attachment = " + str(json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][int(i)]['attachments'][int(j)]['attach_id']))
                        vpcs.append(json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][int(i)]['attachments'][int(j)]['attach_id'])  
                        n=n+1  
    else:
        print("No AWS account attached")                    
    return vpcs    

def attach_vpc(att_id, resource_id, org_id, account, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/aws/operations".format(BaseURL, org_id)
    body = {
    "type": "APPLY_ATTACHMENT_ACTION",
    "resource_id": resource_id,
    "resource_type": "network-connectivity-config",
    "config" : {
            "type": "AwsApplyAttachmentActionConfig",
            "account" : {
                "account_number": account,
                "attachments": [
                    {
                        "action": "ACCEPT",
                        "attach_id": att_id
                    }
                ]
            }
        }
    }
    response = requests.post(myURL, json=body, headers=myHeader)  
    json_response = response.json()
    task_id = json_response ['id']
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
    return task_id    

def get_available_att(resource_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/core/network-connectivity-configs/{}?trait=AwsVpcAttachmentsTrait".format(BaseURL, org_id, resource_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data) 
    vpcs=[]
    n=1
    for i in range(len(json_response['traits']['AwsVpcAttachmentsTrait']['accounts'])):
        print("Account: " + json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][int(i)]['account_number'])
        for j in range(len(json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][int(i)]['attachments'])):
            if json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][int(i)]['attachments'][int(j)]['state'] == "AVAILABLE":
                print(str(n) +": " + "VPC attachment = " + str(json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][int(i)]['attachments'][int(j)]['attach_id']))
                vpcs.append(json_response['traits']['AwsVpcAttachmentsTrait']['accounts'][int(i)]['attachments'][int(j)]['attach_id']) 
                n=n+1   
    return vpcs      

def detach_vpc(att_id, resource_id, org_id, account, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/aws/operations".format(BaseURL, org_id)
    body = {
    "type": "APPLY_ATTACHMENT_ACTION",
    "resource_id": resource_id,
    "resource_type": "network-connectivity-config",
    "config" : {
            "type": "AwsApplyAttachmentActionConfig",
            "account" : {
                "account_number": account,
                "attachments": [
                    {
                        "action": "DELETE",
                        "attach_id": att_id
                    }
                ]
            }
        }
    }
    response = requests.post(myURL, json=body, headers=myHeader)  
    json_response = response.json()
    task_id = json_response ['id']
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
    return task_id    

def disconnect_aws_account(account, resource_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/aws/operations".format(BaseURL, org_id)
    body = {
    "type": "REMOVE_EXTERNAL_ACCOUNT",
    "resource_id": resource_id,
    "resource_type": "network-connectivity-config",
    "config" : {
            "type": "AwsRemoveExternalAccountConfig",
            "account" : {
                "account_number": account
            }
        }
    }
    response = requests.post(myURL, json=body, headers=myHeader)  
    json_response = response.json()
    task_id = json_response ['id']
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
    return task_id       

def add_vpc_prefixes(routes, att_id, resource_id, org_id, account, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/aws/operations".format(BaseURL, org_id)
    body = {
    "type": "APPLY_ATTACHMENT_ACTION",
    "resource_id": resource_id,
    "resource_type": "network-connectivity-config",
    "config" : {
        "type": "AwsApplyAttachmentActionConfig",
        "account" : {
            "account_number": account,
            "attachments": [
                    {
                    "action": "UPDATE",
                    "attach_id": att_id,
                    "configured_prefixes": routes
                    }
                ]
            }
        }
    }
    response = requests.post(myURL, json=body, headers=myHeader)  
    json_response = response.json()
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
    task_id = json_response ['id']
    return task_id    
      
def attach_dxgw(routes, resource_id, org_id, dxgw_owner, dxgw_id, region, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/aws/operations".format(BaseURL, org_id)
    body = {
        "type": "ASSOCIATE_DIRECT_CONNECT_GATEWAY",
        "resource_id": resource_id,
        "resource_type": "network-connectivity-config",
   	    "config" : {
            "type": "AwsAssociateDirectConnectGatewayConfig",
		    "direct_connect_gateway_association": {
			    "direct_connect_gateway_id": dxgw_id,
			    "direct_connect_gateway_owner": dxgw_owner,
                "peering_region_configs": [
				    {
					"allowed_prefixes": routes,
                    "region": region
				    }
			    ]
		    }
        }
    }    
    response = requests.post(myURL, json=body, headers=myHeader)  
    json_response = response.json()
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
    task_id = json_response ['id']
    return task_id  

def detach_dxgw(resource_id, org_id, dxgw_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/aws/operations".format(BaseURL, org_id)
    body = {
        "type": "DISASSOCIATE_DIRECT_CONNECT_GATEWAY",
        "resource_id": resource_id,
        "resource_type": "network-connectivity-config",
   	    "config" : {
            "type": "AwsDisassociateDirectConnectGatewayConfig",
		    "direct_connect_gateway_association": {
			    "direct_connect_gateway_id": dxgw_id
		    }
        }
    }    
    response = requests.post(myURL, json=body, headers=myHeader)  
    json_response = response.json()
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data)
    task_id = json_response ['id']
    return task_id  

def get_route_tables(resource_id, org_id, session_token):
    myHeader = {'csp-auth-token': session_token}
    myURL = "{}/network/{}/core/network-connectivity-configs/{}/route-tables".format(BaseURL, org_id, resource_id)
    response = requests.get(myURL, headers=myHeader)
    json_response = response.json()
    # pretty_data = json.dumps(response.json(), indent=4)
    # print(pretty_data) 
    if  not json_response['content']:       #'content' is empty []
        print("    Routing Tables empty")
    else:    
        members_id = json_response['content'][0]['id']
        external_id = json_response['content'][1]['id']

        myURL = "{}/network/{}/core/network-connectivity-configs/{}/route-tables/{}/routes".format(BaseURL, org_id, resource_id, members_id)  
        response = requests.get(myURL, headers=myHeader)
        json_response = response.json()
        # pretty_data = json.dumps(response.json(), indent=4)
        # print(pretty_data) 
        print("     Members route domain: Routes to all SDDCs, VPCs and Direct Connect Gateways")
        for i in range(len(json_response['content'])):
            print("\tDestination: " + json_response['content'][i]['destination'] + "\t\tTarget: " + json_response['content'][i]['target']['id'])

        myURL = "{}/network/{}/core/network-connectivity-configs/{}/route-tables/{}/routes".format(BaseURL, org_id, resource_id, external_id)  
        response = requests.get(myURL, headers=myHeader)
        json_response = response.json()
        # pretty_data = json.dumps(response.json(), indent=4)
        # print(pretty_data) 
        print("     External (VPC and Direct Connect Gateway) route domain: Routes only to member SDDCs")
        for i in range(len(json_response['content'])):
            print("\tDestination: " + json_response['content'][i]['destination'] + "\t\tTarget: " + json_response['content'][i]['target']['id'])
    return






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
    resource_id = get_resource_id(group_id, org_id, session_token)
    get_group_info(group_id, resource_id, org_id, session_token)  

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

elif intent_name == "connect-aws":
    print("=====Connecting AWS account=========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)
    resource_id = get_resource_id(group_id, org_id, session_token)
    task_id = connect_aws_account(aws_acc, region, resource_id, org_id, session_token)     
    get_task_status(task_id, org_id, session_token)  

elif intent_name == "attach-vpc":
    print("=====Attaching VPCs=========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)    
    resource_id = get_resource_id(group_id, org_id, session_token)
    vpc_list = get_pending_att(resource_id, org_id, session_token)
    if vpc_list == []:
        print('   No VPC to attach')
    else:    
        n = input('   Select VPC to attach: ')
        task_id = attach_vpc(vpc_list[int(n)-1], resource_id, org_id, aws_acc, session_token)   
        get_task_status(task_id, org_id, session_token)      

elif intent_name == "detach-vpc":
    print("=====Detaching VPCs=========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)    
    resource_id = get_resource_id(group_id, org_id, session_token)
    vpc_list = get_available_att(resource_id, org_id, session_token)
    if vpc_list == []:
        print('   No VPC to detach')
    else:    
        n = input('  Select VPC to detach: ')
        # print(vpc_list[int(n)-1])
        task_id = detach_vpc(vpc_list[int(n)-1], resource_id, org_id, aws_acc, session_token)   
        get_task_status(task_id, org_id, session_token)  

elif intent_name == "disconnect-aws":
    print("===== Disconnecting AWS account =========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)
    resource_id = get_resource_id(group_id, org_id, session_token)
    task_id = disconnect_aws_account(aws_acc, resource_id, org_id, session_token)     
    get_task_status(task_id, org_id, session_token)   

elif intent_name == "vpc-prefixes":
    print("===== Adding/Removing VPC Static Routes =========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)    
    resource_id = get_resource_id(group_id, org_id, session_token)
    vpc_list = get_available_att(resource_id, org_id, session_token)
    if vpc_list == []:
        print('   No VPC attached')
    else:    
        n = input('   Select VPC: ')
        routes = input ('   Enter route(s) to add (space separated), or Enter to remove all: ')
        user_list = routes.split()
        task_id = add_vpc_prefixes(user_list, vpc_list[int(n)-1], resource_id, org_id, aws_acc, session_token)   
        get_task_status(task_id, org_id, session_token)           


elif intent_name == "attach-dxgw":
    print("===== Add DXGW Association =========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)    
    resource_id = get_resource_id(group_id, org_id, session_token)
    routes = input ('   Enter route(s) to add (space separated): ')
    user_list = routes.split()
    task_id = attach_dxgw(user_list, resource_id, org_id, dxgw_owner, dxgw_id, region, session_token)   
    get_task_status(task_id, org_id, session_token)  

elif intent_name == "detach-dxgw":
    print("===== Remove DXGW Association =========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)    
    resource_id = get_resource_id(group_id, org_id, session_token)
    task_id = detach_dxgw(resource_id, org_id, dxgw_id, session_token)   
    get_task_status(task_id, org_id, session_token)

elif intent_name == "show-routes":
    print("===== Show TGW route tables =========")
    get_sddc_groups( org_id, session_token)
    group = input('   Select SDDC Group: ')
    group_id = get_group_id(group, org_id, session_token)  
    resource_id = get_resource_id(group_id, org_id, session_token)
  
    get_route_tables(resource_id, org_id, session_token)   
    

else:
    print("\nPlease give an argument like:")
    print("\nSDDC-Group Operations:")
    print("    create-sddc-group [name]")
    print("    delete-sddc-group")
    print("    get-group-info\n")
    print("SDDC Operations:")
    print("    get-sddc-info")
    print("    attach-sddc")
    print("    detach-sddc \n")
    print("AWS Operations:")
    print("    connect-aws")
    print("    disconnect-aws\n")
    print("VPC Operations:")
    print("    attach-vpc")
    print("    detach-vpc")
    print("    vpc-prefixes\n")
    print("DXGW Operations:")
    print("    attach-dxgw")
    print("    detach-dxgw\n")
    print("TGW Operations:")
    print("    show-routes\n")

    













