import logging
import json

def json_load_from_filename(filename):
    
    """Loads data from json file
    
    :param filename: The name of the file in json format
    :type filename: string
    :returns json data as python objects:
    """
    
    logging.info('Reading json from file: ' + filename)
    file = open(filename, encoding = 'utf-8')
    results = json.load(file)
    return(results)

def json_dump_to_filename(data, filename):
    
    """Writes python object to file in json format
    
    :param data: python object to write out
    :param filename: filename to write to
    :type data: serializable python object
    :type filename: string
    """
    
    logging.info('Writing json to file: ' + filename)
    file = open(filename, 'w', encoding = 'utf-8')
    results = json.dump(data, file, indent = 4, sort_keys = True)
    file.close()
    return