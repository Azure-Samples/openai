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

Below is a an example of test case for retail where the user is trying to get matching polos.
The conversation has two dialogs. User starts with first one and provides an image to match as well. On this dialog we test for three things:
1. The http response object has a status_code == 200
2. We have got more than one search result back
3. One of the search result's description has word "polo" in it

This is then followed by a follow up question where the user asks for a green one. Again we assert for three things:
1. We have got more than one search result back
2. One of the search result's description has word "polo" and "green" in it (at least one search result shown to the user is a green polo)

```
    - test_case: "search for polos and shoes to go along with khakis"
      conversation:
        conversation_id: "IntegrationTest_Conv_1"
        dialogs:
          - dialog_id: "1"
            request:
              user_prompt:
                payload:
                - type: "text"
                  value: "I am looking for polos to go along with my khakis."
                - type: "image"
                  value: "data/khakiPants.jpg"
              user_profile: {
                "id": "anonymous",
                "user_name": "anonymous"
              }
              overrides: {
                is_content_safety_enabled: "false"
              }
            assertion:
              response_assertion: "status_code == 200"
              result_assertion:
                result_count: "len(result_count) > 0"
                product_description_includes_keywords: ["polo"]
          - dialog_id: "2"
            request:
              user_prompt:
                payload:
                - type: "text"
                  value: "How about green one instead."
              user_profile: {
                "id": "anonymous",
                "user_name": "anonymous"
              }
              overrides: {
                is_content_safety_enabled: "false"
              }
            assertion:
              result_assertion:
                result_count: "len(result_count) > 0"
                product_description_includes_keywords: ["green", "polo"]
```