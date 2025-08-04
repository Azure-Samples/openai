import React, { useState, useRef, useEffect } from "react";
import { BingGroundingMetadata, BingSearchAnnotation } from "../api/types";
import bingLogo from "../static/bing_icon.ico";
import "./Citations.css";

interface CitationsProps {
  bingGroundingMetadata: BingGroundingMetadata;
  messageText?: string;
}

interface ReferencedAnnotation extends BingSearchAnnotation {
  originalIndex: number;
}

export const Citations: React.FC<CitationsProps> = ({
  bingGroundingMetadata,
  messageText,
}) => {
  const [activeTooltip, setActiveTooltip] = useState<number | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState<string>("");
  const tooltipRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});
  if (
    !bingGroundingMetadata ||
    (!bingGroundingMetadata.bing_search_queries?.length &&
      !bingGroundingMetadata.bing_search_annotations?.length)
  ) {
    return null;
  }

  // Extract citation indices from the message text to get the referenced annotations
  const getReferencedAnnotations = (): ReferencedAnnotation[] => {
    if (
      !messageText ||
      !bingGroundingMetadata.bing_search_annotations?.length
    ) {
      return (
        bingGroundingMetadata.bing_search_annotations?.map(
          (annotation, index) => ({
            ...annotation,
            originalIndex: index,
          })
        ) || []
      );
    }

    // Extract all citation markers from the message text
    const citationRegex = /【\d+:\d+†source】/g;
    const foundCitations = [];
    let match;

    while ((match = citationRegex.exec(messageText)) !== null) {
      foundCitations.push(match[0]); // Store the full citation marker
    }

    // Find annotations that match the citations found in the text
    const referencedAnnotations: ReferencedAnnotation[] = [];

    foundCitations.forEach((citationMarker) => {
      const annotationIndex =
        bingGroundingMetadata.bing_search_annotations.findIndex(
          (annotation) => annotation.quote === citationMarker
        );

      if (annotationIndex !== -1) {
        const annotation =
          bingGroundingMetadata.bing_search_annotations[annotationIndex];
        referencedAnnotations.push({
          ...annotation,
          originalIndex: annotationIndex,
        });
      }
    });

    // If no matching annotations found, show all annotations
    if (referencedAnnotations.length === 0) {
      return bingGroundingMetadata.bing_search_annotations.map(
        (annotation, index) => ({
          ...annotation,
          originalIndex: index,
        })
      );
    }

    return referencedAnnotations;
  };

  const referencedAnnotations = getReferencedAnnotations();
  const handleQuoteHover = (
    annotationIndex: number,
    event: React.MouseEvent
  ) => {
    setActiveTooltip(annotationIndex);

    // Calculate tooltip position
    const sourceItem = event.currentTarget as HTMLElement;
    const rect = sourceItem.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const tooltipWidth = 400; // min-width from CSS

    // Check if tooltip would overflow on the right
    if (rect.left + rect.width / 2 + tooltipWidth / 2 > viewportWidth - 20) {
      setTooltipPosition("tooltip-right");
    }
    // Check if tooltip would overflow on the left
    else if (rect.left + rect.width / 2 - tooltipWidth / 2 < 20) {
      setTooltipPosition("tooltip-left");
    }
    // Default centered position
    else {
      setTooltipPosition("");
    }
  };

  const handleQuoteLeave = () => {
    setActiveTooltip(null);
  };
  const handleSourceClick = (url: string | null) => {
    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
    }
  };

  const handleSearchQueryClick = (query: string) => {
    const bingSearchUrl = `https://www.bing.com/search?q=${encodeURIComponent(
      query
    )}`;
    window.open(bingSearchUrl, "_blank", "noopener,noreferrer");
  };

  return (
    <div>
      {" "}
      {/* Search Queries */}
      {bingGroundingMetadata.bing_search_queries?.length > 0 && (
        <div className="search-queries-section">
          {" "}
          <div className="citations-label">
            <img src={bingLogo} alt="Bing" className="bing-logo" />
            Search Queries
          </div>
          <div className="search-queries">
            {bingGroundingMetadata.bing_search_queries.map((query, index) => (
              <span
                key={index}
                className="search-query-pill clickable"
                onClick={() => handleSearchQueryClick(query)}
                title={`Click to search "${query}" on Bing`}
              >
                {query}
              </span>
            ))}
          </div>
        </div>
      )}{" "}
      {/* Bing Search Sources */}
      {referencedAnnotations.length > 0 && (
        <div className="sources-section">
          <div className="citations-label">Sources:</div>{" "}
          <div className="sources-grid">
            {" "}
            {referencedAnnotations.map((annotation, displayIndex) => {
              // Use the original index + 1 for the display number (to match TextWithCitations)
              const displayNumber = (annotation.originalIndex + 1).toString();

              return (
                <div
                  key={annotation.originalIndex}
                  className="source-item"
                  onMouseEnter={(e) =>
                    handleQuoteHover(annotation.originalIndex, e)
                  }
                  onMouseLeave={handleQuoteLeave}
                  onClick={() => handleSourceClick(annotation.url)}
                >
                  <div className="source-indicator">{displayNumber}</div>
                  <div className="source-title">
                    {annotation.title || "Untitled Source"}
                  </div>
                  {/* Tooltip */}
                  {activeTooltip === annotation.originalIndex && (
                    <div
                      className={`source-tooltip ${tooltipPosition}`}
                      onMouseEnter={() =>
                        setActiveTooltip(annotation.originalIndex)
                      }
                      onMouseLeave={handleQuoteLeave}
                    >
                      <div className="tooltip-content">
                        <div className="tooltip-title">
                          {annotation.title || "Untitled Source"}
                        </div>
                        {annotation.url && (
                          <div className="tooltip-url">{annotation.url}</div>
                        )}{" "}
                        <div className="tooltip-action">
                          Click to open source
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
