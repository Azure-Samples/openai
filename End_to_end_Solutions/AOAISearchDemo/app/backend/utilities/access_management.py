from backend.contracts.chat_response import ApproachType


class AccessManager:
    def __init__(self) -> None:
        pass

    def get_allowed_approaches(self, allowed_resources):
        allowed_approaches = []
        for resource in allowed_resources:
            allowed_approaches.append(self.map_resource_to_approach(resource.resource_type.value))
        return allowed_approaches
    
    def is_user_allowed(self, allowed_approaches, approach_type: ApproachType):
        return approach_type.value in allowed_approaches
    
    def map_approach_to_resource(self, approach: ApproachType):
        if approach == ApproachType.unstructured:
            return "COGNITIVE_SEARCH"
        elif approach == ApproachType.structured:
            return "SQL_DB"
        else:
            raise Exception(f"Unknown approach {approach}")
    
    def map_resource_to_approach(self, resource):
        if resource == "COGNITIVE_SEARCH":
            return ApproachType.unstructured.value
        elif resource == "SQL_DB":
            return ApproachType.structured.value
        else:
            raise Exception(f"Unknown resource {resource}")