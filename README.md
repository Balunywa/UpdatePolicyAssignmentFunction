# Azure Function for Updating Policy Assignment

This repository contains an Azure Function that updates a specific policy assignment's allowed principal IDs by adding a target application's object ID. The function is triggered by an Event Grid event.

## Prerequisites

- [Azure Functions Core Tools](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=windows%2Ccsharp%2Cbash#install-the-azure-functions-core-tools)
- [Azure Functions extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)

## Setup

1. Clone this repository and open it in Visual Studio Code.

2. Install the required Python packages by running `pip install -r requirements.txt`.

3. Deploy the Azure Function using the [Azure Functions extension in Visual Studio Code](https://docs.microsoft.com/en-us/azure/azure-functions/functions-create-first-function-vs-code?pivots=programming-language-python#publish-the-project-to-azure).

4. Create an Event Grid subscription that triggers the function. You can do so using the Azure Portal, Azure CLI, or any other supported method. Here's a sample Azure CLI command to create an Event Grid subscription:


az eventgrid event-subscription create
--source-resource-id <event_grid_topic_resource_id>
--name <subscription_name>
--endpoint-type azurefunction
--endpoint <function_app_resource_id>/functions/<function_name>
--subject-ends-with <event_subject_suffix>


Replace `<event_grid_topic_resource_id>`, `<subscription_name>`, `<function_app_resource_id>`, `<function_name>`, and `<event_subject_suffix>` with appropriate values.

## Usage

Once the function is deployed and the Event Grid subscription is set up, the function will automatically update the specified policy assignment's allowed principal IDs whenever it is triggered by an event from the Event Grid topic matching the specified subject suffix.
