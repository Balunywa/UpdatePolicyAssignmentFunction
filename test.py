from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
import requests
from azure.identity import ClientSecretCredential
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.policy import PolicyClient
import requests

from azure.identity import ClientSecretCredential
from azure.mgmt.policyinsights import PolicyInsightsClient
from azure.mgmt.resource import ResourceManagementClient
import requests

# Set the target application name
target_app_name = "Azure Spring Cloud Resource Management"

# Set your Azure AD credentials
tenant_id = "fef3ddf9-5e8d-4606-907f-c575d0732655"
client_id = "b01e8aaa-1c3f-4cb4-b865-99ab718370b3"
client_secret = "Gfc8Q~kWWHUtwy3wZP2zbMFR2.u915H_RoRM.bG6"

# Authenticate using the ClientSecretCredential
credential = ClientSecretCredential(tenant_id, client_id, client_secret)

# Get an access token with the required scope
token = credential.get_token("https://graph.microsoft.com/.default")

# Set up the headers for the Microsoft Graph API request
headers = {
    "Authorization": f"Bearer {token.token}",
    "Content-Type": "application/json"
}

# Define the Graph API endpoint for listing service principals
service_principals_url = "https://graph.microsoft.com/v1.0/servicePrincipals"


subscription_id = "c801a0b0-c54c-4193-9caa-4d56a72099ad"

resource_client = ResourceManagementClient(credential, subscription_id)
policy_client = PolicyClient(credential, subscription_id)

def get_enterprise_app_object_id(app_name):
    try:
        response = requests.get(service_principals_url, headers=headers)

        if response.status_code == 200:
            service_principals = response.json()["value"]

            # Find the target enterprise application
            for sp in service_principals:
                if sp["displayName"].lower() == app_name.lower():
                    return sp["id"]

            print(f"Could not find the enterprise application with the name '{app_name}'.")
            return None

        else:
            print(f"Error retrieving service principals: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the enterprise application object ID: {e}")
        return None

# Get the object ID for the target application
object_id = get_enterprise_app_object_id(target_app_name)
print(f"The object ID for '{target_app_name}' is: {object_id}")

# Set the name of the policy assignment and the policy definition ID
policy_assignment_name = "Deny-RBAC-Roles"
policy_definition_id = "428fc04ec56945b29e24ad07"

# Get the policy assignment
policy_assignments = policy_client.policy_assignments.list()
policy_assignment = next((pa for pa in policy_assignments if pa.name == policy_assignment_name), None)

if policy_assignment:
    # Get the existing allowedPrincipalIDs parameter
    existing_allowed_principals = policy_assignment.parameters.get("allowedPrincipalIDs", {}).get("value", [])

    # Add the object ID to the allowedPrincipalIDs list
    updated_allowed_principals = existing_allowed_principals + [object_id]

    # Define the updated policy parameters
    updated_policy_parameters = {
        "allowedPrincipalIDs": {
            "value": updated_allowed_principals
        }
    }

    # Update the policy assignment with the new parameters
    updated_policy_assignment = policy_client.policy_assignments.create(
        policy_assignment.scope,
        policy_assignment_name,
        {
            "location": policy_assignment.location,
            "properties": {
                "policyDefinitionId": policy_definition_id,
                "parameters": updated_policy_parameters
            }
        }
    )
   
    print("The policy assignment has been updated with the new allowedPrincipalIDs.")
else:
    print(f"Could not find the policy assignment with the name '{policy_assignment_name}'.")