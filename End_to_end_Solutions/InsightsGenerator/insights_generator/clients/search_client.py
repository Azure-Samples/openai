import json
import os
import tempfile
import uuid
import logging

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes.aio import SearchIndexClient 
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.models import (
    ComplexField,
    CorsOptions,
    SearchIndex,
    ScoringProfile,
    SearchFieldDataType,
    SimpleField,
    SearchableField
)

temp_path= "/tmp/"
logger = logging.getLogger('azure.search')
logger.setLevel(logging.DEBUG)

class AzureSearchClient(object):

    def __init__(self):
        self._service_endpoint = os.getenv("SEARCH_ENDPOINT")
        key = os.getenv("SEARCH_API_KEY")
        self._credential = AzureKeyCredential(key)
        self._admin_client = SearchIndexClient(endpoint=self._service_endpoint, credential=self._credential, logging_enable=True)
        self._index_client_map = {}

    async def close(self):
        await self._admin_client.close()
        for index_name, search_client in self._index_client_map.items( ):
            await search_client.close()

    async def create_index(self, index_name:str):
        print(f"Creating index: {index_name}")
        name = index_name
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, filterable=True, sortable=True, key=True),
            SimpleField(name="date", type=SearchFieldDataType.DateTimeOffset, filterable=True),
            SimpleField(name="location", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="profile_name", type=SearchFieldDataType.String),
            SimpleField(name="rating", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="review_title", type=SearchFieldDataType.String, analyzer_name='en.microsoft'),
            SimpleField(name="stars", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="sentiment_aspects_NL", type="Collection(Edm.String)", filterable=True),
            SimpleField(name="aspects", type="Collection(Edm.String)", filterable=True),
            SimpleField(name="aspects_and_sentiments", type="Collection(Edm.String)", filterable=True),
            SearchableField(name="review_text", type=SearchFieldDataType.String, analyzer_name='en.microsoft')
        ]
        cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
        scoring_profiles = []
        index = SearchIndex(
            name=name,
            fields=fields,
            scoring_profiles=scoring_profiles,
            cors_options=cors_options)
        try:
            result = await self._admin_client.create_index(index)
            print(f"Created index: {result}")
            print(f"Created index fields: {result.fields}")
        except Exception as e:
            print (e)
            raise Exception(f"Failed to create index {index_name}")
        
        # Preload search client for each index
        self._index_client_map[index_name] = self._admin_client.get_search_client(index_name)
        return True

    async def exists_index(self, index_name:str):
        try:
            await self._admin_client.get_index(index_name)
            self._index_client_map[index_name] = self._admin_client.get_search_client(index_name)
            return True
        except ResourceNotFoundError as ex:
            return False
        
    async def list_index(self):
        return [x for x in self._index_client_map.keys()]
    
    async def delete_index(self, index_name:str):
        try:
            result = await self._admin_client.delete_index(index_name)
            self._index_client_map.pop(index_name)
            return True
        except:
            return False
    
    async def upload_documents(self, index_name:str, documents:list[dict]):
        if await self.exists_index(index_name):
            index_client = self._index_client_map[index_name]
            print (index_client)
            try:
                result = await index_client.upload_documents(documents)
            except Exception as e:
                print (e)
            print (result)
            return result[0].succeeded
        return False

    async def search_documents(self, index_name:str, parameters:dict, top = 3):
        if await self.exists_index(index_name=index_name):
            index_client = self._index_client_map[index_name]
            print (f"Index found: {index_name}")
            try:
                print("Search client search documents parameters {}".format(parameters))
                documents = []
                async for document in await index_client.search(search_text= parameters['search_text'], filter = parameters['filter_text'], top = top, include_total_count=True):
                    documents.append(document)
                print("Num documents fetched from Az Search: {}".format(len(documents)))
                return documents
            except Exception as e:
                print (e)
            return None
