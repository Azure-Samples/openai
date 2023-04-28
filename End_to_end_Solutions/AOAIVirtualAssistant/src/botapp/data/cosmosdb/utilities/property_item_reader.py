from typing import Any, Callable, List, Optional

def read_item_property_with_type(item: dict, property_name: str, expected_value_type: Any, object: Any, converter: Optional[Callable] = None, nullable: bool = False) -> Any:
    property = _get_property_from_item(item, property_name, object)
    if converter is not None:
        property = converter(property)
    if nullable == False and not isinstance(property, expected_value_type):
        raise Exception("Invalid type " + type(item[property_name]).__name__ + " for property " + property_name + " needed for object of type " + object.__name__ + ". Property must be of type " + expected_value_type.__name__ + ".")
    return property

def read_item_property_with_enum(item: dict, property_name: str, valid_enum_vals: List[str], enumConverter, object: Any) -> Any:
    property = _get_property_from_item(item, property_name, object)
    if not property in valid_enum_vals:
        raise Exception("Invalid value " + item[property_name] + " for property " + property_name + " needed for object of type " + object.__name__ + ". Value must be one of the following " + str(valid_enum_vals) + ".")
    return enumConverter(property)

def _get_property_from_item(item: dict, property: str, object: Any):
    if not property in item:
        raise Exception("Missing " + property + " property needed for object of type " + object.__name__ + ".")
    return item[property]