import json

def generate_history_messages(history, config):
    formatted_messages = []
    
    user_message_format = config["user_message_format"]
    assistant_message_format = config["assistant_message_format"]
    history_length = config["length"]

    for message in history[-(history_length*2):]:
        # load the message components from history
        message_values = message
        role = ""

        # This is dont since assistant messages can have multiple components like "sql_query", "sql_results" etc.
        # TODO: unify all messages to support multiple components natively
        if message["participant_type"] == "user":
            formatted_message = user_message_format
            role = "user"
        else:
            formatted_message = assistant_message_format
            message_values = json.loads(message["utterance"])
            role = "assistant"
        
        for key in message_values:
            if message_values[key] is not None:
                formatted_message = formatted_message.replace("{" + key + "}", message_values[key])
        
        formatted_messages.append({"role": role, "content": formatted_message})

    return formatted_messages

def generate_system_prompt(config, arguments):
    system_prompt = config["system_prompt"]
    for argument_name in config["system_prompt_arguments"]:
        system_prompt = system_prompt.replace("{" + argument_name + "}", arguments[argument_name])
    
    return system_prompt