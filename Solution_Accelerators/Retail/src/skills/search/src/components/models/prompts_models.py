from pydantic import BaseModel


class FilteringCollectionPrompt(BaseModel):
    systemPrompt: str
    userPromptCollectionPrefix: str
    userPromptItemDescription: str


class GPTFilteringPrompts(BaseModel):
    '''
    Base model used for validating/using 'src/components/gpt_filtering/prompts.yml'
    '''
    postSearchFilterPrompts: FilteringCollectionPrompt
    categorySummaryPrompts: FilteringCollectionPrompt
