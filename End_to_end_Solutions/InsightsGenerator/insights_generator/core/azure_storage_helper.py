from insights_generator.clients.storage_client import StorageClient
from insights_generator.models.create_project_request import CreateProjectRequest
from insights_generator.models.project import Project
from datetime import datetime, timezone
import logging

async def create_project_by_name(body):
    """create a project

    The metadata for a project are stored in Azure Storage.

    :param body: The metadata of the project. Must have the keys: "name", productCategory", "productName"
    :type body: dict
    :returns: metadata of project
    :rtype: dict
    """

    projects_metadata_storage_client = StorageClient("projects")
    try:
        create_request = CreateProjectRequest.from_dict(body)
        
        new_project = Project(name = create_request.name,
                product_category = create_request.product_category,
                product_name = create_request.product_name,
                created_at = str(datetime.now(timezone.utc)))
        success = await projects_metadata_storage_client.set(create_request.name, new_project.to_dict())
        if success:
            await projects_metadata_storage_client.close()
            return new_project.to_dict()
        else:
            raise Exception("Failed to upload blob")
    except Exception as e:
        logging.error("The error raised is: ", e)
        await projects_metadata_storage_client.close()

    return None