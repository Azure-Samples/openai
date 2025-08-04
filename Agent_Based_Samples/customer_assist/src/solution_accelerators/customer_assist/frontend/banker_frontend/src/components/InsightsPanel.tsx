// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import React, { useState, useEffect, useMemo } from "react";
import "./components.css";

interface InsightsData {
  customerSentiment: string;
  sentimentScore: number;
  keyIndicators: string[];
  recommendation: string;
}

const InsightsPanel: React.FC = () => {
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    // TODO: Replace with actual data fetching logic or remove if not needed
    setLoading(false);

    return () => {
      isMounted = false;
    };
  }, []);

  // Helper for sentiment color - memoized to prevent recreation on each render
  const getSentimentColor = useMemo(
    () =>
      (sentiment: string): string => {
        switch (sentiment.toLowerCase()) {
          case "positive":
            return "var(--success-color)";
          case "neutral":
            return "var(--warning-color)";
          case "negative":
            return "var(--danger-color)";
          default:
            return "var(--primary-color)";
        }
      },
    []
  );

  if (loading) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="panel-title">Customer Insights</div>
        </div>
        <div className="panel-loading">Loading insights...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel">
        <div className="panel-header">
          <div className="panel-title">Customer Insights</div>
        </div>
        <div className="panel-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <div className="panel-title">Customer Insights</div>
        <div className="status-indicator status-active"></div>
      </div>

      {insights && (
        <div className="panel-content">
          <div className="sentiment-summary">
            <div
              className="sentiment-score"
              style={{
                fontSize: "2em",
                fontWeight: "bold",
                color: getSentimentColor(insights.customerSentiment),
              }}
            >
              {Math.round(insights.sentimentScore * 100)}%
            </div>
            <div className="sentiment-label">
              {insights.customerSentiment} Sentiment
            </div>
          </div>

          <div className="insight-content">
            <p>
              Customer appears {insights.customerSentiment.toLowerCase()} with
              the service
            </p>
            <p className="indicators">
              <strong>Key indicators:</strong>{" "}
              {insights.keyIndicators.map((indicator, index) => (
                <span key={index} className="indicator">
                  "{indicator}"
                  {index < insights.keyIndicators.length - 1 ? ", " : ""}
                </span>
              ))}
            </p>
            <div className="recommendation-box">
              <strong>Recommendation:</strong> {insights.recommendation}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InsightsPanel;
