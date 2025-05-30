// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import React, { useState, useEffect, useCallback, lazy } from "react";
import {
  connectWebSocket,
  disconnectWebSocket,
  WebSocketError,
  sendWebSocketMessage,
  registerCallback,
} from "../api/api";
import {
  InsightsData,
  TranscriptMessage,
  LoanApplicationForm as LoanFormData,
  UserRole,
} from "../api/models";

// Lazy-loaded components with explicit loading indicators
import type { LoanApplicationFormProps } from "../components/LoanApplicationForm";
const LoanApplicationForm = React.lazy(
  () =>
    import("../components/LoanApplicationForm") as Promise<{
      default: React.ComponentType<LoanApplicationFormProps>;
    }>
);

const SentimentInsights = React.lazy(
  () => import("../components/SentimentInsights")
);
const ChatTranscript = React.lazy(() => import("../components/ChatTranscript"));
const LoanRecommendations = React.lazy(
  () => import("../components/LoanRecommendations")
);
const PostCallAnalysis = React.lazy(
  () => import("../components/PostCallAnalysis")
);

const AdvisorLandingPage: React.FC = () => {
  // State for shared data between components
  const [transcript, setTranscript] = useState<TranscriptMessage[]>([]);
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [formData, setFormData] = useState<LoanFormData | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPostCallAnalysis, setShowPostCallAnalysis] = useState(false);
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);

  // Handler functions for WebSocket updates
  const handleTranscriptUpdate = useCallback((data: TranscriptMessage[]) => {
    console.log("Transcript updated:", data);
    setTranscript([...data]); // Create a new array to ensure reference changes
  }, []);

  const handleInsightsUpdate = useCallback((incomingData: InsightsData) => {
    console.log("Insights updated:", incomingData);
    setInsights(incomingData);
  }, []);

  const handleFormUpdate = useCallback((data: LoanFormData) => {
    console.log("Form data updated:", data);
    setFormData({ ...data }); // Create a new object to ensure reference changes
  }, []);

  const handleError = useCallback((errorMsg: string) => {
    console.error("WebSocket error:", errorMsg);
    setError(errorMsg);
  }, []);

  // Connect to WebSocket when component mounts
  useEffect(() => {
    let isMounted = true;

    // Connect to WebSocket
    connectWebSocket(
      handleTranscriptUpdate,
      handleInsightsUpdate,
      handleFormUpdate,
      handleError
    )
      .then(() => {
        if (isMounted) {
          setWsConnected(true);
          setError(null);
        }
      })
      .catch((err: WebSocketError) => {
        if (isMounted) {
          setError(err.message);
        }
      });

    // Clean up WebSocket connection when component unmounts
    return () => {
      isMounted = false;
      disconnectWebSocket();
    };
  }, [
    handleTranscriptUpdate,
    handleInsightsUpdate,
    handleFormUpdate,
    handleError,
  ]);

  const handleGenerateSummary = useCallback(async () => {
    try {
      console.log("Generating end of call summary...");
      setError(null); // Clear any previous errors

      // Show PostCallAnalysis component immediately when button is clicked
      setShowPostCallAnalysis(true);
      setIsGeneratingSummary(true);

      // Using the enhanced sendWebSocketMessage function with simple additional metadata
      const additionalMetadata = { end_of_call: true };

      // Send the request using the updated sendWebSocketMessage function
      const dialogId = await sendWebSocketMessage(
        null, // No user input needed for summary requests
        UserRole.ADVISOR,
        additionalMetadata
      );

      console.log(`Summary request sent with dialog ID: ${dialogId}`);

      // Register a callback to handle the response if needed
      registerCallback(dialogId, (response) => {
        setIsGeneratingSummary(false);

        if (response.error) {
          setError(response.error.error_str || "Failed to generate summary");
          // Don't hide the panel - we'll show the error message inside it
        } else if (response.answer) {
          // Update insights with the summary data if available
          if (
            response.answer.additional_metadata?.post_call_analysis &&
            insights
          ) {
            // Make sure we create a complete InsightsData object with all required properties
            const updatedInsights: InsightsData = {
              // Keep the existing insights for the other properties
              advisorInsights: insights.advisorInsights,
              sentimentAnalysis: insights.sentimentAnalysis,
              // Update just the postCallAnalysis property
              postCallAnalysis:
                response.answer.additional_metadata.post_call_analysis,
            };
            setInsights(updatedInsights);
          }
        }
      });
    } catch (error) {
      console.error("Error generating summary:", error);
      setError("Failed to generate summary. Please try again.");
      setIsGeneratingSummary(false);
      // We keep the panel open to show the error
    }
  }, [insights]);

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Advisor Dashboard</h1>
        <div className="connection-status">
          {wsConnected ? (
            <span className="status-connected">Connected</span>
          ) : (
            <span className="status-disconnected">Disconnected</span>
          )}
        </div>
        <button onClick={handleGenerateSummary} className="summary-button">
          Generate Conversation Summary
        </button>
      </div>
      {error && <div className="error-banner">{error}</div>}
      <div className="dashboard">
        {/* Loan Application Form - Left panel */}
        <div
          style={{
            gridColumn: "1",
            gridRow: "1 / span 3",
            height: "100%",
            overflowY: "auto",
          }}
        >
          <React.Suspense
            fallback={
              <div className="panel panel-loading">
                Loading Loan Application Form...
              </div>
            }
          >
            <LoanApplicationForm initialData={formData} />
          </React.Suspense>
        </div>

        {/* Post Call Analysis Panel - Will appear over other components when shown */}
        {showPostCallAnalysis && (
          <div className="post-call-analysis-overlay">
            <div className="post-call-container">
              <button
                className="close-post-call-btn"
                onClick={() => setShowPostCallAnalysis(false)}
                aria-label="Close"
              >
                ×
              </button>
              <React.Suspense
                fallback={
                  <div className="panel panel-loading">
                    {isGeneratingSummary
                      ? "Generating call summary..."
                      : "Loading Post Call Analysis..."}
                  </div>
                }
              >
                <PostCallAnalysis
                  postCallData={insights?.postCallAnalysis}
                  isVisible={true}
                  isLoading={isGeneratingSummary}
                />
              </React.Suspense>
            </div>
          </div>
        )}

        <div style={{ gridColumn: "2", gridRow: "1", maxHeight: "60vh" }}>
          <React.Suspense
            fallback={
              <div className="panel panel-loading">
                Loading Advisor Insights...
              </div>
            }
          >
            <LoanRecommendations insights={insights} />
          </React.Suspense>
        </div>

        <div style={{ gridColumn: "2", gridRow: "2", maxHeight: "50vh" }}>
          <React.Suspense
            fallback={
              <div className="panel panel-loading">Loading Transcript...</div>
            }
          >
            <ChatTranscript transcriptData={transcript} />
          </React.Suspense>
        </div>

        {/* Sentiment Insights - Bottom right */}
        <div style={{ gridColumn: "2", gridRow: "3", maxHeight: "20vh" }}>
          <React.Suspense
            fallback={
              <div className="panel panel-loading">
                Loading Sentiment Insights...
              </div>
            }
          >
            <SentimentInsights sentimentData={insights?.sentimentAnalysis} />
          </React.Suspense>
        </div>
      </div>
    </>
  );
};

export default AdvisorLandingPage;
