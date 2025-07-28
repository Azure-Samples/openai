// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import React, { useState, useEffect } from "react";
import {
  LoanApplicationForm as LoanFormData,
  type LoanApplicationForm,
} from "../api/models";
import "./components.css";

export interface LoanApplicationFormProps {
  initialData: LoanFormData | null;
}

const initialState: LoanApplicationForm = {
  personal_info: { first_name: "", last_name: "", email: "" },
  loan_info: {
    loan_purpose: "PERSONAL",
    loan_amount: 0,
    loan_term: 0,
    loan_term_expiration_date: "",
  },
  financial_info: { credit_score: 0 },
  identification_details: {
    drivers_license_number: "",
    expiry_date: "",
  },
  address_verification: {
    full_address: "",
    is_verified: false,
  },
};

const LoanApplicationForm: React.FC<LoanApplicationFormProps> = ({
  initialData,
}) => {
  const [form, setForm] = useState(initialState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Update form when initialData changes with proper null handling
  useEffect(() => {
    if (initialData) {
      // Create a deep copy of initialData with null protection
      const safeData: LoanApplicationForm = {
        personal_info: {
          first_name: initialData.personal_info?.first_name || "",
          last_name: initialData.personal_info?.last_name || "",
          email: initialData.personal_info?.email || "",
        },
        loan_info: {
          loan_purpose: initialData.loan_info?.loan_purpose || "PERSONAL",
          loan_amount: initialData.loan_info?.loan_amount || 0,
          loan_term: initialData.loan_info?.loan_term || 0,
          loan_term_expiration_date:
            initialData.loan_info?.loan_term_expiration_date || "",
        },
        financial_info: {
          credit_score: initialData.financial_info?.credit_score || 300,
        },
        identification_details: {
          drivers_license_number:
            initialData.identification_details?.drivers_license_number || "",
          expiry_date: initialData.identification_details?.expiry_date || "",
        },
        address_verification: {
          full_address: initialData.address_verification?.full_address || "",
          is_verified: initialData.address_verification?.is_verified || false,
        },
      };
      setForm(safeData);
    }
  }, [initialData]);

  const handleChange = (
    section: keyof LoanApplicationForm,
    field: string,
    value: any
  ) => {
    setForm((prev) => ({
      ...prev,
      [section]: { ...(prev[section] || {}), [field]: value },
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault(); // Prevent default form submission
    // No action needed
  };

  // Helper function to safely access nested form properties
  const getSafeValue = (
    section: keyof LoanApplicationForm,
    field: string,
    defaultValue: any = ""
  ) => {
    const sectionObj = form[section] as Record<string, any>;
    return sectionObj && sectionObj[field] != null
      ? sectionObj[field]
      : defaultValue;
  };

  return (
    <form onSubmit={handleSubmit} className="loan-form">
      <h2>Loan Application Form</h2>
      <fieldset className="loan-fieldset">
        <legend>
          <b>Personal Information</b>
        </legend>
        <div className="loan-flex-row">
          <div className="loan-flex-1">
            <label htmlFor="first_name">First Name</label>
            <input
              id="first_name"
              name="first_name"
              value={getSafeValue("personal_info", "first_name")}
              onChange={(e) =>
                handleChange("personal_info", "first_name", e.target.value)
              }
              required
              minLength={2}
              title="Enter your first name"
              placeholder="First Name"
            />
          </div>
          <div className="loan-flex-1">
            <label htmlFor="last_name">Last Name</label>
            <input
              id="last_name"
              name="last_name"
              value={getSafeValue("personal_info", "last_name")}
              onChange={(e) =>
                handleChange("personal_info", "last_name", e.target.value)
              }
              required
              minLength={2}
              title="Enter your last name"
              placeholder="Last Name"
            />
          </div>
        </div>
        <div className="loan-margin-top-16">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            value={getSafeValue("personal_info", "email")}
            onChange={(e) =>
              handleChange("personal_info", "email", e.target.value)
            }
            required
            title="Enter your email address"
            placeholder="Email"
          />
        </div>
      </fieldset>
      <fieldset className="loan-fieldset">
        <legend>
          <b>Loan Information</b>
        </legend>
        <div className="loan-flex-row">
          <div className="loan-flex-1">
            <label htmlFor="loan_purpose">Loan Purpose</label>
            <select
              id="loan_purpose"
              name="loan_purpose"
              value={getSafeValue("loan_info", "loan_purpose", "BUSINESS")}
              onChange={(e) =>
                handleChange("loan_info", "loan_purpose", e.target.value)
              }
              required
              title="Select loan purpose"
            >
              <option value="PERSONAL">Personal</option>
              <option value="BUSINESS">Business</option>
            </select>
          </div>
          <div className="loan-flex-1">
            <label htmlFor="loan_amount">Loan Amount</label>
            <input
              id="loan_amount"
              name="loan_amount"
              type="number"
              min={1}
              value={getSafeValue("loan_info", "loan_amount", 0)}
              onChange={(e) =>
                handleChange("loan_info", "loan_amount", Number(e.target.value))
              }
              required
              title="Enter loan amount"
              placeholder="Loan Amount"
            />
          </div>
          <div className="loan-flex-1">
            <label htmlFor="loan_term">Loan Term</label>
            <input
              id="loan_term"
              name="loan_term"
              type="number"
              min={1}
              value={getSafeValue("loan_info", "loan_term", 0)}
              onChange={(e) =>
                handleChange("loan_info", "loan_term", Number(e.target.value))
              }
              required
              title="Enter loan term"
              placeholder="Loan Term (in months)"
            />
          </div>
          <div className="loan-flex-1">
            <label htmlFor="loan_term">Loan Term Expiration Date</label>
            <input
              id="loan_term_expiration_date"
              name="loan_term_expiration_date"
              type="text"
              min={1}
              value={getSafeValue("loan_info", "loan_term_expiration_date", "")}
              onChange={(e) =>
                handleChange(
                  "loan_info",
                  "loan_term_expiration_date",
                  e.target.value
                )
              }
              required
              title="Enter loan term expiration date"
              placeholder="Loan Term Expiration Date (YYYY-MM-DD)"
            />
          </div>
        </div>
      </fieldset>
      <fieldset className="loan-fieldset">
        <legend>
          <b>Financial Information</b>
        </legend>
        <label htmlFor="credit_score">Credit Score</label>
        <input
          id="credit_score"
          name="credit_score"
          type="number"
          min={0}
          max={850}
          value={getSafeValue("financial_info", "credit_score", 300)}
          onChange={(e) =>
            handleChange(
              "financial_info",
              "credit_score",
              Number(e.target.value)
            )
          }
          required
          title="Enter your credit score"
          placeholder="Credit Score (300-850)"
        />
      </fieldset>

      {/* Identification Details Section */}
      <fieldset className="loan-fieldset">
        <legend>
          <b>Identification Details</b>
        </legend>
        <div className="loan-form-group">
          <label htmlFor="drivers_license_number">
            Driver's License Number <span className="required">*</span>
          </label>
          <input
            type="text"
            id="drivers_license_number"
            name="drivers_license_number"
            value={getSafeValue(
              "identification_details",
              "drivers_license_number"
            )}
            onChange={(e) =>
              handleChange(
                "identification_details",
                "drivers_license_number",
                e.target.value
              )
            }
            required
            placeholder="Enter driver's license number"
          />
        </div>
        <div className="loan-form-group">
          <label htmlFor="expiry_date">
            Expiration Date <span className="required">*</span>
          </label>
          <input
            type="text"
            id="expiry_date"
            name="expiry_date"
            value={getSafeValue("identification_details", "expiry_date")}
            onChange={(e) =>
              handleChange(
                "identification_details",
                "expiry_date",
                e.target.value
              )
            }
            required
          />
        </div>
      </fieldset>

      {/* Address Verification Section */}
      <fieldset className="loan-fieldset">
        <legend>
          <b>Address Verification</b>
        </legend>
        <div className="loan-form-group">
          <label htmlFor="full_address">
            Full Address <span className="required">*</span>
          </label>
          <textarea
            id="full_address"
            name="full_address"
            value={getSafeValue("address_verification", "full_address")}
            onChange={(e) =>
              handleChange(
                "address_verification",
                "full_address",
                e.target.value
              )
            }
            rows={3}
            required
            placeholder="Enter complete address"
          />
        </div>

        <div className="loan-form-group">
          <label className="loan-checkbox-label">
            <input
              type="checkbox"
              name="is_verified"
              checked={getSafeValue(
                "address_verification",
                "is_verified",
                false
              )}
              onChange={(e) =>
                handleChange(
                  "address_verification",
                  "is_verified",
                  e.target.checked
                )
              }
              required
            />
            Address Verified <span className="required">*</span>
          </label>
        </div>
      </fieldset>

      <button type="submit" className="loan-submit-btn" disabled={loading}>
        {loading ? "Submitting..." : "Submit Application"}
      </button>
      {error && <div className="loan-error">{error}</div>}
      {success && (
        <div className="loan-success">Application submitted successfully!</div>
      )}
    </form>
  );
};

export default LoanApplicationForm;
