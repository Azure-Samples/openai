
## Get duration breakdown for RAG based bot:

```
let conv_dialogs = 
traces
| extend conversation_id = tostring(customDimensions.conversation_id)
| extend dialog_id = tostring(customDimensions.dialog_id)
| where * contains "demo:" // add additional filters here
| where tostring(customDimensions.dialog_id) !in ("")
| project conversation_id, dialog_id
| distinct conversation_id, dialog_id
;

conv_dialogs
| join kind=leftouter (
    traces
    | where * contains "StaticOrchestrator run completed"
    | extend conversation_id = tostring(customDimensions.conversation_id)
    | extend dialog_id = tostring(customDimensions.dialog_id)
    | extend rephrase_duration = round(toreal(customDimensions.search_request_generation_duration_ms)/1000,2)
    | extend search_duration = round(toreal(customDimensions.search_duration_ms)/1000,2)
    | extend final_answer_duration = round(toreal(customDimensions.final_answer_duration_ms)/1000,2)
) on $left.conversation_id == $right.conversation_id and $left.dialog_id == $right.dialog_id
| join kind=leftouter(
    traces
    | where * contains "Finished orchestrator run"
    | extend conversation_id = tostring(customDimensions.conversation_id)
    | extend dialog_id = tostring(customDimensions.dialog_id)
    | extend session_duration = round(toreal(customDimensions.duration_ms)/1000,2)
)on $left.conversation_id == $right.conversation_id and $left.dialog_id == $right.dialog_id
| project conversation_id, dialog_id, session_duration, rephrase_duration, search_duration, final_answer_duration
| order by conversation_id, dialog_id

```