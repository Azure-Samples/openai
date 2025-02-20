def generate_system_prompt(config, arguments):
    system_prompt = config["system_prompt"]
    for argument_name in config["system_prompt_arguments"]:
        system_prompt = system_prompt.replace(
            "{" + argument_name + "}", arguments[argument_name])

    return system_prompt