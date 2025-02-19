from typing import List


def are_equal_string_lists(list_a: List[str], list_b: List[str]):
    ''' Compares content of string is equivalent even if is in different order

    Returns:
        tuple: A tuple containing the following elements:
            - equal (bool)
            - array diff (List[str])
    '''
    list_a_set = set(list_a)
    list_b_set = set(list_b)

    list_diff = list_a_set - list_b_set
    return len(list_diff) == 0, list_diff
