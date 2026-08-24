# Use case: AI Powered multi-language Virtual assistant
# AI Powered multi-language Virtual assistant Accelerator uses Azure Speech and Azure OpenAI services to that could be used in real-time virtual assistant. 

# install Speech SDK in console
# pip install azure-cognitiveservices-speech
# pip install python-dotenv on Windows or dotenv in Linux/MacOS
# pip install python-dotenv
# pip install azure.cognitiveservices

import os
import azure.cognitiveservices.speech as speechsdk
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# This example requires environment variables named "OPEN_AI_KEY" and "OPEN_AI_ENDPOINT"
# Your endpoint should look like the following https://YOUR_OPEN_AI_RESOURCE_NAME.openai.azure.com/
openai.api_key = os.environ.get('OPEN_AI_KEY')
openai.api_base =  os.environ.get('OPEN_AI_ENDPOINT')
openai.api_type = 'azure'
openai.api_version = '2022-12-01'

# This will correspond to the custom name you chose for your deployment when you deployed a model.
deployment_id='mytext-davinci-003' 

# This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
audio_output_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

# Should be the locale for the speaker's language. English: en-US, Chinese: zh-CN, India Hindi: hi-IN
# Language list: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=stt
speech_config.speech_recognition_language="en-US"
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# The language of the voice that responds on behalf of Azure OpenAI. English: en-US-JennyMultilingualNeural, Chinese: zh-CN-XiaoxiaoNeural, India Hindi: hi-IN-SwaraNeural
speech_config.speech_synthesis_voice_name="en-US-JennyMultilingualNeural"
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output_config)

# Prompts Azure OpenAI with a request and synthesizes the response.
def ask_openai(prompt):

    # Ask Azure OpenAI
    response = openai.Completion.create(engine=deployment_id, prompt=prompt, max_tokens=100)
    text = response['choices'][0]['text'].replace('\n', ' ').replace(' .', '.').strip()
    print('Azure OpenAI response:' + text)

    # Azure text to speech output
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    # Check result
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized to speaker for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

# Continuously listens for speech input to recognize and send as text to Azure OpenAI
def chat_with_open_ai():
    while True:
        print("Azure OpenAI is listening. Say 'Stop' or press Ctrl-Z to end the conversation.")
        try:
            # Get audio from the microphone and then send it to the TTS service.
            speech_recognition_result = speech_recognizer.recognize_once_async().get()

            # If speech is recognized, send it to Azure OpenAI and listen for the response.
            if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
                if speech_recognition_result.text == "Stop.": 
                    print("Conversation ended.")
                    break
                print("Recognized speech: {}".format(speech_recognition_result.text))
                ask_openai(speech_recognition_result.text)
            elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
                print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
                break
            elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = speech_recognition_result.cancellation_details
                print("Speech Recognition canceled: {}".format(cancellation_details.reason))
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print("Error details: {}".format(cancellation_details.error_details))
        except EOFError:
            break

# Main

try:
    chat_with_open_ai()
except Exception as err:
    print("Encountered exception. {}".format(err))