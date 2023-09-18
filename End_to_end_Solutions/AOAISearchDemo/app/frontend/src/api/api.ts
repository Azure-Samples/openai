import { ChatRequest, ChatResponse, SearchSettings, UserProfile } from "./models";

export class ChatResponseError extends Error {
    public retryable: boolean;

    constructor(message: string, retryable: boolean) {
        super((message = message));
        this.message = message;
        this.retryable = retryable;
    }
}

export async function chatApi(options: ChatRequest): Promise<ChatResponse> {
    const response = await fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            user_id: options.userID,
            conversation_id: options.conversationID,
            dialog_id: options.dialogID,
            dialog: options.dialog,
            overrides: {
                semantic_ranker: options.overrides?.semanticRanker,
                semantic_captions: options.overrides?.semanticCaptions,
                top: options.overrides?.top,
                temperature: options.overrides?.temperature,
                exclude_category: options.overrides?.excludeCategory,
                suggest_followup_questions: options.overrides?.suggestFollowupQuestions,
                classification_override: options.overrides?.classificationOverride,
                vector_search: options.overrides?.vectorSearch
            }
        })
    });

    const parsedResponse: ChatResponse = await response.json();
    if (response.status > 299 || !response.ok) {
        throw new ChatResponseError(parsedResponse.error ?? "An unknown error occurred.", parsedResponse.show_retry ?? false);
    }

    return parsedResponse;
}

export async function getAllUsers(): Promise<UserProfile[]> {
    const response = await fetch("/user-profiles", {
        method: "GET"
    });

    if (response.status > 299 || !response.ok) {
        throw Error("Received error response when fetching user profiles.");
    }

    const userProfiles: UserProfile[] = await response.json();

    return userProfiles;
}

export async function clearChatSession(userID: string, conversationID: string): Promise<void> {
    const response = await fetch(`/chat-sessions/${userID}/${conversationID}`, {
        method: "DELETE"
    });

    if (response.status > 299 || !response.ok) {
        throw Error(`Received error response when attemping to clear chat session: ${await response.text()}.`);
    }
}

export async function getSearchSettings(): Promise<SearchSettings> {
    const response = await fetch("/search-settings", {
        method: "GET"
    })

    if (response.status > 299 || !response.ok) {
        throw Error("Received error response when fetching search settings.");
    }

    const searchSettings: SearchSettings = await response.json();
    return searchSettings;
}

export function getCitationFilePath(citation: string): string {
    return `/content/${citation}`;
}
