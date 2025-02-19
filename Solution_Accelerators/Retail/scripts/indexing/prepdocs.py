import argparse
import html
import io
import openai
import os
import re
import time
import tiktoken
import backoff
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchFieldDataType,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    SearchableField,
    SearchField,
    VectorSearch
)
from azure.storage.blob import BlobServiceClient
from typing import List
from pypdf import PdfReader, PdfWriter
from utils.cli import config
from utils.common import blob_name_from_file_page, table_to_html

args = config

# Use the current user identity to connect to Azure services unless a key is explicitly set for any of them
azd_credential = AzureDeveloperCliCredential() if args.tenantid == None else AzureDeveloperCliCredential(
    tenant_id=args.tenantid)
default_creds = azd_credential if args.searchkey == None or args.storagekey == None else None
search_creds = default_creds if args.searchkey == None and default_creds is not None else AzureKeyCredential(args.searchkey)

openai.api_type = "azure"
openai.api_version = "2024-02-15-preview"

skipvectorization = True if args.skipvectorization.lower() == "true" else False if args.skipvectorization.lower() == "false" else None
if skipvectorization is None:
    raise ValueError("skipvectorization must be 'true' or 'false'")

if not args.skipblobs:
    storage_creds = default_creds if args.storagekey == None else args.storagekey

if not args.localpdfparser:
    # check if Azure Document Intelligence credentials are provided
    if args.documentintelligenceservice == None:
        print(
            "Error: Azure Document Intelligence service is not provided. Please provide documentintelligenceservice or use --localpdfparser for local pypdf parser.")
        exit(1)
    documentintelligence_creds = default_creds if args.documentintelligencekey == None and default_creds is not None else AzureKeyCredential(
        args.documentintelligencekey)

def upload_blobs(filename):
    blob_service = BlobServiceClient(account_url=f"https://{args.storageaccount}.blob.core.windows.net",
                                     credential=storage_creds)
    blob_container = blob_service.get_container_client(args.container)
    if not blob_container.exists():
        blob_container.create_container()

    # if file is PDF split into pages and upload each page as a separate blob
    if os.path.splitext(filename)[1].lower() == ".pdf":
        reader = PdfReader(filename)
        pages = reader.pages
        for i in range(len(pages)):
            blob_name = blob_name_from_file_page(filename, i)
            if args.verbose: print(f"\tUploading blob for page {i} -> {blob_name}")
            f = io.BytesIO()
            writer = PdfWriter()
            writer.add_page(pages[i])
            writer.write(f)
            f.seek(0)
            blob_container.upload_blob(blob_name, f, overwrite=True)
    else:
        blob_name = blob_name_from_file_page(filename)
        with open(filename, "rb") as data:
            blob_container.upload_blob(blob_name, data, overwrite=True)

def remove_blobs(filename):
    if args.verbose: print(f"Removing blobs for '{filename or '<all>'}'")
    blob_service = BlobServiceClient(account_url=f"https://{args.storageaccount}.blob.core.windows.net",
                                     credential=storage_creds)
    blob_container = blob_service.get_container_client(args.container)
    if blob_container.exists():
        if filename == None:
            blobs = blob_container.list_blob_names()
        else:
            prefix = os.path.splitext(os.path.basename(filename))[0]
            blobs = filter(lambda b: re.match(f"{prefix}-\d+\.pdf", b), blob_container.list_blob_names(
                name_starts_with=os.path.splitext(os.path.basename(prefix))[0]))
        for b in blobs:
            if args.verbose: print(f"\tRemoving blob {b}")
            blob_container.delete_blob(b)

