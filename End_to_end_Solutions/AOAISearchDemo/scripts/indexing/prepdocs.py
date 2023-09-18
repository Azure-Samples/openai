import argparse
import html
import io
import openai
import os
import re
import time
import tiktoken
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureDeveloperCliCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchFieldDataType,
    SemanticConfiguration,
    SemanticField,
    SemanticSettings,
    SimpleField,
    SearchableField,
    SearchField,
    PrioritizedFields,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
    HnswParameters
)
from azure.storage.blob import BlobServiceClient
from typing import List
from pypdf import PdfReader, PdfWriter

parser = argparse.ArgumentParser(
    description="Prepare documents by extracting content from PDFs, splitting content into sections, uploading to blob storage, and indexing in a search index.",
    epilog="Example: prepdocs.py '..\data\*' --storageaccount myaccount --container mycontainer --searchservice mysearch --index myindex -v"
)
parser.add_argument("files", help="Files to be processed")
parser.add_argument("--category",
                    help="Value for the category field in the search index for all sections indexed in this run")
parser.add_argument("--skipblobs", action="store_true", help="Skip uploading individual pages to Azure Blob Storage")
parser.add_argument("--storageaccount", help="Azure Blob Storage account name")
parser.add_argument("--container", help="Azure Blob Storage container name")
parser.add_argument("--storagekey", required=False,
                    help="Optional. Use this Azure Blob Storage account key instead of the current user identity to login (use az login to set current user for Azure)")
parser.add_argument("--tenantid", required=False,
                    help="Optional. Use this to define the Azure directory where to authenticate)")
parser.add_argument("--searchservice",
                    help="Name of the Azure Cognitive Search service where content should be indexed (must exist already)")
parser.add_argument("--index",
                    help="Name of the Azure Cognitive Search index where content should be indexed (will be created if it doesn't exist)")
parser.add_argument("--searchkey", required=False,
                    help="Optional. Use this Azure Cognitive Search account key instead of the current user identity to login (use az login to set current user for Azure)")
parser.add_argument("--remove", action="store_true",
                    help="Remove references to this document from blob storage and the search index")
parser.add_argument("--removeall", action="store_true",
                    help="Remove all blobs from blob storage and documents from the search index")
parser.add_argument("--localpdfparser", action="store_true",
                    help="Use PyPdf local PDF parser (supports only digital PDFs) instead of Azure Form Recognizer service to extract text, tables and layout from the documents")
parser.add_argument("--formrecognizerservice", required=False,
                    help="Optional. Name of the Azure Form Recognizer service which will be used to extract text, tables and layout from the documents (must exist already)")
parser.add_argument("--formrecognizerkey", required=False,
                    help="Optional. Use this Azure Form Recognizer account key instead of the current user identity to login (use az login to set current user for Azure)")
parser.add_argument("--skipvectorization", help="Skip vectorization of document content")
parser.add_argument("--openAIService", required=False, help="Azure OpenAI service resource name")
parser.add_argument("--openAIKey", required=False, help="OpenAI API key")
parser.add_argument("--openAIEngine", required=False, help="OpenAI embeddings model engine name")
parser.add_argument("--openAITokenLimit", required=False, help="The max token limit for requests to the specidied OpenAI embeddings model")
parser.add_argument("--openAIDimensions", required=False,
                    help="The max number of dimensions allowed for an embeddings request to the specified OpenAI model")
parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
args = parser.parse_args()

# Use the current user identity to connect to Azure services unless a key is explicitly set for any of them
azd_credential = AzureDeveloperCliCredential() if args.tenantid == None else AzureDeveloperCliCredential(
    tenant_id=args.tenantid)
default_creds = azd_credential if args.searchkey == None or args.storagekey == None else None
search_creds = default_creds if args.searchkey == None and default_creds is not None else AzureKeyCredential(args.searchkey)
openai.api_type = "azure"
openai.api_version = "2023-03-15-preview"
skipvectorization = True if args.skipvectorization.lower() == "true" else False if args.skipvectorization.lower() == "false" else None
if skipvectorization is None:
    raise ValueError("skipvectorization must be 'true' or 'false'")
if not args.skipblobs:
    storage_creds = default_creds if args.storagekey == None else args.storagekey
if not args.localpdfparser:
    # check if Azure Form Recognizer credentials are provided
    if args.formrecognizerservice == None:
        print(
            "Error: Azure Form Recognizer service is not provided. Please provide formrecognizerservice or use --localpdfparser for local pypdf parser.")
        exit(1)
    formrecognizer_creds = default_creds if args.formrecognizerkey == None and default_creds is not None else AzureKeyCredential(
        args.formrecognizerkey)

def blob_name_from_file_page(filename, page=0):
    if os.path.splitext(filename)[1].lower() == ".pdf":
        return os.path.splitext(os.path.basename(filename))[0] + f"-{page}" + ".pdf"
    else:
        return os.path.basename(filename)

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

def table_to_html(table):
    table_html = "<table>"
    rows = [sorted([cell for cell in table.cells if cell.row_index == i], key=lambda cell: cell.column_index) for i in
            range(table.row_count)]
    for row_cells in rows:
        table_html += "<tr>"
        for cell in row_cells:
            tag = "th" if (cell.kind == "columnHeader" or cell.kind == "rowHeader") else "td"
            cell_spans = ""
            if cell.column_span > 1: cell_spans += f" colSpan={cell.column_span}"
            if cell.row_span > 1: cell_spans += f" rowSpan={cell.row_span}"
            table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
        table_html += "</tr>"
    table_html += "</table>"
    return table_html


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
        if args.verbose: print(f"Extracting text from '{filename}' using Azure Form Recognizer")
        form_recognizer_client = DocumentAnalysisClient(
            endpoint=f"https://{args.formrecognizerservice}.cognitiveservices.azure.com/",
            credential=formrecognizer_creds, headers={"x-ms-useragent": "azure-search-chat-demo/1.0.0"})
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
        index = SearchIndex(
            name=args.index,
            fields=[
                SimpleField(name="id", type="Edm.String", key=True),
                SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
                SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True, vector_search_dimensions=args.openAIDimensions, vector_search_configuration="default"),
                SimpleField(name="category", type="Edm.String", filterable=True, facetable=True),
                SimpleField(name="sourcepage", type="Edm.String", filterable=True, facetable=True),
                SimpleField(name="sourcefile", type="Edm.String", filterable=True, facetable=True)
            ],
            vector_search=VectorSearch(
                algorithm_configurations=[
                    VectorSearchAlgorithmConfiguration(
                        name="default",
                        kind="hnsw",
                        hnsw_parameters=HnswParameters(
                            m=4,
                            ef_construction=400,
                            ef_search=1000,
                            metric="cosine"
                        )
                    )
                ]
            ),
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='default',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='content')]))])
        ) if not skipvectorization else SearchIndex(
            name=args.index,
            fields=[
                SimpleField(name="id", type="Edm.String", key=True),
                SearchableField(name="content", type="Edm.String", analyzer_name="en.microsoft"),
                SimpleField(name="category", type="Edm.String", filterable=True, facetable=True),
                SimpleField(name="sourcepage", type="Edm.String", filterable=True, facetable=True),
                SimpleField(name="sourcefile", type="Edm.String", filterable=True, facetable=True)
            ],
            semantic_settings=SemanticSettings(
                configurations=[SemanticConfiguration(
                    name='default',
                    prioritized_fields=PrioritizedFields(
                        title_field=None, prioritized_content_fields=[SemanticField(field_name='content')]))])
        )
        if args.verbose: print(f"Creating {args.index} search index")
        index_client.create_index(index)
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
