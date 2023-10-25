# Making LLM work with abbreviations 
<p align="center">  
<img src="https://github.com/azurepocmain/aoai/assets/91505344/e386c8cf-e0fb-414d-a65b-dc90b8d3f06a" width="500" height="300"></p>


This repo aims to provide an approach for grounding abbreviations so that the LLM fully understands the context of the question. For smaller internal organization abbreviations, adding instructions in the prompt can resolve this anomaly. However, for larger data corpus, we will need to leverage a vector store to perform a cosine similarity search.  Both approaches leverage the chat completion functions to split the users questions into required text classifications we outlined and the results provided to us as arguments. We are then either provided the raw data or enriched data depending on the initial instructions. For larger corpus of data where abbreviations won’t fit in the instructions. We will pass the arguments into a method which will embed the specific argument, provide a high-ranking cosine results. Finally, pass the question with the results to the LLM to fully ground the LLM on the organizations data corpus. 
_______________________________________________________________________________________
While this is a complex topic, this repo takes a very unique approach of solving this issue, by leveraging Azure Open AI function argument. Tokenizing and embedding an organization data and storing the coordinates in a  vector database, and perform a cosine similarity search. This allows us to break down a user’s question to tokens, select the required tokens, then process that token against a vector index. 
_______________________________________________________________________________________
You may be tempted to use an VM open source vector database, however, I would caution you against such an action. While working with a number of clients, they were unable to experience satisfactory results. We ultimately ended up going with an enterprise level vector store as Azure Cosmos DB Mongo DB Vcore or Azure Cognitive Search. 
_______________________________________________________________________________________
For example, we have an organization that predominantly uses abbreviations when describing company departments. A new employee while in a meeting is attempting to leverage the new Azure Open AI document discovery tool that leverages LLM to perform full text search on the corpus of data. The employee is able to ask nearly any question and decides to confirm what department correlates to RD abbreviation and the latest projects they have been working on as the projects seem very important for the company’s bottom line. While asking the question, because the language model is unable to correlate RD, it hallucinates and provides inaccurate responses. However, providing proper instructions and leveraging Open AI functions, when dealing with a small corpus of data. We are able to ground the language model with the organization corpus of data before sending the full question to Cognitive search or Azure Cosmos DB Mongo API for the full text data to return. 

Before: No enrichment and high probability of hallucination:

![image](https://github.com/azurepocmain/aoai/assets/91505344/2eb164c3-a376-47e9-be4d-b31282dcfae3)

After with the function enrichment:

![image](https://github.com/azurepocmain/aoai/assets/91505344/2902c9dd-f9d2-4e99-97b8-ad7e389f214c)



**Function Code:** 
<pre>
  
import os
import openai
import json
from dotenv import load_dotenv
load_dotenv()

openai.api_type  = os.getenv("API_TYPE")
openai.api_version = os.getenv("API_VERSION_FUNCTION_CALL")
openai.api_key = os.getenv("API_KEY")
openai.api_base = os.getenv("API_BASE")
ENGINE_API= os.getenv("ENGINE")
max_tokens=2000
temperature=0.0
top_p=0
frequency_penalty=0.0
presence_penalty=0.0
stop=None
from aoai1_poc_github  import _company_corpus_search


def _aoai_company_function_token(prompt):
    
    messages = [
        {"role": "system", "content": """You're an AI assistant designed to help users search internal data corpus.
         You must handle a variety of company name abbreviations.
        """},
        {"role": "system", "name":"example_user", "content": "What are the latest RD documents?"},
        {"role": "system", "name": "example_assistant", "content": "arguments: {\n  \"abbreviations\": \"Research and Development\"\n}"},
        {"role": "system", "name":"example_user", "content": "What are the latest EGA documents?"},
        {"role": "system", "name": "example_assistant", "content": "arguments: {\n  \"abbreviations\": \"Executive General and Administration\"\n}"},
        {"role": "user", "content": prompt}]
    functions = [
         {
            "name": "_company_corpus_search",
            "description": "Gets business's document information",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_type": {"type": "string", "description": "Type of document."},
                    "abbreviations": {
                        "type": "string", 
                        "description": "Gets the abbrivation for the company entity return the full name from the followig list:SM=Sales and Marketing, IM=Inventory Management, M=Manufacturing, EGA=Executive General and Administration, AZ=Quality Assurance "},
                },
                "required": [],
            }
        },
         
        
    ]
    openai.api_type  = os.getenv("API_TYPE")
    openai.api_version = os.getenv("API_VERSION_FUNCTION_CALL")
    openai.api_key = os.getenv("API_KEY")
    openai.api_base = os.getenv("API_BASE")
    response = openai.ChatCompletion.create(
         engine=ENGINE_API,
        messages=messages,
        functions=functions,
        function_call="auto",  #auto is default, but we'll be explicit
    )
    response_message = response["choices"][0]["message"]
    print(response_message)
  
    #convert OpenAIObject to a JSON-formatted string
    json_str = str(response_message)  
  
    #load JSON string into a dictionary
    json_dict = json.loads(json_str)   
    
    #get the function name and arguments from the JSON dictionary
    func_name = json_dict['function_call']['name']  
    func_args_str = json.loads(json_dict['function_call']['arguments'])
    print(func_name)
    
    # convert function arguments string to a dictionary
    #func_args = json.loads(func_args_str)  
    API_KEY = os.getenv("NEWOPENAI_KEY") 
    RESOURCE_ENDPOINT = os.getenv("NEWRESOURCE_ENDPOINT") 
    openai.api_type = "azure"
    openai.api_key = API_KEY
    openai.api_base = RESOURCE_ENDPOINT
    openai.api_version = "2023-03-15-preview"
    #determine which function to call based on the function name
    
    # Parse the arguments JSON string  
    document_type = func_args_str.get('document_type')
    abbreviations = func_args_str.get('abbreviations')
    print(abbreviations)
    
    if func_name == '_company_corpus_search':  
        result = _company_corpus_search(prompt=prompt, document_type=document_type, abbreviations=abbreviations)  
    else:  
        result = 'There was an issue selecting the function'  
        return result  


 
</pre>


_________________________________________________________________
Using this method, we are able to break down user questions via classification tokens and then pass those adjectives, nouns, abbreviations, etc., to the respective function for processing and enrichment. 
This also provides a way to leverage multiple functions depending on the users question. For example, we can call a function that stores data in cognitive search, Azure SQL or even external APIs. Then have it all processed and summarized by the language model. 
_________________________________________________________________

Finally, when we integrate the vector database, in this case Azure Cosmos DB, with the function, with no detailed instructions. We are able to see the full power of the vector engine below. This plays an integral role when organizations have a large corpus of data that cannot easily fit into the instructions and need to be embedded. 

![image](https://github.com/azurepocmain/aoai/assets/91505344/ceb69542-6bed-4501-94f8-cb1ddbad81b6)

We would then pass the Full Abbreviation results to the language model or rewrite the question before performing the full LLM request. This will essentially ground the model and provide appropriate context of the users question. 
<p></p>


**For more information or even to have this conecpt demoed live. Please feel free to conact your local CSA (Cloud Solution Architect)**
For the full instructions and code stack, please see the above repo folders. 




*Created by: Victor Adeyanju CSA*