def get_document_text(filename):
    offset = 0
    page_map = []
    if args.localpdfparser:
        reader = PdfReader(filename)
        pages = reader.pages
        for page_num, p in enumerate(pages):
            page_text = p.extract_text()
            page_map.append((page_num, offset, page_text))
            offset += len(page_text)
    else:
        if args.verbose: print(f"Extracting text from '{filename}' using Azure Document Intelligence service")
        form_recognizer_client = DocumentAnalysisClient(
            endpoint=f"https://{args.documentintelligenceservice}.cognitiveservices.azure.com/",
            credential=documentintelligence_creds, headers={"x-ms-useragent": "azure-search-chat-demo/1.0.0"})
        with open(filename, "rb") as f:
            poller = form_recognizer_client.begin_analyze_document("prebuilt-layout", document=f)
        form_recognizer_results = poller.result()

        for page_num, page in enumerate(form_recognizer_results.pages):
            tables_on_page = [table for table in form_recognizer_results.tables if
                              table.bounding_regions[0].page_number == page_num + 1]

            # mark all positions of the table spans in the page
            page_offset = page.spans[0].offset
            page_length = page.spans[0].length
            table_chars = [-1] * page_length
            for table_id, table in enumerate(tables_on_page):
                for span in table.spans:
                    # replace all table spans with "table_id" in table_chars array
                    for i in range(span.length):
                        idx = span.offset - page_offset + i
                        if idx >= 0 and idx < page_length:
                            table_chars[idx] = table_id

            # build page text by replacing characters in table spans with table html
            page_text = ""
            added_tables = set()
            for idx, table_id in enumerate(table_chars):
                if table_id == -1:
                    page_text += form_recognizer_results.content[page_offset + idx]
                elif not table_id in added_tables:
                    page_text += table_to_html(tables_on_page[table_id])
                    added_tables.add(table_id)

            page_text += " "
            page_map.append((page_num, offset, page_text))
            offset += len(page_text)

    return page_map

def chunk_content(content):
    token_limit = int(args.openAITokenLimit)
    enc = tiktoken.encoding_for_model("gpt-4")
    tokenized_content = enc.encode(content)
    section_chunks: List[str] = []

    if len(tokenized_content) > token_limit:
        if args.verbose: print("\tTokenized content is over the token limit. Chunking section...")
        # If the section content is too long, we need to chunk it into multiple inputs
        num_chunks = len(tokenized_content) // token_limit if len(tokenized_content) % token_limit == 0 else len(tokenized_content) // token_limit + 1
        chunk_size = len(tokenized_content) // num_chunks if len(tokenized_content) % num_chunks == 0 else len(tokenized_content) // num_chunks + 1
        tokenized_chunks: List[List[int]] = []
        for i in range(num_chunks):
            start = i * chunk_size
            end = min((i + 1) * chunk_size, len(content))
            tokenized_chunks.append(tokenized_content[start:end])
        section_chunks.extend([enc.decode(tokenized_chunk) for tokenized_chunk in tokenized_chunks])

        if args.verbose: print(f"\tChunked content into {num_chunks} chunks.")
    else:
        section_chunks.append(content)

    return section_chunks


@backoff.on_exception(backoff.expo,
                      (openai.error.OpenAIError, openai.error.RateLimitError),
                      max_tries=5,
                      max_value=32)
def vectorize_content(content):
    openai.api_base = f"https://{args.openAIService}.openai.azure.com"
    openai.api_key = args.openAIKey
    response = openai.Embedding.create(engine=args.openAIEngine, input=content)
    return response['data'][0]['embedding']

def create_sections(filename, page_map):
    for i, (pagenum, _, section) in enumerate(page_map):
        if skipvectorization:
            yield {
                "id": re.sub("[^0-9a-zA-Z_-]", "_", f"{filename}-{i}"),
                "content": section,
                "category": args.category,
                "sourcepage": blob_name_from_file_page(filename, pagenum),
                "sourcefile": filename
            }
        else:
            section_chunks = chunk_content(section) # Chunk the section content if it's over the token limit
            for chunk in section_chunks:
                vectorized_content = vectorize_content(chunk)
                yield {
                    "id": re.sub("[^0-9a-zA-Z_-]", "_", f"{filename}-{i}"),
                    "content": chunk,
                    "contentVector": vectorized_content,
                    "category": args.category,
                    "sourcepage": blob_name_from_file_page(filename, pagenum),
                    "sourcefile": filename
                }

