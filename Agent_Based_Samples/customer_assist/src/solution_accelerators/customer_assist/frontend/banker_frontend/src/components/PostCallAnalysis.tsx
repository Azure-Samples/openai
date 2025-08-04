// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import React from "react";
import { PostCallAnalysis as PostCallAnalysisData } from "../api/models";
import "./components.css";

interface PostCallAnalysisProps {
  postCallData?: PostCallAnalysisData;
  isVisible: boolean;
  isLoading?: boolean;
}

const PostCallAnalysis: React.FC<PostCallAnalysisProps> = ({
  postCallData,
  isVisible,
  isLoading = false,
}) => {
  if (!isVisible) {
    return null;
  }

  return (
    <div className="panel post-call-panel">
      <div className="panel-header">
        <h2 className="panel-title">Call Summary</h2>
      </div>

      {isLoading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">Generating call summary...</p>
        </div>
      ) : postCallData &&
        (postCallData.summary ||
          postCallData.overall_sentiment ||
          postCallData.overall_engagement ||
          postCallData.advisor_feedback ||
          (postCallData.next_steps && postCallData.next_steps.length > 0)) ? (
        <div className="post-call-content">
          {postCallData.summary && (
            <div className="summary-section">
              <h3 className="section-title">Summary</h3>
              <div className="summary-text">{postCallData.summary}</div>
            </div>
          )}

          {postCallData.overall_sentiment && (
            <div className="sentiment-section">
              <h3 className="section-title">Overall Sentiment</h3>
              <div className="sentiment-text">
                {postCallData.overall_sentiment}
              </div>
            </div>
          )}

          {postCallData.overall_engagement && (
            <div className="engagement-section">
              <h3 className="section-title">Overall Engagement</h3>
              <div className="engagement-text">
                {postCallData.overall_engagement}
              </div>
            </div>
          )}

          {postCallData.advisor_feedback && (
            <div className="feedback-section">
              <h3 className="section-title">Advisor Feedback</h3>
              <div className="feedback-text">
                {postCallData.advisor_feedback}
              </div>
            </div>
          )}

          {postCallData.next_steps && postCallData.next_steps.length > 0 && (
            <div className="next-steps-section">
              <h3 className="section-title">Next Steps</h3>
              <ul className="next-steps-list">
                {postCallData.next_steps.map((step, index) => (
                  <li key={index} className="next-step-item">
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="no-data-message">
          {isLoading
            ? "Generating call summary..."
            : "No call summary available yet."}
        </div>
      )}
    </div>
  );
};

export default PostCallAnalysis;
