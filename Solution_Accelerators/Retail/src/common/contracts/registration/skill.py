import uuid

class Skill:
    def __init__(self, name, description, endpoint, security_group, openai_plugin_definition, guid=None):
        self.name = name
        self.description = description
        self.endpoint = endpoint
        self.security_group = security_group
        self.openai_plugin_definition = openai_plugin_definition
        self.guid = guid if guid else str(uuid.uuid4())

    def to_dict(self):
        """
        Convert the Skill object to a dictionary representation.
        Useful for storing in Redis.
        """
        return {
            "guid": self.guid,
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "security_group": self.security_group,
            "openai_plugin_definition": self.openai_plugin_definition
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a Skill object from a dictionary representation.
        Useful for reading from Redis.
        """
        return cls(
            data["name"],
            data["description"],
            data["endpoint"],
            data["security_group"],
            data["openai_plugin_definition"],
            data["guid"]
        )
