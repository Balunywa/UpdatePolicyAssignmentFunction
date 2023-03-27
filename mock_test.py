from azure.functions import HttpRequest
from __init__ import main


# Create a mock request
mock_request = HttpRequest("POST", "/api/your-endpoint", body="...")

# Call the main function with the mock request
response = main(mock_request)

# Do something with the response
print(response.get_body())
