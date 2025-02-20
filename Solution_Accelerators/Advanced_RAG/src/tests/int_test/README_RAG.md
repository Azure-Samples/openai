# Overview
This folder contains integration tests which are defined in the test_cases.yaml file. The purpose of these integration tests is to ensure all our services are running and producing valid responses on some basic scenarios. This is not meant to perform stress test or test for edge cases.

## Defining integration test
Currently tests are defined in the test_cases.yaml file. Each test case is a conversation with the bot, that could include multiple dialogs (follow up questions). 

A test case has a converation and optional communication protocol (http or websockets or both) to use to test. Each conversation has a Conversation_ID and collection of Dialogs.
A Dialog has Dialog_ID, message, overrides to use if any and assertion (what to validate for that request)

For Assertion, we can specifiy two types of assertions which are optional:
 - assertion on the reponse (ChatResponse) object and 
 - assertion on the result (ChatResponse.answer) object

For assertion on the result, we can do things like:
 - assert on the result count
 - assert that the ChatResponse answer field contains certain strings

Below is a an example of test case for a RAG scenario where the user is asking for revenue information.
The conversation has two dialogs. User starts with first one asking for revenue in year 2023. On this dialog we test for two things:
1. The response from the backend is a valid ChatResponse (by deserializing the response to ChatResponse object)
2. As part of status_code check, we are also ensure ChatResponse object's error field is empty (basically no errors occured)
3. Checking to ensure that the final answer shown to the user has citations included.

This is then followed by a follow up question where the user asks for revenue the year before. Again we assert for three things:
1. The response from the backend is a valid ChatResponse (by deserializing the response to ChatResponse object)
2. As part of status_code check, we are also ensure ChatResponse object's error field in empty (basically no errors occured)
3. Checking to ensure that the final answer shown to the user has citations included.

```
- test_case: "test for revenue"
  communication_protocol: "http"
  scenario: "rag"
  conversation:
    conversation_id: "IntegrationTest_Conv_2"
    user_id: 7b17fb37-c3d6-4df0-8a51-dc1d6aa0e267
    dialogs:
      - dialog_id: "1"
        message:
          payload:
            - type: "text"
              value: "What was International Holding Company PJSC's revenue in 2023?"
        overrides:
          search_overrides:
            top: 1
        assertion:
          response_assertion: "status_code == 200"
          check_presence_citation: True
      - dialog_id: "2"
        message:
          payload:
            - type: "text"
              value: "How about a year before that?"
        overrides:
          search_overrides:
            top: 1
        assertion:
          response_assertion: "status_code == 200"
          check_presence_citation: True
```