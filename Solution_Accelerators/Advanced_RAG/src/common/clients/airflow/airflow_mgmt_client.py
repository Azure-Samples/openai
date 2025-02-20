from azure.identity import DefaultAzureCredential
from common.clients.airflow.http_client import HTTPClient

class AirflowMGMT(HTTPClient):
    def __init__(self, base_uri: str, logger, subscription_id: str, resource_group_name: str, data_factory_name: str):
        super().__init__(base_uri, logger)
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        self.data_factory_name = data_factory_name
        self.api_version = '2018-06-01'
    
    def sync_dags(self, runtime_name: str, linked_service_name: str, storage_folder_path: str):
        # ToDo: update auth and add error handling
        credential = DefaultAzureCredential()
        token = credential.get_token("https://management.azure.com/.default")
        access_token = token.token

        path = f"/subscriptions/{self.subscription_id}/resourcegroups/{self.resource_group_name}/providers/Microsoft.DataFactory/factories/{self.data_factory_name}/airflow/sync?api-version={self.api_version}"
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Content-Type': 'application/json'
        }
        data = {
            "IntegrationRuntimeName": runtime_name,
            "LinkedServiceName": linked_service_name,
            "StorageFolderPath": storage_folder_path,
            "CopyFolderStructure": True,
            "Overwrite": True,
            "AddRequirementsFromFile": True
        }

        json_response, status_code = self.make_request(path, self.HttpMethod.POST, custom_headers=headers, payload=data)

        if 200 <= status_code < 300:
            print("Sync triggered successfully!")
        else:
            print(f"Failed to trigger sync. Status code: {status_code}, Response: {json_response}")