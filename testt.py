import logging
import azure.functions as func
import json
import requests
import os

def main(event: func.EventGridEvent):
    logging.info('Python EventGrid trigger function processed an event: %s', event.get_json())

    event_data = event.get_json()

    # Check if the event is for Azure Spring Resource Manager creation
    if event_data['eventType'] == 'Microsoft.Resources.ResourceWriteSuccess' and \
       event_data['data']['operationName'] == 'Microsoft.Resources/deployments/write' and \
       'spring' in event_data['data']['resourceUri']:

        # Extract the Object ID from event data
        object_id = event_data['data']['properties']['servicePrincipalProfile']['clientId']

        # Update the allowed list of Object IDs in the policy assignment and reassign the policy
        update_policy_assignment(object_id)

def update_policy_assignment(object_id):
    # Set your tenant ID, subscription ID, client ID, and client secret
    tenant_id = os.environ['TENANT_ID']
    subscription_id = os.environ['SUBSCRIPTION_ID']
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']
    resource_group = os.environ['RESOURCE_GROUP']
    policy_assignment_name = os.environ['POLICY_ASSIGNMENT_NAME']

    # Authenticate and get access token
    authority_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/token'
    token_payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'resource': 'https://management.azure.com/'
    }
    token_response = requests.post(authority_url, data=token_payload).json()
    access_token = token_response['access_token']

    # Get current policy assignment
    policy_assignment_url = f'https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Authorization/policyAssignments/{policy_assignment_name}?api-version=2021-06-01'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    policy_assignment_response = requests.get(policy_assignment_url, headers=headers).json()

    # Add the new Object ID to the allowed list
    allowed_principal_ids = policy_assignment_response['properties']['parameters']['allowedPrincipalIDs']['value']
    allowed_principal_ids.append(object_id)

    # Update the policy assignment with the new allowed list of Object IDs
    policy_assignment_update_payload = {
    'properties': {
        'parameters': {
            'allowedPrincipalIDs': {
                'value': allowed_principal_ids
            }
        }
    }
   }
  
    policy_assignment_update_response = requests.put(policy_assignment_url, headers=headers, json=policy_assignment_update_payload)

    if policy_assignment_update_response.status_code == 200:
        logging.info(f'Updated policy assignment {policy_assignment_name} with new Object ID: {object_id}')
    else:
        logging.error(f'Failed to update policy assignment {policy_assignment_name}')

