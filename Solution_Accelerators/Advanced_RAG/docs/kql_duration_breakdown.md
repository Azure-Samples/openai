
## Get duration breakdown for RAG based bot:

```
let conv_dialogs = 
traces
| extend conversation_id = tostring(customDimensions.conversation_id)
| extend dialog_id = tostring(customDimensions.dialog_id)
| where * contains "22_Sep"
| where tostring(customDimensions.dialog_id) !in ("")
| distinct conversation_id, dialog_id
| project conversation_id, dialog_id
| order by conversation_id, dialog_id
;

conv_dialogs
| join kind=leftouter (
    traces
    | where * contains "StaticOrchestrator run completed"
    | extend conversation_id_ = tostring(customDimensions.conversation_id)
    | extend dialog_id_ = tostring(customDimensions.dialog_id)
    | extend rephrase_duration = toreal(customDimensions.search_request_generation_duration_ms)/1000
    | extend search_duration = toreal(customDimensions.search_duration_ms)/1000
    | extend final_answer_duration = toreal(customDimensions.final_answer_duration_ms)/1000
) on $left.conversation_id == $right.conversation_id_ and $left.dialog_id == $right.dialog_id_
| project conversation_id, dialog_id, rephrase_duration, search_duration, final_answer_duration
```

## Duration Breakdown query for Retail demo
```
// using timestamp > ago(8h) to only consider logs from last 8 hours which could also be changed to use any conversaiton id

let filteredTrace = traces 
| where timestamp > ago(8h);

let sm = 
(
    filteredTrace
    | where message has "Finished chat request"
    | extend timestamp = datetime_utc_to_local(timestamp, 'US/Pacific')
    | extend conversation_id = tostring(customDimensions.conversation_id)
    | extend dialog_id = tostring(customDimensions.dialog_id)
    | extend dialog_sec = round(toreal(customDimensions.duration_ms) / 1000, 2)
    | extend sm_conversation_id = conversation_id
    | extend sm_dialog_id = dialog_id
);


let orchestrator =
(
    filteredTrace
    | where * has "StaticOrchestrator run completed"
    | extend timestamp = datetime_utc_to_local(timestamp, 'US/Pacific')
    | extend conversation_id = tostring(customDimensions.conversation_id)
    | extend dialog_id = tostring(customDimensions.dialog_id)
    | extend img_describer_sec = round(toreal(customDimensions.describe_and_replace_images_duration_ms) / 1000, 2)
    | extend classification_sec = round(toreal(customDimensions.classification_duration_ms) / 1000, 2)
    | extend recommender_sec = round(toreal(customDimensions.recommender_duration_ms) / 1000, 2)
    | extend search_sec = round(toreal(customDimensions.search_duration_ms) / 1000, 2)
    | extend final_answer_sec = round(toreal(customDimensions.final_answer_duration_ms) / 1000, 2)
    | extend orc_conversation_id = conversation_id
    | extend orc_dialog_id = dialog_id
);


sm
| join kind=fullouter orchestrator on conversation_id, dialog_id
| project timestamp,
            conversation_id = coalesce(sm_conversation_id, orc_conversation_id), 
          dialog_id = coalesce(sm_dialog_id, orc_dialog_id), 
          dialog_sec, img_describer_sec, classification_sec, recommender_sec, search_sec
// | where  img_describer_sec > 1.0
| order by timestamp asc
        //, conversation_id, dialog_id
// | summarize percentile(dialog_sec, 50), percentile(dialog_sec, 75), percentile(dialog_sec, 95),
//             percentile(img_describer_sec, 50), percentile(img_describer_sec, 75), percentile(img_describer_sec, 95),
//             percentile(classification_sec, 50), percentile(classification_sec, 75), percentile(classification_sec, 95),
//             percentile(recommender_sec, 50), percentile(recommender_sec, 75), percentile(recommender_sec, 95),
//             percentile(search_sec, 50), percentile(search_sec, 75), percentile(search_sec, 95)
```

