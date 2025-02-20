from typing import List, Dict, Optional

from tabulate import tabulate
from shapely import geometry, Point
import numpy as np
import pandas as pd
from azure.ai.documentintelligence.models import (
    DocumentLine,
    DocumentTable
)
from splitters.models.document_elements import TableBoundingRegion

def prettify_document_table(table: DocumentTable) -> str:
    table_df = __convert_table_to_dataframe(table)
    return pretty_format_dataframe(table_df)

def get_intersecting_table_from_line(
        line: DocumentLine, 
        table_polygons: Dict[int, TableBoundingRegion], 
        current_page: int
    )-> Optional[TableBoundingRegion]:
    '''
    Returns intersecting DocumentTable with the line geometry. If there is no intersecting table, returns None.
    '''
    line_geometry = geometry.LineString(
        [(point.x, point.y) for point in get_coordinates_from_polygon(line.polygon)]
    ).buffer(0.01)

    for _, table_polygon in table_polygons.items():
        if table_polygon.page_number == current_page and table_polygon.polygon.buffer(0).intersection(line_geometry.buffer(0)):
            return table_polygon

    return None

def is_line_in_table(line: DocumentLine, table_polygon: TableBoundingRegion) -> bool:
    '''
    Checks whether the line geometry intersects with any of the tables within the Document.
    '''
    line_geometry = geometry.LineString(
        [(point.x, point.y) for point in get_coordinates_from_polygon(line.polygon)]
    ).buffer(0.01)

    return table_polygon.polygon.buffer(0).intersection(line_geometry.buffer(0))


def get_coordinates_from_polygon(polygon: List[float]) -> List[Point]:
    '''
    Generates four coordinates in the form of list of Points from a Polygon.
    '''
    coordinates: List[Point] = []
    while(polygon):
        x = polygon.pop(0); y = polygon.pop(0)
        point = Point(x, y)
        coordinates.append(point)
    return coordinates

def pretty_format_dataframe(df):
    return tabulate(df, headers=df.columns, tablefmt="jira")

def __convert_table_to_dataframe(table):
    '''
    Converts azure.ai.documentintelligence.models.DocumentTable into a DataFrame representation.
    '''
    # Create DataFrame representation with analyzed table.
    array = np.full((table.row_count, table.column_count), fill_value="")
    df = pd.DataFrame(array)

    # Hydrate DataFrame with individual cells in table.
    for cell in table.cells:
        df.iloc[cell.row_index, cell.column_index] = cell.content

    # Assign first row of the table as column names.
    df = df.rename(columns=df.iloc[0]).drop(df.index[0])
    return df