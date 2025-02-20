import os


def get_env_var(env_var_name: str, default_value=None):
    env_value = os.environ.get(env_var_name) or default_value
    if env_var_name is None:
        raise EnvironmentError(
            f"Env variable '{env_var_name}' not set. Set the variable in the configuration and relaunch the server")

    return env_value
