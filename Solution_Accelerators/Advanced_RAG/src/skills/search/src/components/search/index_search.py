import logging
import time
from typing import Optional

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient, SearchItemPaged
from azure.search.documents.indexes.models import SearchField
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import QueryType, VectorizedQuery
from typing import Dict, List

from common.clients.openai.openai_client import AzureOpenAIClient
from common.clients.openai.openai_embeddings_configuration import OpenAIEmbeddingsConfiguration
from common.contracts.skills.search.api_models import SearchQuery, Filter, FilterType
from common.telemetry.app_logger import AppLogger
from components.shared.errors import VectorSearchError, SearchIndexError
from components.models.config_models import SearchFieldConfig, SearchType
from components.utils.object_utils import are_equal_string_lists


class SearchIndex:
    filterable_fields: List[str] = []
    facetable_fields: List[str] = []
    search_client: SearchClient = None
    index_client: SearchIndexClient = None
    fields: List[SearchField] = []

    item_id_field: str = ""
    product_id_field: str = ""
    category_field: str = ""
    image_description_fields: List[str] = []

    def __init__(
            self,
            name: str,
            search_endpoint: str,
            openai_client: AzureOpenAIClient,
            embeddings_deployment: str,
            select_fields: List[SearchFieldConfig] = [],
            vector_config: List[str] = [],
            semantic_config: str = None,
            search_type: SearchType = SearchType.keywords,
            logger: AppLogger = None
        ) -> None:
        self.name: str = name
        self.search_endpoint = search_endpoint
        self.openai_client = openai_client
        self.embeddings_deployment = embeddings_deployment
        self.search_type = search_type
        self.select_fields = select_fields
        self.vector_config = vector_config
        self.semantic_config = semantic_config
        self.logger = logger

        self._populate_index_fields()
        self._analyze_fields()


    def _populate_index_fields(self):
        index_client = self.get_index_client()
        try:
            index_data = index_client.get_index(self.name)
            self.fields = index_data.fields
        except Exception as e:
            raise SearchIndexError(
                f"Could not retrieve Cognitive Search Index '{self.name}'. Check configuration of env vars or index name")

    def _analyze_fields(self):
        '''
        Scans Search Index and determines facetable and filterable fields
        Also, validates if select fields exist in index
        '''

        facetables = list()
        filterables = list()
        valid_selectable_fields = list()
        available_fields = list()

        select_field_names = self.get_select_fields_names()
        for f in self.fields:
            if f.facetable:
                facetables.append(f.name)
            if f.filterable:
                filterables.append(f.name)
            if f.name in select_field_names:
                valid_selectable_fields.append(f.name)

            available_fields.append(f.name)

        self.facetable_fields = facetables
        self.filterable_fields = filterables

        valid_fields, fields_diff = are_equal_string_lists(
            select_field_names, valid_selectable_fields)
        if not valid_fields:
            raise ValueError(
                f"Could not find fields {list(fields_diff)} in index '{self.name}'. Valid fields = {available_fields}. Check configuration and try again")

        self.image_description_fields = []
        for select_field in self.select_fields:
            if select_field.is_item_id:
                self.item_id_field = select_field.name

            if select_field.is_product_id:
                self.product_id_field = select_field.name

            if select_field.is_product_category:
                if not select_field.name in self.filterable_fields:
                    raise ValueError(
                        "Any field mark as is_product_category must me a Filterable Field")
                if not select_field.name in self.facetable_fields:
                    raise ValueError(
                        "Any field mark as is_product_category must me a Facetable Field")

                self.category_field = select_field.name

            if select_field.contains_image_description:
                self.image_description_fields.append(select_field.name)

    def get_select_fields_names(self):
        '''
        Search Fields to be displayed in search result only
        '''
        return [x.name for x in self.select_fields]

    def get_item_id_field_name(self):
        return self.item_id_field

    def get_product_id_field_name(self):
        return self.product_id_field

    def get_category_field_name(self):
        return self.category_field

    def get_image_description_fields(self):
        return self.image_description_fields

    def get_search_client(self):
        if self.search_client == None:
            self.search_client = SearchClient(
                endpoint=self.search_endpoint,
                credential=DefaultAzureCredential(),
                index_name=self.name
            )

        return self.search_client

    def get_index_client(self):
        if self.index_client == None:
            self.index_client = SearchIndexClient(
                endpoint=self.search_endpoint,
                credential=DefaultAzureCredential(),
            )

        return self.index_client

    def _search_results_cleanup(self, result_dict: dict) -> dict:
        '''
        Removing entries in the search result dict that have None value
        '''
        return {key: value for key, value in result_dict.items() if value is not None and key != "@search.score"}

    def _get_filter_input(self, filter: Optional[Filter] = None):
        if not filter:
            return None
        
        if not all(filter.field_name in self.filterable_fields for filter in filter.search_filters):
            raise ValueError("Filter is incorrect. Specified field(s) is not filterable.")
        
        if len(filter.search_filters) > 1 and not filter.logical_operator:
            raise ValueError("Filter is incorrect. Logical Operator must be present in case of multiple filters.")

        filter_strings = list()
        for search_filter in filter.search_filters:
            match search_filter.filter_type:
                case FilterType.EQUALS:
                    filter_string = f"{search_filter.field_name} eq '{search_filter.field_value}'"
                case FilterType.NOT_EQUALS:
                    filter_string = f"not({search_filter.field_name} eq '{search_filter.field_value}')"
                case FilterType.GREATER_OR_EQUALS:
                    filter_string = f"{search_filter.field_name} ge '{search_filter.field_value}'"
                case FilterType.LESSER_OR_EQUALS:
                    filter_string = f"{search_filter.field_name} le '{search_filter.field_value}'"
                case FilterType.CONTAINS:
                    filter_string = f"{search_filter.field_name}/any(p:p eq '{search_filter.field_value}')"
                case _:
                    raise Exception(f"Search filter is currently not supported.")

            filter_strings.append(filter_string)

        return f' {filter.logical_operator.lower()} '.join(filter_strings) if filter.logical_operator and len(filter_strings) > 1 else filter_strings[0]

    async def _hybrid_keyword_or_vector_search(self, query: SearchQuery, search_query_for_embedding: str, results_count: int, search_name: str, categories: List[str] = [], search_id: str = "", semantic_config: str = None):
        ''' 
        Hybrid Keyword and Vector search share almost the same setup,
        Only difference in current sdk is passing or not the search_text in the search query

        Args:
                query (str): text search query used for keyword search (if used)
                search_query_for_embedding (str): text search query to be converted to text embedding first before used for vector search
                results_count (int): Count of search results to be returned
                search_name (str): search name to be used to be added in logging prefix
                search_id (str): id of the search query
        '''
        if search_query_for_embedding and not self.vector_config:
            raise VectorSearchError(
                f"Cannot do {search_name} search if vector_config is not defined")

        if len(categories) > 0 and self.category_field == "":
            raise VectorSearchError(
                f"Cannot do {search_name} search with filter if no field is mark as 'is_product_category'")

        embedding_start_time = time.time()
        text_embedding = (await self.openai_client.create_embedding_async(
            [OpenAIEmbeddingsConfiguration(
                content=search_query_for_embedding,
                embeddings_deployment_name=self.embeddings_deployment
            )]
        ))[0]
        duration = time.time() - embedding_start_time

        self.logger.info(
            f"{search_name}Search.TextEmbedding: duration={duration:.4f}s")

        search_client = self.get_search_client()

        search_start_time = time.time()
        vector_config = [VectorizedQuery(
            vector=text_embedding, fields=v, k_nearest_neighbors=results_count) for v in self.vector_config]
        results: SearchItemPaged[Dict] = search_client.search(
            search_text=query.search_query,
            select=self.get_select_fields_names(),
            filter=self._get_filter_input(query.filter),
            top=results_count,
            query_type=QueryType.SEMANTIC if semantic_config else QueryType.SIMPLE,
            vector_queries=vector_config,
            semantic_configuration_name=semantic_config,
        )
        duration = time.time() - search_start_time
        self.logger.debug(
            f"{search_name}Search.CognitiveSearch: sid={search_id}, duration={duration:.4f}s")

        duration = time.time() - embedding_start_time
        self.logger.info(
            f"{search_name}Search.Success: sid={search_id}, duration={duration:.4f}s")

        return self.unpack_search_results(results)

    def simple_search(self, query: SearchQuery, results_count: int, search_name: str, categories: List[str] = [], search_id: str = "", semantic_config: str = None):
        ''' 
        Keyword Search only takes text as input

        Args:
                query (str): text search query used for keyword search (if used)
                results_count (int): Count of search results to be returned
                search_id (str): id of the search query
        '''
        if len(categories) > 0 and self.category_field == "":
            raise VectorSearchError(
                f"Cannot do keyword search with filter if no field is mark as 'is_product_category'")

        search_client = self.get_search_client()
        search_start_time = time.time()
        results: SearchItemPaged[Dict] = search_client.search(
            search_text=query,
            select=self.get_select_fields_names(),
            filter=self._get_filter_input(query.filter),
            top=results_count,
            query_type=QueryType.SEMANTIC if semantic_config else QueryType.SIMPLE,
            semantic_configuration_name=semantic_config,
        )
        duration = time.time() - search_start_time

        self.logger.info(
            f"{search_name}.Success: sid={search_id}, duration={duration:.4f}s")

        return self.unpack_search_results(results)

    async def vector_search(self, query: SearchQuery, results_count: int, categories: List[str] = [], search_id: str = ""):
        return await self._hybrid_keyword_or_vector_search(
            query=None,
            search_query_for_embedding=query.search_query,
            results_count=results_count,
            search_name="Vector",
            categories=categories,
            search_id=search_id
        )

    async def hybrid_keyword_search(self, query: SearchQuery, results_count: int, categories: List[str] = [], search_id: str = ""):
        return await self._hybrid_keyword_or_vector_search(
            query=query,
            search_query_for_embedding=query.search_query,
            results_count=results_count,
            search_name="HybridKeyword",
            categories=categories,
            search_id=search_id
        )

    async def hybrid_semantic_search(self, query: SearchQuery, results_count: int, categories: List[str] = [], search_id: str = ""):
        return await self._hybrid_keyword_or_vector_search(
            query=query,
            search_query_for_embedding=query.search_query,
            results_count=results_count,
            search_name="HybridSemantic",
            categories=categories,
            search_id=search_id,
            semantic_config=self.semantic_config,
        )

    def keyword_search(self, query: SearchQuery, results_count: int, categories: List[str] = [], search_id: str = ""):
        self.simple_search(
            query=query.search_query,
            results_count=results_count,
            search_name="Keywords",
            categories=categories,
            search_id=search_id,
        )

    def semantic_search(self, query: SearchQuery, results_count: int, categories: List[str] = [], search_id: str = ""):
        self.simple_search(
            query=query.search_query,
            results_count=results_count,
            search_name="Semantic",
            categories=categories,
            search_id=search_id,
            semantic_config=self.semantic_config,
        )

    async def search(self, search_query: SearchQuery, results_count: int = 3, categories: List[str] = [], search_id: str = ""):
        if self.search_type == SearchType.vector:
            return await self.vector_search(search_query, results_count, categories, search_id)
        elif self.search_type == SearchType.hybrid_keywords:
            return await self.hybrid_keyword_search(search_query, results_count, categories, search_id)
        elif self.search_type == SearchType.hybrid_semantic:
            return await self.hybrid_semantic_search(search_query, results_count, categories, search_id)
        elif self.search_type == SearchType.semantic:
            return self.semantic_search(search_query, results_count, categories, search_id)
        else:
            return self.keyword_search(search_query, results_count, categories, search_id)

    def unpack_search_results(self, results: SearchItemPaged[Dict]):
        output = list()
        # search results come in an iterator, unpacking before returning
        for r in results:
            output.append(self._search_results_cleanup(r))

        return output

    def get_filterable_categories(self):
        if self.category_field == "":
            return []

        search_start_time = time.time()
        # must specify max number of facets, else will limit results to first 10 categories only
        results: SearchItemPaged[Dict] = self.get_search_client().search(
            search_text=None,
            top=0,
            select=self.category_field,
            facets=[f"{self.category_field},count:100"],

        )
        duration = time.time() - search_start_time
        self.logger.debug(
            f"CognitiveSearch.CategoriesFetch: duration={duration:.4f}s")

        categories = [x.get("value")
                      for x in results.get_facets().get(self.category_field)]

        return categories

    def get_items_by_category(self, category: str, max_items_sample_per_category: int = 20):
        search_client = self.get_search_client()
        search_start_time = time.time()
        results: SearchItemPaged[Dict] = search_client.search(
            search_text=None,
            select=self.get_select_fields_names(),
            filter=self._get_filter_input([category]),
            query_type=QueryType.SIMPLE,
            top=max_items_sample_per_category,
        )
        duration = time.time() - search_start_time
        self.logger.debug(
            f"CognitiveSearch.CategoryItems: duration={duration:.4f}s")

        return self.unpack_search_results(results)
