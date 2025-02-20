# RECOMMENDER SERVICE

The Recommender Service transforms user-provided context like product images, query etc. into natural language search queries that the system uses to retrieve relevant products.

## KEY FEATURES
- Context-Aware Recommendations: Leverages both textual and visual input (e.g., descriptions of uploaded images) to provide tailored suggestions.
- Descriptive Search Queries: Converts user input into natural language queries that highlight essential product qualities like color, style, material, and occasion.
- Database-Agnostic: Works without prior knowledge of the database or its inventory, ensuring unbiased recommendations. 
- The prompt for the Recommender Skill can be found [here](src/skills/recommender/src/prompts_config.yaml). It can be customized to include additional context, such as specific categories within the catalog or other relevant details, to ground the generated recommendations.

## GROUNDING YOUR RECOMMENDATIONS
All prompt-related configuration, including Azure Conginitive Service configuration like deployment name, system prompt etc. can be found in [prompt_config.yaml](src/prompts_config.yaml). To make any changes to the recommender prompt, update this file.

Additionally, to dynamically ground recommendations with the product catalog, consider exposing an endpoint from the search service to provide catalog-related context, such as product categories etc. This context can then be used to update the recommendation service prompt, enabling recommendation grounding.

## EXAMPLE INPUT & OUTPUT

### INPUT

```
{
    "descriptions": [
        "A sleek, dark navy blue suit with a subtle texture, paired with a crisp white dress shirt and a matching navy blue tie."
    ],
    "recommendation_query": "I am looking for pants that will complement this suit"
}
```

### OUTPUT

```
{
  "result": {
    "user_id": null,
    "conversation_id": null,
    "dialog_id": null,
    "recommendations": [
      "A pair of formal, tailored black trousers with a slim fit, featuring a smooth wool blend fabric and a flat front design",
      "A pair of charcoal grey dress pants with a straight leg cut, crafted from a lightweight, wrinkle-resistant material and featuring a classic waistband with belt loops"
    ]
  }
}
```
