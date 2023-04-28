# Logging enterprise information in Azure OpenAI
For enterprises, logging the interactions with the Azure OpenAI models is a strong requirement.

## Key Solution Advantages:
* **Comprehensive logging of Azure OpenAI model execution tracked to Source IP address.** Log information includes what text users are submitting to the model as well as text being received back from the model. This ensures models are being used responsibly within the corporate environment and within the approved use cases of the service.
* **Advanced Usage and Throttling controls** allow fine-grained access controls for different user groups without allowing access to underlying service keys.
* **High availability of the model APIs** to ensure user requests are met even if the traffic exceeds the limits of a single Azure OpenAI service.
* **Secure use of the service** by ensuring role-based access managed via Azure Active Directory follows principle of least privilege.

[Demo Video](https://clipchamp.com/watch/WX92A7nDyR4)

[Read more](https://github.com/Azure-Samples/openai-python-enterprise-logging)
