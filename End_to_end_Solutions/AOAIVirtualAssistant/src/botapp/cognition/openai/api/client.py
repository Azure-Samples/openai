import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from cognition.openai.api.completions.response import OpenAICompletionsResponse, OpenAICompletionsResponseChoice
from cognition.openai.api.completions.request_params import OpenAICompletionsParams

"""
Client class to make requests to Open AI model endpoints.
"""
class OpenAIClient:
	def __init__(self, model_settings: dict):

		self.resource_name = model_settings["resource-name"]
		self.deployment_id = model_settings["deployment-name"]
		self.api_version = model_settings["api-version"]
		self.api_key = model_settings["api-key"]

	@retry(reraise=True, stop = stop_after_attempt(6), wait = wait_exponential(multiplier = 1, max = 60))
	def completions(self, prompt: str, params: OpenAICompletionsParams) -> OpenAICompletionsResponseChoice:
		"""
		Makes a POST request to the OpenAI completions endpoint given the request params and 
		returns the completion result. If the request fails, it will retry up to 6 times with exponential backoff to handle rate limit errors.
		"""
	
		base_url = f"https://{self.resource_name}.openai.azure.com"
		path = f"/openai/deployments/{self.deployment_id}/completions?api-version={self.api_version}"
		headers = {'api-key': self.api_key}
		payload = vars(params)
		payload["prompt"] = prompt
		try:
			response = requests.post(url = base_url + path, headers = headers, json = payload)
			response.raise_for_status()
			first_choice = OpenAICompletionsResponse.as_payload(response.text).get_first_choice()
			# Work around for this bug https://community.openai.com/t/error-gpt3-responding-with-finish-reason-none/77116
			if first_choice.finish_reason == None:
				raise Exception("Invalid response: Open AI Completions endpoint returned a finish_reason value of 'None'.")
			return first_choice
		except requests.RequestException as re:
			print(re)
			raise Exception("Error making request to Open AI completions endpoint.")
