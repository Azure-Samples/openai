/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */
import { config } from "@react-spring/web";
import { ChatRequest, ChatResponse, SearchSettings, UserProfile, SpeechKeyResponse } from "./models";

const BACKEND_URI = import.meta.env.VITE_BACKEND_URI;
const CONFIGURATION_SERVICE_URI = import.meta.env.VITE_CONFIGURATION_SERVICE_URI;

export enum ConfigID {
    ORCHESTRATOR_RUNTIME = "orchestrator_runtime",
    SEARCH_RUNTIME = "search_runtime",
    SESSION_MANAGER_RUNTIME = "session_manager_runtime"
}

export class ChatResponseError extends Error {
    public retryable: boolean;

    constructor(message: string, retryable: boolean) {
        super((message = message));
        this.message = message;
        this.retryable = retryable;
    }
}

export async function getAllUsers(): Promise<UserProfile[]> {
    const response = await fetch(`${BACKEND_URI}/user-profiles`, {
        method: "GET"
    });

    if (response.status > 299 || !response.ok) {
        throw Error("Received error response when fetching user profiles.");
    }

    const userProfiles: UserProfile[] = await response.json();

    return userProfiles;
}

export async function getUserProfiles(): Promise<UserProfile[]> {
    const response = await fetch(`${BACKEND_URI}/user-profiles`);

    if (response.status > 299 || !response.ok) {
        throw Error(`Received error response when attempting to fetch user profiles: ${await response.text()}.`);
    }

    return await response.json();
}

export async function getConfigurations(configID: ConfigID): Promise<any> {
    const response = await fetch(`${CONFIGURATION_SERVICE_URI}/configuration-service/configs/${configID}`);

    if (response.status > 299 || !response.ok) {
        throw Error(`Received error response when attempting to fetch configurations: ${await response.text()}.`);
    }

    const configurations = await response.json();
    return configurations.available_configuration_versions;
}

export async function clearChatSession(userID: string, conversationID: string): Promise<void> {
    const response = await fetch(`${BACKEND_URI}/chat-sessions/${userID}/${conversationID}`, {
        method: "DELETE"
    });

    if (response.status > 299 || !response.ok) {
        throw Error(`Received error response when attemping to clear chat session: ${await response.text()}.`);
    }
}

export async function getSearchSettings(): Promise<SearchSettings> {
    const response = await fetch(`${BACKEND_URI}/search-settings`, {
        method: "GET"
    });

    if (response.status > 299 || !response.ok) {
        throw Error("Received error response when fetching search settings.");
    }

    const searchSettings: SearchSettings = await response.json();
    return searchSettings;
}

export function getCitationFilePath(citation: string, configVersion?: string): string {
    let url = `${BACKEND_URI}/content/${citation}`;
    if (configVersion) {
        const separator = url.includes("?") ? "&" : "?";
        url += `${separator}override_version=${configVersion}`;
    }
    return url;
}

export async function getSpeechToken(): Promise<SpeechKeyResponse> {
    const response = await fetch(`${BACKEND_URI}/get-speech-token`, {
        method: "GET"
    });

    if (response.status > 299 || !response.ok) {
        throw Error("Received error response when fetching speech token.");
    }

    const response_date = await response.json();
    const token: SpeechKeyResponse = {
        token: response_date.token,
        region: response_date.region,
        received_at: new Date()
    };
    return token;
}

export async function isSpeechTokenValid(token: SpeechKeyResponse): Promise<boolean> {
    const currentTime = new Date();
    const tokenTime = new Date(token.received_at);
    return currentTime.getTime() - tokenTime.getTime() < 480000;
}

export async function getICEData(region: string, auth: string): Promise<any> {
    const response = await fetch(`https://${region}.tts.speech.microsoft.com/cognitiveservices/avatar/relay/token/v1`, {
        method: "GET",
        headers: {
            Authorization: auth
        }
    });

    return await response.json();
}
