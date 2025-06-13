import React from "react";
import { BingGroundingMetadata } from "../api/types";
import { markdownToHTML, wrapLists } from "../utils/markdownUtils";

interface TextWithCitationsProps {
  text: string;
  bingGroundingMetadata?: BingGroundingMetadata;
}

export const TextWithCitations: React.FC<TextWithCitationsProps> = ({
  text,
  bingGroundingMetadata,
}) => {
  const handleCitationClick = (annotationIndex: number) => {
    if (
      bingGroundingMetadata?.bing_search_annotations?.[annotationIndex]?.url
    ) {
      window.open(
        bingGroundingMetadata.bing_search_annotations[annotationIndex].url!,
        "_blank",
        "noopener,noreferrer"
      );
    }
  };

  // If no citations, just render text with markdown formatting
  if (
    !bingGroundingMetadata ||
    !bingGroundingMetadata.bing_search_annotations?.length
  ) {
    const htmlContent = wrapLists(markdownToHTML(text));
    return <span dangerouslySetInnerHTML={{ __html: htmlContent }} />;
  }
  // Process citations first, then apply markdown formatting
  const citationRegex = /【\d+:\d+†source】/g;
  const parts: (string | React.ReactElement)[] = [];
  let lastIndex = 0;
  let match;

  while ((match = citationRegex.exec(text)) !== null) {
    // Add text before the citation with markdown formatting
    if (match.index > lastIndex) {
      const textBefore = text.slice(lastIndex, match.index);
      const htmlContent = wrapLists(markdownToHTML(textBefore));
      parts.push(
        <span
          key={`text-${lastIndex}`}
          dangerouslySetInnerHTML={{ __html: htmlContent }}
        />
      );
    }

    // Find the annotation that matches this citation marker
    const citationMarker = match[0]; // Full citation like "【3:0†source】"
    const annotationIndex =
      bingGroundingMetadata.bing_search_annotations?.findIndex(
        (annotation) => annotation.quote === citationMarker
      ) ?? -1;

    // Use 1-based numbering for display (findIndex returns -1 if not found, so we add 1)
    const displayNumber = annotationIndex + 1;

    parts.push(
      <span
        key={match.index}
        className="citation-link"
        onClick={() => handleCitationClick(annotationIndex)}
        title={
          annotationIndex >= 0 &&
          bingGroundingMetadata.bing_search_annotations?.[annotationIndex]
            ? bingGroundingMetadata.bing_search_annotations[annotationIndex]
                .title || "Source"
            : "Source"
        }
      >
        [{displayNumber}]
      </span>
    );

    lastIndex = citationRegex.lastIndex;
  }

  // Add remaining text with markdown formatting
  if (lastIndex < text.length) {
    const textAfter = text.slice(lastIndex);
    const htmlContent = wrapLists(markdownToHTML(textAfter));
    parts.push(
      <span
        key={`text-${lastIndex}`}
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />
    );
  }

  return <span>{parts}</span>;
};
