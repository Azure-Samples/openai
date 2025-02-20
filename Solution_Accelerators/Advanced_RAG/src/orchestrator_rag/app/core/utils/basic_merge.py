from typing import List
from itertools import zip_longest

from common.contracts.skills.search.api_models import SearchRagResult, SearchResponse


def basic_merge(search_response: SearchResponse) -> List[SearchRagResult]:
    """
    This function is used to merge the search results obtained from the search skill.
    All the search results are merged into a single list, in a round-robin fashion
    and ordered by search_score in descending order.
    Duplicates are removed based on chunkid.
    """
    deduped_chunks = []
    seen_chunks = set()
    search_results_list = [result.search_results for result in search_response.results]
    for results in zip_longest(*search_results_list, fillvalue=None):
        for chunk in results:
            if chunk is None:
                continue

            if chunk.id not in seen_chunks:
                chunk.search_score = getattr(chunk, "search_score", 0)
                seen_chunks.add(chunk.id)
                deduped_chunks.append(chunk)

    if all(hasattr(x, "search_score") for x in deduped_chunks):
        deduped_chunks.sort(key=lambda x: x.search_score, reverse=True)

    return deduped_chunks
