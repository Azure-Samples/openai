// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import React, { useMemo } from "react";
import "./components.css";
import { SentimentAnalysisData } from "../api/models";

interface SentimentInsightsProps {
  sentimentData: SentimentAnalysisData | undefined;
}

const SentimentInsights: React.FC<SentimentInsightsProps> = ({
  sentimentData,
}) => {
  // Memoized helper functions to prevent recalculation on each render
  const getSentimentIcon = useMemo(() => {
    return (sentiment: string): string => {
      if (!sentiment) return "😐";

      const normalizedSentiment = sentiment.toUpperCase();
      switch (normalizedSentiment) {
        case "POSITIVE":
          return "😊";
        case "NEGATIVE":
          return "😞";
        case "NEUTRAL":
        default:
          return "😐";
      }
    };
  }, []);

  const getSentimentColor = useMemo(() => {
    return (sentiment: string): string => {
      if (!sentiment) return "#9e9e9e"; // Default gray

      const normalizedSentiment = sentiment.toUpperCase();
      switch (normalizedSentiment) {
        case "POSITIVE":
          return "var(--success-color)";
        case "NEGATIVE":
          return "var(--danger-color)";
        case "NEUTRAL":
        default:
          return "#9e9e9e"; // Gray for neutral
      }
    };
  }, []);

  const formatSentiment = useMemo(() => {
    return (sentiment: string): string => {
      if (!sentiment) return "Unknown";
      return (
        sentiment.charAt(0).toUpperCase() + sentiment.slice(1).toLowerCase()
      );
    };
  }, []);

  return (
    <div className="panel sentiment-panel">
      <div className="panel-header">
        <div className="panel-title">Customer Sentiment</div>
        <div className="status-indicator status-active"></div>
      </div>

      {!sentimentData ? (
        <div className="panel-loading">Analyzing customer sentiment...</div>
      ) : (
        <div className="panel-content">
          <div className="sentiment-container">
            <div
              className="sentiment-icon"
              style={{ color: getSentimentColor(sentimentData.sentiment) }}
            >
              {getSentimentIcon(sentimentData.sentiment)}
            </div>
            <div className="sentiment-details">
              <div
                className="sentiment-label"
                style={{ color: getSentimentColor(sentimentData.sentiment) }}
              >
                {formatSentiment(sentimentData.sentiment)}
              </div>
              {sentimentData.reasoning && (
                <div className="sentiment-reasoning">
                  <strong>Analysis:</strong> {sentimentData.reasoning}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SentimentInsights;
