from enum import Enum

class Role(Enum):
    user = "user"
    assistant = "assistant"
    system = "system"

class ChatDialog:
    def __init__(self, role: Role, content: str):
        self.role = role
        self.content = content

    def to_dict(self):
        return {
            "role": self.role.value,
            "content": self.content
        }
    
    @staticmethod
    def as_dict(dct: dict):
        role = Role(dct.get("role"))
        content = dct.get("content")
        
        return ChatDialog(role, content)