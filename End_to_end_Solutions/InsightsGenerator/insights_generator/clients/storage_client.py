import asyncio
import json
import logging
import os
import tempfile
import uuid
from azure.storage.blob.aio import BlobServiceClient

temp_path= "/tmp/"
#logger = logging.getLogger('azure')
#logger.setLevel(logging.DEBUG)

class StorageClient(object):

    def __init__(self, container: str):
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string, logging_enable=True)
        self.container_client = None
        try:
            logging.info(f"Fetching container {container}")
            self.container_client = self.blob_service_client.get_container_client(container)
            logging.info(f"Loaded container {container}")
        except ResourceNotFoundError:
            logging.info(f"Creating container {container}")
            asyncio.run(self.blob_service_client.create_container(container))
            self.container_client = self.blob_service_client.get_container_client(container)
            logging.info(f"Loaded container {container}")

    async def close(self):
        await self.blob_service_client.close()
        return True

    async def set(self, blob_name:str, data):
        try:
            logging.info(f"Writing blob: {blob_name} with data: {data}")
            local_file_name = blob_name if ".json" in blob_name else f"{blob_name}.json" 
            upload_file_path = os.path.join(temp_path, local_file_name)
            with open(upload_file_path, mode='w') as writer:
                json.dump(data, writer)
            with open(upload_file_path, mode="rb") as reader:
                blob_client = self.container_client.get_blob_client(local_file_name)
                logging.info(f"blob client: {blob_client}")
                await blob_client.upload_blob(reader, blob_type="BlockBlob", overwrite=True)
                
            logging.info(f"Writing blob completed: {blob_name}")
            return True
        except:
            return False

    async def get(self, blob_name:str):
        logging.info(f"Reading blob: {blob_name}")
        local_file_name = blob_name if ".json" in blob_name else blob_name + ".json"
        blob_client = self.container_client.get_blob_client(local_file_name)
        stream = await blob_client.download_blob()
        data = await stream.readall()
        logging.info(f"Reading blob completed: {blob_name}")
        return json.loads(data)
        
    async def list(self):
        logging.info(f"Reading blob list")
        project_list = []
        async for blob in self.container_client.list_blobs():
            project_list.append(await self.get(blob.name))
        logging.info(f"Read {len(project_list)} blobs.")
        return project_list
    
    async def delete(self, blob_name:str):
        try:
            logging.info(f"Deleting blob: {blob_name}")
            local_file_name = blob_name if ".json" in blob_name else blob_name + ".json"
            blob_client = self.container_client.get_blob_client(local_file_name)
            await blob_client.delete_blob()
            logging.info(f"Deleting blob completed: {blob_name}")
            return True
        except:
            return False
