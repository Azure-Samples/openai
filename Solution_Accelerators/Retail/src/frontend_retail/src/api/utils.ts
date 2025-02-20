export const parseDescription = (description: string): [string, string[]] => {
    const regex = new RegExp(/Description: (.*)\n\n\sAttributes: (.*)/g);
    const match = regex.exec(description);

    const descriptionText = match ? match[1] : description;
    const attributesText = match ? match[2] : "";
    const attributes = attributesText.split(",").map(attribute => attribute.trim());

    return [descriptionText, attributes];
};
