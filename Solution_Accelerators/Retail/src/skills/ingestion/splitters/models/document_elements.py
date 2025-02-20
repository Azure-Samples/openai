from typing import List
from azure.ai.documentintelligence.models import DocumentTable
from shapely import geometry

class Section:
    heading: str = ""
    content: str = ""
    page_number: int

class IndexDocument:
    title: str
    sections: List[Section] = []

class Document:
    title: str
    sections: List[Section] = []

class TableBoundingRegion:
    table: DocumentTable
    polygon: geometry.Polygon
    page_number: int