## Below query was used with V1 Design where plans and skills payload where generated on the fly
```
let filteredTrace = traces | where timestamp > ago(30m);

let step =
(
    filteredTrace
    | where message has "Step execution completed."
    | extend conversation_id = tostring(customDimensions.conversation_id)
    | extend dialog_id = tostring(customDimensions.dialog_id)
    | extend step_name = tostring(customDimensions.step_name)
    | extend step_aoai_call_ms = toreal(customDimensions.step_aoai_call_duration_ms)
    | extend step_execution_ms = toreal(customDimensions.step_execution_duration_ms)
    | summarize step_aoai_sec = sum(step_aoai_call_ms)/1000, step_exec_sec = sum(step_execution_ms)/1000 by conversation_id, dialog_id, step_name
);

let aoai = ( 
    filteredTrace
    | where message has "AOAI Call"
    | extend conversation_id = tostring(customDimensions.conversation_id)
    | extend dialog_id = tostring(customDimensions.dialog_id)
    | extend step_name = iif(tostring(customDimensions.aoai_response) contains '"relative_path": "/imageSearch"', "cognitiveSearchSkill", iif(tostring(customDimensions.aoai_response) contains '"relative_path": "/recommend"', "recommender", iif(tostring(customDimensions.aoai_response) contains '"relative_path": "/analyze"', "imagedescriber", "Planner")))
    | extend prompt_token_count = toreal(customDimensions.prompt_token_count)
    | extend total_token_count = toreal(customDimensions.total_token_count)
    | extend completion_token_count = toreal(customDimensions.completion_token_count)
    | extend model = tostring(parse_json(tostring(customDimensions.aoai_model_parameters)).model)
    | summarize prompt_token = sum(prompt_token_count), total_token = sum(total_token_count), completion_token = sum(completion_token_count) by conversation_id, dialog_id, step_name, model
);


let step_details = (
aoai
| join kind = leftouter step on conversation_id, dialog_id, step_name
| project conversation_id, dialog_id, step_name, step_aoai_sec, step_exec_sec, model, prompt_token, completion_token, total_token
);

let dialog = 
(
    filteredTrace
    | where message has "Finished chat request"
    | extend conversation_id = tostring(customDimensions.conversation_id)
    | extend dialog_id = tostring(customDimensions.dialog_id)
    | extend dialog_ms = toreal(customDimensions.duration_ms)
    | summarize dialog_sec = sum(dialog_ms)/1000 by conversation_id, dialog_id
);

let orchestrator =
(
    filteredTrace
    | where message has "LinearOrchestrator run completed"
    | extend conversation_id = tostring(customDimensions.conversation_id)
    | extend dialog_id = tostring(customDimensions.dialog_id)
    | extend plan = tostring(customDimensions.plan)
    | extend plan_generation_ms = toreal(customDimensions.plan_generation_duration_ms)
    | extend plan_execution_ms = toreal(customDimensions.plan_execution_duration_ms)
    | summarize plan_gen_sec = sum(plan_generation_ms)/1000, plan_exec_sec = sum(plan_execution_ms)/1000 by conversation_id, dialog_id, plan
);


let plan = 
(
    filteredTrace
    | where message has "Plan execution completed"
    | extend conversation_id = tostring(customDimensions.conversation_id)
    | extend dialog_id = tostring(customDimensions.dialog_id)
    | extend search_step_ms = toreal(customDimensions.cognitiveSearchSkill_duration_ms)
    | extend recommender_step_ms = toreal(customDimensions.recommender_duration_ms)
    | extend imagedescriber_step_ms = toreal(customDimensions.imagedescriber_duration_ms)
    | summarize search_sec = sum(search_step_ms)/1000, recommender_sec = sum(recommender_step_ms)/1000, imagedescriber_sec = sum(imagedescriber_step_ms)/1000 by conversation_id, dialog_id
);


dialog
| join kind=inner orchestrator on conversation_id, dialog_id
| join kind=inner plan on conversation_id, dialog_id
| join kind=inner step_details on conversation_id, dialog_id
| project conversation_id, dialog_id, dialog_sec, plan, plan_gen_sec, plan_exec_sec, imagedescriber_sec, recommender_sec, search_sec, step_name, step_aoai_sec, step_exec_sec, model, prompt_token, completion_token, total_token
| order by conversation_id, dialog_id
```