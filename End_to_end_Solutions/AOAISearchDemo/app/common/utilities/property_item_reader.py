from typing import Any, Callable, List, Optional

class MissingPropertyError(BaseException):
    pass

class NullValueError(BaseException):
    pass

def read_item_property_with_type(item: dict, property_name: str, expected_value_type: type, object: Any = None, converter: Optional[Callable] = None, nullable: bool = False, optional: bool = False) -> Any:
    is_present, property = _try_get_property_from_item(item, property_name, object, optional)
    if is_present == False and optional == True:
        return None
    obj_str = f" needed for object of type {object.__name__}" if object is not None else ""
    if converter is not None:
        property = converter(property)
    if nullable == False and property is None:
        raise NullValueError(f"Invalid null value set for {property_name}.")
    if not isinstance(property, expected_value_type) and not property is None:
        raise TypeError(f"Invalid type {type(property).__name__} for property {property_name}{obj_str}. Property must be of type {expected_value_type.__name__}.")
    return property

def read_item_property_with_enum(item: dict, property_name: str, valid_enum_vals: List[str], enumConverter: Callable, object: Any = None, optional: bool = False) -> Any:
    is_present, property = _try_get_property_from_item(item, property_name, object, optional)
    if is_present == False and optional == True:
        return None
    obj_str = f" needed for object of type {object.__name__}" if object is not None else ""
    if not property in valid_enum_vals:
        raise TypeError(f"Invalid value {property} for property {property_name}{obj_str}. Value must be one of the following {str(valid_enum_vals)}.")
    return enumConverter(property)

def _try_get_property_from_item(item: dict, property: str, object: Any = None, optional: bool = False):
    obj_str = f" needed for object of type {object.__name__}" if object is not None else ""
    if not property in item and optional == False:
        raise MissingPropertyError(f"Missing {property} property{obj_str}.")
    elif not property in item and optional == True:
        return False, None
    return True, item[property]