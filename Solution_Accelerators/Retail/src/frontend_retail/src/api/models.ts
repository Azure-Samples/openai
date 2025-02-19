/*
 *   Copyright (c) 2024 
 *   All rights reserved.
 */
// Front end models

import { ProductDetails } from "../components/ProductDetails";

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
    Other = "Other"
}

// See UserProfile in src/common/contracts/data/user_profile.py
export type UserProfile = {
    id: string;
    user_name: string;
    description: string;
    gender: UserGender;
    age: number;
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
    Product = "product"
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

export interface ChatRequest {
    conversation_id: string;
    user_id: string;
    dialog_id: string;
    message: UserPrompt;
    user_profile: UserProfile;
    overrides?: ChatRequestOverrides;
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
};

export type Error = {
    error_str?: string;
    retry?: boolean;
    status_code?: number;
};

// Todo: Fix data_points type to string[] on the backend if that is sufficient.
export type ChatResponse = {
    connection_id: string;
    dialog_id: string;
    conversation_id: string;
    user_id: string;
    answer: Answer;
    error?: Error;
};

export type ProductResult = {
    id: string;
    name: string;
    description: string;
    summarizedDescription: string;
    imageUrl: string;
    category: string;
    attributes: string[];
};

export interface UIBotAnswerItems {
    productName: string;
    description: string;
}

export interface UIBotAnswerBody {
    introMessage: string;
    items: UIBotAnswerItems[];
}

export type UIBotMessage = {
    answer?: UIBotAnswerBody;
    results?: ProductResult[];
};
