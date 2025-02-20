import io
import os

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob.aio._blob_service_client_async import BlobServiceClient
from PyPDF2 import PdfReader, PdfWriter

from common.telemetry.app_logger import AppLogger


class AzureStorageClient():
    '''
    Creates an Azure Storage Client to facilitate uploading files by page.
    '''
    def __init__(
        self,
        storage_account_name: str,
        logger: AppLogger
    ) -> None:
        self.blob_client = BlobServiceClient(
            account_url=f"https://{storage_account_name}.blob.core.windows.net",
            credential=DefaultAzureCredential()
        )

        self.logger = logger

    async def validate_container_async(self, blob_container_name: str) -> bool:
        return await self.blob_client.get_container_client(blob_container_name).exists()

    async def download_file_async(self, blob_container_name: str, filename: str):
        blob_container = self.blob_client.get_container_client(blob_container_name)
        blob_client = blob_container.get_blob_client(filename)

        try:
            blob_reader = await blob_client.download_blob()
            return await blob_reader.readall(), blob_client.url
        except ResourceNotFoundError:
            self.logger.error(f"Specified blob {filename} does not exist.")
            return None, None

    async def upload_file_by_page_async(self, blob_container_name: str, file_path: str, task_id: str) -> bool:
        '''
        Uploads a file from local storage to the Blob store under the specified container.
        '''
        if not os.path.isfile(file_path):
            return False

        total_pages = 0
        try:
            blob_container = self.blob_client.get_container_client(blob_container_name)
            container_exists = await blob_container.exists()
            if not container_exists:
                await blob_container.create_container()

            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            for i, page in enumerate(reader.pages, start=1):
                blob_name = self.__get_blob_file_name(filename=file_path, page=i)

                pdf_writer = PdfWriter()
                pdf_writer.add_page(page)

                page_as_bytes = io.BytesIO()
                pdf_writer.write(page_as_bytes)
                page_as_bytes.seek(0)

                await blob_container.upload_blob(blob_name, page_as_bytes, overwrite=True)
        except Exception as ex:
            self.logger.error(f"Task {task_id}. Failed to upload file {file_path} by pages to blob store.\nError {ex}")
            return False

        self.logger.info(f"Task {task_id}. Document {file_path} by page uploaded to storage successfully. Total pages uploaded: {total_pages}")
        return True

    async def upload_parsed_document_async(self, blob_container_name: str, content: bytes, document_name: str, markdown: bool, task_id: str) -> bool:
        '''
        Uploads raw parsed content from document loader as PDF file under the specified container.
        '''
        try:
            blob_container = self.blob_client.get_container_client(blob_container_name)
            container_exists = await blob_container.exists()
            if not container_exists:
                await blob_container.create_container()

            blob_name = f"{self.__get_blob_file_name(filename=document_name)}/parsed/document_{self.__get_blob_file_name(filename=document_name)}"
            blob_name += ".md" if markdown else ".txt"
            await blob_container.upload_blob(blob_name, content, overwrite=True)

            self.logger.info(f"Task {task_id}. Parsed Document {document_name} uploaded to storage successfully.")
            return True
        except Exception as ex:
            self.logger.error(f"Task {task_id}. Failed to upload file {document_name} by pages to blob store.\nError {ex}")
            return False

    def __get_blob_file_name(self, filename: str, page: int = 0) -> str:
        '''
        Generates a filename with page information.
        '''
        abs_file_name = os.path.splitext(os.path.basename(filename))[0]
        return f'{abs_file_name}/{abs_file_name}-{page}.pdf' if page != 0 else abs_file_name