/*
 *   Copyright (c) 2024 
 *   All rights reserved.
 */
import { SearchResultRetail, UIBotMessage, UserProfile } from "./models";
import { parseDescription } from "./utils";

const BACKEND_URI = import.meta.env.VITE_BACKEND_URI;

console.log(`BACKEND URI GLOBAL: ${BACKEND_URI}`);

export class ChatResponseError extends Error {
    private retryable: boolean;

    constructor(message: string, retryable: boolean = false) {
        super((message = message));
        this.message = message;
        this.retryable = retryable;
    }
}

const finalAnswerIntroductions = [
    "We've curated a personalized list of recommendations just for you",
    "Your unique set of recommendations awaits",
    "Here are some recommendations just for you",
    "Take a look at what I've uncovered for you"
];

export async function getUserProfiles(): Promise<UserProfile[]> {
    console.log(`BACKEND URI getUserProfiles function: ${BACKEND_URI}`);
    const response = await fetch(`${BACKEND_URI}/user-profiles`);

    if (response.status > 299 || !response.ok) {
        throw Error(`Received error response when attempting to fetch user profiles: ${await response.text()}.`);
    }

    return await response.json();
}

export async function clearChatSession(userId: string, conversationId: string): Promise<void> {
    const response = await fetch(`${BACKEND_URI}/chat-sessions/${userId}/${conversationId}`, {
        method: "DELETE"
    });

    if (response.status > 299 || !response.ok) {
        throw Error(`Received error response when attempting to clear chat session: ${await response.text()}.`);
    }
}
