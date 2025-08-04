// Utility functions for processing Bing citations

export interface ParsedCitation {
  originalText: string;
  annotationIndex: number;
  quote: string;
}

/**
 * Parse citation markers from text and return processed text with citations
 * Citation markers look like: 【8:1†source】, 【8:2†source】, etc.
 */
export function parseCitationMarkers(text: string): {
  processedText: string;
  citations: ParsedCitation[];
} {
  const citationPattern = /【(\d+):(\d+)†source】/g;
  const citations: ParsedCitation[] = [];
  let processedText = text;
  let match;

  while ((match = citationPattern.exec(text)) !== null) {
    const fullMatch = match[0];
    const annotationIndex = parseInt(match[2], 10) - 1; // Convert to 0-based index
    const quote = fullMatch;

    citations.push({
      originalText: fullMatch,
      annotationIndex,
      quote,
    });

    // Replace the citation marker with a clickable link
    processedText = processedText.replace(
      fullMatch,
      `<sup class="citation-link" data-annotation-index="${annotationIndex}">[${match[2]}]</sup>`
    );
  }

  return { processedText, citations };
}

/**
 * Create HTML for text with citations
 */
export function createCitationHTML(text: string): string {
  const { processedText } = parseCitationMarkers(text);
  return processedText;
}
