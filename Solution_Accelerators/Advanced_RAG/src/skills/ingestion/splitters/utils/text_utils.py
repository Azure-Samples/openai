import os
import re
from typing import Optional

import markdown
from bs4 import BeautifulSoup

def get_file_name_with_page(filename: str, page: int):
    return f'{os.path.splitext(os.path.basename(filename))[0]}-{page}.pdf'

def get_base_file_name(filename: str, include_extension: bool = False):
    '''
    Generates base file name from the fully qualified file name.
    For e.g. data/filename1.pdf will be returned as 'filename1.pdf'
    if include_ext is True, 'filename1' otherwise.
    '''
    if include_extension:
        return os.path.basename(filename)

    return os.path.splitext(os.path.basename(filename))[0]

def get_chunks_within_max_length(large_text_chuck: str, max_length: int):
    '''
    Generates chunk of text within the specified max_length up until the last
    end of a sentence. Results are yielded to the caller.
    '''
    start = 0
    end = 0

    while start + max_length  < len(large_text_chuck) and end != -1:
        end = max(large_text_chuck.rfind(i, start, start + max_length + 1) for i in (". ", "\n"))
        yield large_text_chuck[start:end]
        start = end + 1
    yield large_text_chuck[start:]


def clean_up_text(markdown_str: str, include_image_descriptions: bool = False) -> Optional[str]:
    '''
    Remove all Markdown elements from input and returns a human-readable text.
    '''
    if not markdown_str:
        return None

    html = markdown.markdown(markdown_str)
    soup = BeautifulSoup(html, features='html.parser')

    clean_text = ""
    if include_image_descriptions:
        all_text = soup.findAll(string=True)

        for text in all_text:
            # If there is image description in the page,
            # extract and add it to the text in the order in which
            # it was parsed.
            if 'FigureContent' in text:
                pattern = r'FigureContent="([^\"]*)"'
                match = re.search(pattern, text)
                if match:
                    clean_text += f'{match.group(1)}\n'
            else:
                clean_text += f'{text}\n'
    else:
        clean_text = soup.get_text()

    return clean_text