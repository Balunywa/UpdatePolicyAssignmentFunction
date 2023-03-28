from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.policyinsights.models import QueryOptions
from azure.identity import ClientSecretCredential
from azure.mgmt.resource.policy import PolicyClient
from azure.mgmt.policyinsights import PolicyInsightsClient
from azure.mgmt.policyinsights.models import PolicyStatesResource
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
import requests



# Set the target application name
#target_app_name = "Azure Spring Cloud Resource Management"

# Set the Key Vault URL
#key_vault_url = "https://<your-key-vault-name>.vault.azure.net/"
key_vault_url = "https://deny-all-keys.vault.azure.net/"

# Initialize the SecretClient with the DefaultAzureCredential
secret_client = SecretClient(vault_url=key_vault_url, credential=DefaultAzureCredential())

# Retrieve the secrets from Azure Key Vault
tenant_id = secret_client.get_secret("tenantId").value
client_id = secret_client.get_secret("clientId").value
client_secret = secret_client.get_secret("clientSecret").value

# Retrieve the target_app_name from Azure Key Vault
target_app_name = secret_client.get_secret("targetAppName").value


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
policyInsightsClient = PolicyInsightsClient(credential, subscription_id)

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
    

object_id = get_enterprise_app_object_id(target_app_name)
print(f"The object ID for '{target_app_name}' is: {object_id}")


# Set the assignment ID
assignment_id = "/subscriptions/c801a0b0-c54c-4193-9caa-4d56a72099ad/providers/Microsoft.Authorization/policyAssignments/428fc04ec56945b29e24ad07"

# Get the policy assignment
policy_assignment = policy_client.policy_assignments.get_by_id(assignment_id)

if policy_assignment:
    # Get the existing allowedPrincipalIDs parameter
    existing_allowed_principals = policy_assignment.parameters["allowedPrincipalIDs"].value if "allowedPrincipalIDs" in policy_assignment.parameters else []

    # Check if the object ID is already in the allowedPrincipalIDs list
    if object_id in existing_allowed_principals:
        print("The object ID is already in the allowedPrincipalIDs list.")
    else:
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
            policy_assignment.name,
            {
                "location": policy_assignment.location,
                "properties": {
                    "policyDefinitionId": policy_assignment.policy_definition_id,
                    "parameters": updated_policy_parameters
                }
            }
        )
       
        print("The policy assignment has been updated with the new allowedPrincipalIDs.")
else:
    print(f"Could not find the policy assignment with the ID '{assignment_id}'.")