def create_search_index():
    if args.verbose: print(f"Ensuring search index {args.index} exists")
    index_client = SearchIndexClient(endpoint=f"https://{args.searchservice}.search.windows.net/",
                                     credential=search_creds)
    if args.index not in index_client.list_index_names():
        fields = [
                SimpleField(name="id", type="Edm.String", key=True),
                SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
                SimpleField(name="category", type="Edm.String", filterable=True, facetable=True),
                SimpleField(name="sourcepage", type="Edm.String", filterable=True, facetable=True),
                SimpleField(name="sourcefile", type="Edm.String", filterable=True, facetable=True)
            ]

        semantic_config = SemanticConfiguration(
            name="semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                # title_field=SemanticField(field_name="title"),
                # keywords_fields=[SemanticField(field_name="category")],
                content_fields=[SemanticField(field_name="content")]))

        # Create the semantic settings with the configuration
        semantic_search = SemanticSearch(configurations=[semantic_config])

        if not skipvectorization:
            fields.append(SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                                      searchable=True, vector_search_dimensions=args.openAIDimensions, vector_search_profile_name="HnswProfile"))
            vector_search = VectorSearch(algorithms=[HnswAlgorithmConfiguration(name="Hnsw")],
                                profiles=[VectorSearchProfile(name="HnswProfile",
                                                            algorithm_configuration_name="Hnsw",)])
            index = SearchIndex(name=args.index, fields=fields, vector_search=vector_search, semantic_search=semantic_search)
        
        else:
            index = SearchIndex(name=args.index, fields=fields, semantic_search=semantic_search)

        if args.verbose: 
            print(f"Creating {args.index} search index")
        index_client.create_or_update_index(index)
    else:
        if args.verbose: print(f"Search index {args.index} already exists")


def index_sections(filename, sections):
    if args.verbose: print(f"Indexing sections from '{filename}' into search index '{args.index}'")
    search_client = SearchClient(endpoint=f"https://{args.searchservice}.search.windows.net/",
                                 index_name=args.index,
                                 credential=search_creds)
    i = 0
    batch = []
    for s in sections:
        batch.append(s)
        i += 1
        if i % 1000 == 0:
            results = search_client.upload_documents(documents=batch)
            succeeded = sum([1 for r in results if r.succeeded])
            if args.verbose: print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
            batch = []

    if len(batch) > 0:
        results = search_client.upload_documents(documents=batch)
        succeeded = sum([1 for r in results if r.succeeded])
        if args.verbose: print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")


def remove_from_index(filename):
    if args.verbose: print(f"Removing sections from '{filename or '<all>'}' from search index '{args.index}'")
    search_client = SearchClient(endpoint=f"https://{args.searchservice}.search.windows.net/",
                                 index_name=args.index,
                                 credential=search_creds)
    while True:
        filter = None if filename == None else f"sourcefile eq '{os.path.basename(filename)}'"
        r = search_client.search("", filter=filter, top=1000, include_total_count=True)
        if r.get_count() == 0:
            break
        r = search_client.delete_documents(documents=[{"id": d["id"]} for d in r])
        if args.verbose: print(f"\tRemoved {len(r)} sections from index")
        # It can take a few seconds for search results to reflect changes, so wait a bit
        time.sleep(2)


if args.removeall:
    remove_blobs(None)
    remove_from_index(None)
else:
    if not args.remove:
        create_search_index()

    print(f"Processing files...")
    for root, dirs, files in os.walk(args.files):
        for file in files:
            filename = os.path.join(root, file)
            if args.verbose: print(f"Processing '{filename}'")
            if args.remove:
                remove_blobs(filename)
                remove_from_index(filename)
            elif args.removeall:
                remove_blobs(None)
                remove_from_index(None)
            else:
                if not args.skipblobs:
                    upload_blobs(filename)
                page_map = get_document_text(filename)
                sections = create_sections(os.path.basename(filename), page_map)
                index_sections(os.path.basename(filename), sections)