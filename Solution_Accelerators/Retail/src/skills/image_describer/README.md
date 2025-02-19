# IMAGE DESCRIBER SKILL

The Image Describer Skill generates detailed, one-sentence descriptions of user provided product images. This skill focuses on capturing all important and distinguishing features of the item in a clear and concise manner. The Image Describer skill leverages [Azure AI Service](https://azure.microsoft.com/en-us/products/ai-services/) to utilize OpenAI models for its functionality.

## KEY FEATURES
- Comprehensive Descriptions: Highlights critical attributes such as color, texture, materials, functionality, patterns, and unique details of the user provided image(s).
- Strictly Observational: Describes only what is visible in the image without including suggestions, recommendations, or inferred details.
- One-Sentence Output: Ensures each description is succinct yet thorough.

### EXAMPLE INPUT & OUTPUT

### INPUT

<img src="../../../data/retail/product_images/business_jacket1.png" alt="Description" width="300" height="300">

### OUTPUT

```
{
  "results": [
    {
      "image": "business_jacket1.png",
      "analysis": "The image features a sleek, dark navy suit with a subtle textured finish, paired with a crisp white dress shirt and a matching navy tie, showcasing a classic and sophisticated look."
    }
  ]
}
```