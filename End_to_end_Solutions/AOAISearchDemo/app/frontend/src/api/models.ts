export const enum ApproachType {
    Structured = "structured",
    Unstructured = "unstructured",
    ChitChat = "chit_chat"
}

export type ChatRequestOverrides = {
    semanticRanker?: boolean;
    semanticCaptions?: boolean;
    excludeCategory?: string;
    top?: number;
    temperature?: number;
    suggestFollowupQuestions?: boolean;
    classificationOverride?: ApproachType;
    vectorSearch?: boolean;
};

interface DialogRequest {
    userID: string;
    conversationID: string;
    dialogID: string;
}

export interface ChatRequest extends DialogRequest {
    dialog: string;
    overrides?: ChatRequestOverrides;
}

export type Answer = {
    formatted_answer: string;
    query_generation_prompt?: string;
    query?: string;
    query_result?: string;
};

export type ChatResponse = {
    answer: Answer;
    classification?: ApproachType;
    data_points: string[];
    show_retry?: boolean;
    suggested_classification?: ApproachType;
    error?: string;
};

export type UserProfile = {
    user_id: string;
    user_name: string;
    description: string;
    sample_questions?: string[];
};

export type ChatError = {
    retryable: boolean;
    message?: string;
};

export type UserQuestion = {
    question: string;
    classificationOverride?: ApproachType;
};

export type SearchSettings = {
    vectorization_enabled: boolean;
};
