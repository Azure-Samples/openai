import argparse


class Config:
    def __init__(self) -> None:
        self.parse_arguments()
    
    def parse_arguments(self):
        parser = argparse.ArgumentParser(
            description="Prepare documents by extracting content from PDFs, splitting content into sections, uploading to blob storage, and indexing in a search index.",
            epilog="Example: prepdocs.py '..\data\*' --storageaccount myaccount --container mycontainer --searchservice mysearch --index myindex -v")
    
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
                            help="Name of the Azure AI Search service where content should be indexed (must exist already)")
        parser.add_argument("--index",
                            help="Name of the Azure AI Search index where content should be indexed (will be created if it doesn't exist)")
        parser.add_argument("--searchkey", required=False,
                            help="Optional. Use this Azure AI Search account key instead of the current user identity to login (use az login to set current user for Azure)")
        parser.add_argument("--remove", action="store_true",
                            help="Remove references to this document from blob storage and the search index")
        parser.add_argument("--removeall", action="store_true",
                            help="Remove all blobs from blob storage and documents from the search index")
        parser.add_argument("--localpdfparser", action="store_true",
                            help="Use PyPdf local PDF parser (supports only digital PDFs) instead of Azure Form Recognizer service to extract text, tables and layout from the documents")
        parser.add_argument("--documentintelligenceservice", required=False,
                            help="Optional. Name of the Azure AI Document Intelligence service which will be used to extract text, tables and layout from the documents (must exist already)")
        parser.add_argument("--documentintelligencekey", required=False,
                            help="Optional. Use this Azure AI Document Intelligence key instead of the current user identity to login (use az login to set current user for Azure)")
        parser.add_argument("--skipvectorization", help="Skip vectorization of document content")
        parser.add_argument("--openAIService", required=False, help="Azure OpenAI service resource name")
        parser.add_argument("--openAIKey", required=False, help="OpenAI API key")
        parser.add_argument("--openAIEngine", required=False, help="OpenAI embeddings model engine name")
        parser.add_argument("--openAITokenLimit", required=False, help="The max token limit for requests to the specidied OpenAI embeddings model")
        parser.add_argument("--openAIDimensions", required=False,
                            help="The max number of dimensions allowed for an embeddings request to the specified OpenAI model")
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

        args = parser.parse_args()
        for arg in vars(args):
            setattr(self, arg, getattr(args, arg))
        
        # Method to set default values. Currently unused. 
        self.set_default_values()

    def set_default_values(self):
        if not hasattr(self, 'optional_arg_not_in_command_line'):
            self.optional_arg_not_in_command_line = 'default_value'


config = Config()