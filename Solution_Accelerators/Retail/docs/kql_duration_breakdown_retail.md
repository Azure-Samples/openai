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