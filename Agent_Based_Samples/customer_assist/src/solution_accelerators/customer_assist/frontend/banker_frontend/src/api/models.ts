// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */
// Front end models

export type InputText = {
  text: string;
};

export type InputImage = {
  imageName: string;
  imageUrl: string;
};

export type InputProduct = {
  articleId: string;
  productName: string;
  productImageUrl: string;
};

export type UserInput = {
  message: (InputText | InputImage | InputProduct)[];
};

// Backend models

// User profiles

export enum UserGender {
  Male = "Male",
  Female = "Female",
  Other = "Other",
}

// See UserProfile in src/common/contracts/data/user_profile.py
export type UserProfile = {
  id: string;
  user_name: string;
  description: string;
  gender: UserGender;
  age: number;
  role: UserRole;
};

// User message types

// See Overrides in src/common/contracts/data/chat_session.py
export type Overrides = {
  isContentSafetyEnabled?: boolean;
};

// See UserPromptPayload in src/common/contracts/data/chat_session.py
export enum PayloadType {
  Text = "text",
  Image = "image",
  Product = "product",
}

export type SearchOverrides = {
  semantic_ranker?: boolean;
  vector_search?: boolean;
  top?: number;
  config_version?: string;
};

export type OrchestratorServiceOverrides = {
  search_results_merge_stratery?: string;
  config_version?: string;
};

export type SessionManagerServiceOverrides = {
  check_safe_image_content?: boolean;
  config_version?: string;
};

export type ChatRequestOverrides = {
  search_overrides?: SearchOverrides;
  orchestrator_runtime?: OrchestratorServiceOverrides;
  session_manager_runtime?: SessionManagerServiceOverrides;
};

export type UserPromptPayload = {
  type: string;
  value: string;
  locale?: string;
};

export type UserPrompt = {
  payload: UserPromptPayload[];
};

// Adding proper UserRole enum based on the comments
export enum UserRole {
  CUSTOMER = "customer",
  ADVISOR = "advisor",
  USER = "user",
}

export interface ChatRequest {
  user_id: string;
  dialog_id: string;
  message: UserPrompt;
  user_profile: UserProfile;
  overrides?: ChatRequestOverrides;
  additional_metadata?: {
    [key: string]: any;
  };
}

export class ChatResponseError extends Error {
  private retryable: boolean;

  constructor(message: string, retryable: boolean = false) {
    super((message = message));
    this.message = message;
    this.retryable = retryable;
  }
}

// Bot message types
// TODO: update these once the session manager contracts are updated to match the proposed contracts

// See SearchResult in src/common/contracts/data/chat_session.py
export interface SearchResultBase {
  articleId: string;
  productName: string;
  summarizedDescription: string;
  detailDescription: string;
  imageUrl: string;
}

// leaving old index names to avoid breaking website if using older search server
export interface SearchResultRetail extends SearchResultBase {
  category: string;
  prod_name?: string;
  article_id?: string;
  image_sas_url?: string;
}

export type SearchResult = SearchResultRetail;

export type CognitiveSearchResult = {
  search_results: SearchResult[];
};

export type SkillOutput = {
  results: CognitiveSearchResult[];
};

export type SkillResult = {
  step_output?: SkillOutput;
  trimmed_search_results: SearchResultRetail[];
};

export type StepsExecution = {
  cognitiveSearchSkill?: SkillResult;
};

export type Answer = {
  answer_string: string;
  data_points?: string[];
  steps_execution?: StepsExecution;
  speak_answer?: string;
  speaker_locale?: string;
  // The following fields are optional and can be used for additional metadata specific to the use-case.
  // They can be set to None if not needed.
  additional_metadata: {
    [key: string]: any;
  };
};

export type Error = {
  error_str?: string;
  retry?: boolean;
  status_code?: number;
};

export type ChatResponse = {
  connection_id: string;
  dialog_id: string;
  conversation_id: string;
  user_id: string;
  answer: {
    answer_string: string;
    additional_metadata: {
      insights?: InsightsData;
      sentiment_analysis?: SentimentAnalysisData;
      form_data?: LoanApplicationForm;
      transcript?: TranscriptMessage[];
      [key: string]: any;
    };
    data_points?: string[];
    steps_execution?: StepsExecution;
    speak_answer?: string;
    speaker_locale?: string;
  };
  error?: Error;
};

// Define additional types needed for the advisor dashboard
export interface SentimentAnalysisData {
  sentiment: "Positive" | "Neutral" | "Negative";
  reasoning: string;
  score?: number;
}

// New interfaces to match backend models
export interface AdvisorInsights {
  missing_fields: string[];
  next_question: string;
  document_verification_insights: string;
  document_verification_status: string;
  loan_policy_insights?: {
    max_loan_amount?: string;
    min_loan_term?: string;
    max_loan_term?: string;
    min_interest_rate?: string;
    max_interest_rate?: string;
    policy_summary?: string;
  };
}

export interface PostCallAnalysis {
  next_steps: string[];
  summary: string;
  overall_sentiment: string;
  overall_engagement: string;
  advisor_feedback: string;
}

export interface FormField {
  name: string;
  id: string;
  section: string;
  priority: number;
}

export interface DocumentStatus {
  type: string;
  status: "verified" | "pending" | "missing";
  message?: string;
}

export interface LoanOffer {
  id: string;
  name: string;
  interestRate: number;
  term: number;
  maxAmount: number;
  description: string;
}
// Models for Advisor Landing Page

export interface PersonalInformation {
  first_name: string;
  last_name: string;
  email: string;
}

export interface LoanInformation {
  loan_purpose: "BUSINESS" | "PERSONAL";
  loan_amount: number;
  loan_term: number; // in months
  loan_term_expiration_date: string;
}

export interface FinancialInformation {
  credit_score: number;
}

// New interface for validation documents
export interface IdentificationDetails {
  drivers_license_number: string;
  expiry_date: string; // Changed from expiration_date to expiry_date to match backend
}

export interface AddressVerification {
  full_address: string;
  is_verified: boolean;
}

export interface LoanApplicationForm {
  personal_info: PersonalInformation;
  loan_info: LoanInformation;
  financial_info: FinancialInformation;
  identification_details: IdentificationDetails;
  address_verification: AddressVerification;
}

export interface InsightsData {
  advisorInsights: AdvisorInsights;
  sentimentAnalysis: SentimentAnalysisData;
  postCallAnalysis: PostCallAnalysis;
}

export interface TranscriptMessage {
  role: "advisor" | "customer";
  text: string;
  image_url?: string;
  image_description?: string;
}

export type SpeechKeyResponse = {
  token: string;
  region: string;
  received_at: Date;
};
