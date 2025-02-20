/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */
export const enum ApproachType {
    Structured = "structured",
    Unstructured = "unstructured",
    ChitChat = "chit_chat"
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
    overrides?: ChatRequestOverrides;
}

export type Answer = {
    answer_string: string;
    data_points?: string[];
    steps_execution?: object;
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

export enum UserGender {
    Male = "Male",
    Female = "Female",
    Other = "Other"
}

export type UserProfile = {
    id: string;
    user_name: string;
    description: string;
    gender: UserGender;
    age: number;
};

export type ChatError = {
    retryable: boolean;
    message?: string;
};

export type UserQuestion = {
    question: string;
    questionLocale?: string;
    classificationOverride?: ApproachType;
    STTOutput?: boolean;
};

export type SearchSettings = {
    vectorization_enabled: boolean;
};

export type SpeechKeyResponse = {
    token: string;
    region: string;
    received_at: Date;
};
