import re
from typing import Dict, Tuple
from copy import deepcopy

class AdaptiveCardConverter:
    def __init__(self, adaptive_card_template, session_manager_url):
        self.adaptive_card_template = adaptive_card_template
        self.session_manager_url = session_manager_url

    def generate_content_url(self, file_reference) -> str:
        content_url = self.session_manager_url + "/content/" + file_reference
        return content_url

    def extract_and_replace_citations(self, final_answer: str) -> Tuple[str, list]:
        citations = list()
        
        citation_pattern = r"\{[^\}]+\}"
        
        def replacer(match):
            file_reference = match.group(0)[1:-1]
            blob_url = self.generate_content_url(file_reference)
            citation_number = final_answer[:match.start()].count("{") + 1
            citations.append((citation_number, file_reference, blob_url))
            return f"[^{citation_number}](#{citation_number})"
        converted_text = re.sub(citation_pattern, replacer, final_answer)

        return converted_text, citations
    
    def generate_clickable_actions(self, citations: list) -> list:
        actions = list()
        for _, filename, blob_url in citations:
            actions.append({
                "type": "Action.OpenUrl",
                "title": f"{filename}",
                "url": blob_url
            })
        return actions

    def append_references(self, text_body: str, citations: list) -> str:
        references = "  ".join([f" <a name={citation_number}></a>{citation_number}.[{filename}]({blob_url})" for citation_number, filename, blob_url in citations])
        return text_body + "\n\n\n\n" + "Citations: " + references

    def to_adaptive_with_citations(self, response: Dict):
        final_answer = response.get("answer", {}).get("final_answer", "")
        adaptive_card = deepcopy(self.adaptive_card_template)
        
        converted_text, citations = self.extract_and_replace_citations(final_answer)
        text_body = self.append_references(converted_text, citations)
        adaptive_card["body"][0]["text"] = text_body

        # actions = self.generate_clickable_actions(citations)
        # adaptive_card["actions"] = actions

        return adaptive_card






