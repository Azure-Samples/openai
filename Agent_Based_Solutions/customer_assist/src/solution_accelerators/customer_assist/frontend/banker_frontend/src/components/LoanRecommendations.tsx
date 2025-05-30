// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import React, { useState, useEffect, useCallback, useMemo } from "react";
import "./components.css";
import {
  AdvisorInsights,
  InsightsData,
  DocumentStatus,
  FormField,
} from "../api/models";

interface LoanRecommendationsProps {
  insights: InsightsData | null;
}

interface LoanPolicyInfo {
  maxAmount: string;
  minTerm: string;
  maxTerm: string;
  minRate: string;
  maxRate: string;
  summary: string;
}

const LoanRecommendations: React.FC<LoanRecommendationsProps> = ({
  insights,
}) => {
  const [loading, setLoading] = useState(true);
  const [nextFields, setNextFields] = useState<FormField[]>([]);
  const [documents, setDocuments] = useState<DocumentStatus[]>([]);
  const [nextQuestion, setNextQuestion] = useState<string>("");
  const [loanPolicy, setLoanPolicy] = useState<LoanPolicyInfo | null>(null);

  // Convert missing fields to FormField objects with improved section mapping
  const convertMissingFieldsToFormFields = useCallback(
    (advisorInsights: AdvisorInsights | undefined): FormField[] => {
      if (!advisorInsights || !advisorInsights.missing_fields) {
        return [];
      }

      // Map field names to their sections
      const fieldSections: Record<string, string> = {
        // Personal information fields
        first_name: "Personal Details",
        last_name: "Personal Details",
        email: "Personal Details",

        // Loan information fields
        loan_purpose: "Loan Information",
        loan_amount: "Loan Information",
        loan_term: "Loan Information",
        loan_term_expiration_date: "Loan Information",

        // Financial information fields
        credit_score: "Financial Information",

        // Document verification fields
        primary_id_type: "Personal Details Verification",
        drivers_license_number: "Personal Details Verification",
        document_number: "Personal Details Verification",
        expiration_date: "Personal Details Verification",
        expiry_date: "Personal Details Verification",

        current_address: "Address Verification",
        full_address: "Address Verification",
        address_since: "Address Verification",
        address_document: "Address Verification",

        income_type: "Income Verification",
        monthly_income: "Income Verification",
        income_document: "Income Verification",
      };

      return advisorInsights.missing_fields.map((field, index) => ({
        id: field,
        name: field.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()), // Format field name for display
        section: fieldSections[field] || "Additional Information",
        priority: index + 1,
      }));
    },
    []
  );

  // Convert document verification insights to document status objects
  const convertToDocumentStatus = useCallback(
    (advisorInsights: AdvisorInsights | undefined): DocumentStatus[] => {
      if (!advisorInsights) {
        return [];
      }

      const documents: DocumentStatus[] = [];

      // Get the message for analysis
      const verificationMessage =
        advisorInsights.document_verification_insights || "";

      // Check both status field and message content for verification keywords
      const isVerified =
        advisorInsights.document_verification_status
          ?.toLowerCase()
          .includes("verified") ||
        verificationMessage.toLowerCase().includes("verified") ||
        verificationMessage.toLowerCase().includes("matches successfully") ||
        verificationMessage.toLowerCase().includes("valid");

      const isPending =
        advisorInsights.document_verification_status
          ?.toLowerCase()
          .includes("pending") ||
        verificationMessage.toLowerCase().includes("pending") ||
        verificationMessage.toLowerCase().includes("waiting");

      // Determine status based on content analysis
      const docStatus: "verified" | "pending" | "missing" = isVerified
        ? "verified"
        : isPending
        ? "pending"
        : "missing";

      documents.push({
        type: "Document Verification",
        status: docStatus,
        message:
          verificationMessage || "No document verification insights available",
      });

      return documents;
    },
    []
  );

  // Process loan policy insights from advisor insights
  const processLoanPolicyInsights = useCallback(
    (advisorInsights: AdvisorInsights | undefined): LoanPolicyInfo | null => {
      if (!advisorInsights || !advisorInsights.loan_policy_insights) {
        return null;
      }

      const policyInsights = advisorInsights.loan_policy_insights;
      return {
        maxAmount: policyInsights.max_loan_amount || "N/A",
        minTerm: policyInsights.min_loan_term || "N/A",
        maxTerm: policyInsights.max_loan_term || "N/A",
        minRate: policyInsights.min_interest_rate || "N/A",
        maxRate: policyInsights.max_interest_rate || "N/A",
        summary: policyInsights.policy_summary || "No policy summary available",
      };
    },
    []
  );

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      try {
        // Set next fields from backend insights
        if (insights?.advisorInsights) {
          const formattedFields = convertMissingFieldsToFormFields(
            insights.advisorInsights
          );

          // Only set top 3 fields
          const topFields = formattedFields.slice(0, 3);
          setNextFields(topFields);

          // Set next question from backend
          setNextQuestion(insights.advisorInsights.next_question || "");

          // Set document verification status
          const docStatus = convertToDocumentStatus(insights.advisorInsights);
          setDocuments(docStatus);

          // Process and set loan policy insights
          const policyInfo = processLoanPolicyInsights(
            insights.advisorInsights
          );
          setLoanPolicy(policyInfo);
        }
      } catch (error) {
        console.error("Failed to load data:", error);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadData();

    return () => {
      isMounted = false;
    };
  }, [
    insights,
    convertMissingFieldsToFormFields,
    convertToDocumentStatus,
    processLoanPolicyInsights,
  ]);

  // Memoized helper functions for consistent UI rendering
  const getStatusIcon = useMemo(() => {
    return (status: string): string => {
      switch (status) {
        case "verified":
          return "✅";
        case "pending":
          return "⚠️";
        case "missing":
          return "❌";
        default:
          return "❓";
      }
    };
  }, []);

  const getStatusColor = useMemo(() => {
    return (status: string): string => {
      switch (status) {
        case "verified":
          return "var(--success-color)";
        case "pending":
          return "var(--warning-color)";
        case "missing":
          return "var(--danger-color)";
        default:
          return "inherit";
      }
    };
  }, []);

  return (
    <div className="panel recommendations-panel">
      <div className="panel-header">
        <div className="panel-title">Advisor Insights</div>
        <div className="status-indicator status-active"></div>
      </div>

      {loading ? (
        <div className="panel-loading">Loading advisor insights...</div>
      ) : (
        <div className="panel-content">
          <div className="insight-section">
            <h3 className="insight-title">Suggested Next Question</h3>
            {nextQuestion ? (
              <div
                className="next-question-container"
                style={{
                  backgroundColor: "var(--primary-light)",
                  padding: "10px",
                  borderRadius: "6px",
                  marginBottom: "12px",
                }}
              >
                {nextQuestion}
              </div>
            ) : (
              <div className="no-data-message">
                Loading loan policy information...
              </div>
            )}
          </div>

          {/* Loan Policy Information Section */}
          <div className="insight-section">
            <h3 className="insight-title">Loan Policy Information</h3>
            <div className="loan-policy-info">
              {loanPolicy ? (
                <>
                  <div className="loan-policy-details">
                    <p>
                      <strong>Maximum Loan Amount:</strong> $
                      {loanPolicy.maxAmount}
                    </p>
                    <p>
                      <strong>Interest Rate Range:</strong> {loanPolicy.minRate}
                      % - {loanPolicy.maxRate}%
                    </p>
                    <p>
                      <strong>Loan Term Range:</strong> {loanPolicy.minTerm} -{" "}
                      {loanPolicy.maxTerm} months
                    </p>
                  </div>
                  <div className="loan-policy-summary">
                    <strong>Policy Summary:</strong> {loanPolicy.summary}
                  </div>
                </>
              ) : (
                <div className="no-data-message">
                  Loading loan policy information...
                </div>
              )}
            </div>
          </div>

          <div className="insight-section">
            <h3 className="insight-title">Missing Information</h3>
            <div className="next-fields-list">
              {nextFields.length > 0 ? (
                nextFields.map((field, index) => (
                  <div key={field.id} className="next-field-item">
                    <div className="field-priority">{index + 1}</div>
                    <div className="field-info">
                      <div className="field-name">{field.name}</div>
                      {field.section && (
                        <div className="field-section">{field.section}</div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-data-message">
                  No missing fields detected
                </div>
              )}
            </div>
          </div>

          <div className="insight-section">
            <h3 className="insight-title">Document Verification Status</h3>
            <div className="document-status-list">
              {documents.length > 0 ? (
                documents.map((doc, index) => (
                  <div key={index} className="document-status-item">
                    <div
                      className="document-status-icon"
                      style={{ color: getStatusColor(doc.status) }}
                    >
                      {getStatusIcon(doc.status)}
                    </div>
                    <div className="document-status-info">
                      <div className="document-type">{doc.type}</div>
                      <div
                        className="document-message"
                        style={{ color: getStatusColor(doc.status) }}
                      >
                        {doc.message}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-data-message">
                  No document verification information available
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LoanRecommendations;
