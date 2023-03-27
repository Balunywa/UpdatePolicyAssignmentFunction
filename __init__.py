import logging
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.policyinsights.models import QueryOptions
from azure.identity import ClientSecretCredential
from azure.mgmt.resource.policy import PolicyClient
from azure.mgmt.policyinsights import PolicyInsightsClient
from azure.mgmt.policyinsights.models import PolicyStatesResource
from azure.identity import ClientSecretCredential
import requests
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Check for webhook validation
    validation_code = req.headers.get("ValidationCode")
    if validation_code:
        return func.HttpResponse(validation_code)

    # Set the target application name
    target_app_name = "Azure Spring Cloud Resource Management"

    # Set your Azure AD credentials
    tenant_id = "46ebbfcd-0b34-421b-95b6-0d3be04f5baf"
    client_id = "6f8d280c-dbf1-464d-b79f-9918efbba95d"
    client_secret = "vF18Q~H3wLNHZXjXX4jimDJlldJ.T20mRJSYVcT0"

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

    subscription_id = "baba5760-b841-47cc-ad3f-0097b63b2ac7"

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

    object_id = get_enterprise_app_object_id(target_app_name)
    logging.info(f"The object ID for '{target_app_name}' is: {object_id}")

    
    # Set the assignment ID
    assignment_id = "/subscriptions/baba5760-b841-47cc-ad3f-0097b63b2ac7/providers/Microsoft.Authorization/policyAssignments/17069aaf294942ea816b5070"

    # Get the policy assignment
    policy_assignment = policy_client.policy_assignments.get_by_id(assignment_id)

    if policy_assignment:
        # Get the existing allowedPrincipalIDs parameter
        existing_allowed_principals = policy_assignment.parameters["allowedPrincipalIDs"].value if "allowedPrincipalIDs" in policy_assignment.parameters else []

        # Check if the object ID is already in the allowedPrincipalIDs list
        if object_id in existing_allowed_principals:
            logging.info("The object ID is already in the allowedPrincipalIDs list.")
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

    logging.info("The policy assignment has been updated with the new allowedPrincipalIDs.")

    return func.HttpResponse(
        json.dumps({"message": "Function completed successfully.", "updatedPolicyAssignment": updated_policy_assignment.as_dict()}),
        status_code=200,
        headers={"Content-Type": "application/json"}
    )    
