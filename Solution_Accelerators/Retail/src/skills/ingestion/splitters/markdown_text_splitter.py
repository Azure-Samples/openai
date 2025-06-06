import uuid
import re
import difflib
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from common.clients.openai.openai_client import AzureOpenAIClient
from common.clients.openai.openai_embeddings_configuration import OpenAIEmbeddingsConfiguration
from common.telemetry.app_logger import AppLogger
from langchain.text_splitter import MarkdownHeaderTextSplitter as LangChainMarkdownHeaderSplitter
from langchain_core.documents.base import Document

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    AnalyzeResult,
    ContentFormat,
    DocumentAnalysisFeature,
)

from splitters.utils.text_utils import (
    clean_up_text,
    get_chunks_within_max_length,
    get_base_file_name,
    get_file_name_with_page
)

@dataclass
class SplitMetadata:
    original_split: str
    current_length: int = 0
    content_by_page: Dict[int, int] = field(default_factory=Dict)
    headings: List[str] = field(default_factory=List)

@dataclass
class DocumentSplit:
    split: str
    source_page: str
    headings: List[str] = field(default_factory=List)

class MarkdownHeaderTextSplitter:
    def __init__(
        self,
        logger: AppLogger,
        openai_client: AzureOpenAIClient,
        embeddings_deployment_name: str,
        max_chunk_size: int,
        markdown_content_include_image_captions: bool,
        azure_document_intelligence_endpoint: str,
        azure_document_intelligence_key: str,
        headers_to_split_on: Optional[str] = None
    ) -> None:
        self.logger = logger

        self.openai_client = openai_client
        self.embeddings_deployment_name = embeddings_deployment_name

        self.max_chunk_size = max_chunk_size
        self.markdown_content_include_image_captions = markdown_content_include_image_captions

        self.document_analyzer_client = DocumentIntelligenceClient(
            endpoint=azure_document_intelligence_endpoint,
            credential=AzureKeyCredential(azure_document_intelligence_key)
        )

        if headers_to_split_on is not None:
            self.headers_to_split_on = [header.strip() for header in headers_to_split_on.split('|')]

    async def generate_splits_async(self, document_file_path: str, analyzed_document: AnalyzeResult, reported_year: str, subsidiary: str, task_id: str) -> List:
        '''
        Splits the document based on the markdown tags generated by Azure Document Intelligence.

        Returns a list of individual splits based on headers_to_split_on setting.
        '''
        if not analyzed_document:
            self.logger.error("Found empty document string. Skipping splits generation.")
            return []

        parsed_content = analyzed_document.content

        # Generate split configuration based on markdown headers.
        split_headers = []
        if self.headers_to_split_on is not None and len(self.headers_to_split_on) > 0:
            for i, header in enumerate(self.headers_to_split_on, start = 1):
                split_headers.append(("#" * i, header))

        # Create Markdown splitter with header configuration and include headers.
        text_splitter = LangChainMarkdownHeaderSplitter(
            headers_to_split_on=split_headers,
            strip_headers=False
        )

        content_by_page = {}
        for page in range(len(analyzed_document.pages)):
            content_by_page[page + 1] = self.get_page_content(document_file_path, page + 1)

        # Generate splits and associated page level metadata.
        markdown_splits = text_splitter.split_text(parsed_content)
        splits = self.generate_page_metadata_for_splits(content_by_page, document_file_path, markdown_splits, len(analyzed_document.pages))

        # Create documents for index upload based on Search index schema.
        return await self.__generate_index_documents(
            document_file_path,
            splits,
            reported_year,
            subsidiary,
            task_id
        )

    async def __generate_index_documents(self, file_path: str, documents: List[DocumentSplit], reported_year: str, subsidiary: str, task_id: str) -> List[Dict]:
        splits: List[Dict] = []
        for document in documents:
            for content in get_chunks_within_max_length(document.split, self.max_chunk_size):
                # Clean up content if cleanup enabled
                # If cleanup is enabled and content is all markdown, ignore and go to next section.
                content = clean_up_text(content, include_image_descriptions=self.markdown_content_include_image_captions)
                if not content:
                    continue

                splits.append({
                    "id": f"{get_base_file_name(file_path)}-{uuid.uuid4()}",
                    "content": content,
                    "contentVector": (await self.openai_client.create_embedding_async(
                        openai_configs=[
                            OpenAIEmbeddingsConfiguration(
                                content=content,
                                embeddings_deployment_name=self.embeddings_deployment_name
                            )
                        ]
                    ))[0],
                    "sourcePage": document.source_page,
                    "sourceFile": get_base_file_name(file_path, include_extension=True),
                    "headings": document.headings,
                    "reportedYear": reported_year,
                    "subsidiary": subsidiary
                })

        self.logger.info(f"Task {task_id}. Successfully generated splits. Total count: {len(splits)}")
        return splits

    def generate_page_metadata_for_splits(self, content_by_page: dict, file_path: str, splits: List[Document], total_pages: int) -> List[DocumentSplit]:
        if not splits:
            self.logger.info(f"No splits found for document {file_path}")

        page_number = 1
        split_idx = 0
        current_content = ""

        split_to_metadata_map: Dict[str, SplitMetadata] = {}

        while page_number <= total_pages:
            current_content += self.clean_up_split_text(content_by_page[page_number])

            while split_idx < len(splits):
                # Remove line breaks, figure tags from split text before comparison.
                split_content = self.clean_up_split_text(splits[split_idx].page_content)

                # For really small splits with length < 25, add them as is and continue to the next split.
                if len(split_content) < 25:
                    split_to_metadata_map[split_content] = SplitMetadata(
                        original_split=splits[split_idx].page_content,
                        current_length=len(split_content),
                        content_by_page=
                        {
                            page_number: len(split_content)
                        },
                        headings=list(set(splits[split_idx].metadata.values()))
                    )

                    split_idx += 1
                    continue

                # Get overlap between the current split and the current page content.
                # Overlap plays role in the following way:
                # 1. Overlap dictates how much of the split content is present in the current page.
                #    There could be partial overlap or a complete overlap.
                # 2. If there is overlapping content, then the length of the overlap also dictates
                #    which page will be assigned as the "sourcePage" for a given split.
                overlap = self.get_chunk_overlap_with_current_page(
                    split_content=split_content,
                    page_content=content_by_page[page_number]
                )

                # If split content is completely within the current content, then we can register the split.
                if split_content in current_content:
                    if split_content in split_to_metadata_map:
                        split_to_metadata_map[split_content].content_by_page[page_number] = len(overlap)
                    else:
                        split_to_metadata_map[split_content] = SplitMetadata(
                            original_split=splits[split_idx].page_content,
                            current_length=len(split_content),
                            content_by_page=
                            {
                                page_number: len(split_content)
                            },
                            headings=list(set(splits[split_idx].metadata.values()))
                        )

                    # Remove split content from current content to keep the remaining content.
                    # Next split could be compared from the new beginning of the current content.
                    current_content = current_content.replace(split_content, "")
                    split_idx += 1
                else:
                    if overlap:
                        if split_content in split_to_metadata_map:
                            split_to_metadata_map[split_content].content_by_page[page_number] = len(overlap)
                            split_to_metadata_map[split_content].current_length += len(overlap)
                        # Else, add new entry for the split.
                        else:
                            split_to_metadata_map[split_content] = SplitMetadata(
                                original_split=splits[split_idx].page_content,
                                current_length=len(overlap),
                                content_by_page=
                                {
                                    page_number: len(overlap)
                                },
                                headings=list(set(splits[split_idx].metadata.values()))
                            )

                        break
                    else:
                        # Current page content must be over, so move to next page
                        # Increment page number, but not the split index as we still
                        # need to establish a full/partial match.
                        break

            # Increment page number when the content from current
            # page is fully exhausted.
            page_number += 1

        # Generate final result set with page number from source document.
        document_splits: List[DocumentSplit] = []
        for split_content, metadata in split_to_metadata_map.items():
            document_splits.append(
                DocumentSplit(
                    split=metadata.original_split,
                    source_page=self.get_source_page(file_path, metadata.content_by_page),
                    headings=metadata.headings
                )
            )

        return document_splits

    def get_chunk_overlap_with_current_page(self, split_content: str, page_content: str):
        seq_match_calculator = difflib.SequenceMatcher(None, page_content, split_content, autojunk=False)

        # Use position on page content to extract the overlap since there could be
        # a full overlap on the split.
        pos_a, _, size = seq_match_calculator.find_longest_match(0, len(page_content), 0, len(split_content))
        return page_content[pos_a:pos_a+size]

    def get_page_content(self, document_path: str, page_number: Optional[int] = None) -> str:
        try:
            with open(document_path, "rb") as fd:
                document_as_bytes = fd.read()

                analyze_document_request = AnalyzeDocumentRequest(bytes_source=document_as_bytes)
                poller = self.document_analyzer_client.begin_analyze_document(
                    "prebuilt-layout",
                    analyze_document_request,
                    features=[DocumentAnalysisFeature.OCR_HIGH_RESOLUTION],
                    output_content_format=ContentFormat.MARKDOWN,
                    pages=str(page_number) if page_number else None
                )

                return poller.result().content
        except Exception:
            self.logger.error(f"Failed for page {page_number}. {document_path}.")
            raise

    def clean_up_split_text(self, input: str) -> str:
        clean_str = input.replace("\n", "").replace(" ", "").replace("#", "")
        return re.sub(r'(figures\/[\d]+)', '', clean_str)

    def get_source_page(self, file_path: str, content_by_page: dict) -> str:
        return get_file_name_with_page(file_path, max(content_by_page, key=content_by_page.get))