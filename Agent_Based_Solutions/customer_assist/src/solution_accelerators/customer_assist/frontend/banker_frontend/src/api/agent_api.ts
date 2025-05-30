// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

/**
 * Agent API for conversation simulation
 * This file contains functions for interacting with the conversation simulator service
 */

import { UserRole } from "./models";

// API base URL for the conversation simulator
const CONVERSATION_SIMULATOR_URI =
  import.meta.env.VITE_CONVERSATION_SIMULATOR_URI || "http://localhost:5001";

// Import the shared currentSessionId from api.ts
import { currentSessionId as webSocketSessionId } from "./api";

// Interface for Redis queue messages returned by the conversation simulator
export interface ConversationSimulatorMessage {
  role: string; // 'advisor' or 'customer'
  text: string;
  timestamp: string;
  image_url?: string;
  image_description?: string;
}

// Session ID for the current conversation
let currentSessionId: string | null = null;

/**
 * Start a simulated conversation between an agent and customer
 * @returns Promise<boolean> - True if the conversation was successfully started
 */
export async function startAgentConversation(): Promise<boolean> {
  try {
    // Use the WebSocket session ID if available
    if (!webSocketSessionId) {
      console.warn(
        "No WebSocket session ID available. Agent conversation may not sync properly with the current session."
      );
    }

    console.log(
      `Starting agent conversation with WebSocket session ID: ${webSocketSessionId}`
    );

    const response = await fetch(`${CONVERSATION_SIMULATOR_URI}/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: webSocketSessionId, // Pass the WebSocket session ID
      }),
    });

    if (!response.ok) {
      console.error(
        `Failed to start agent mode: ${response.status} ${response.statusText}`
      );
      return false;
    }

    const data = await response.json();
    console.log("Start conversation response:", data);

    if (data.success) {
      // Store the session ID for future requests
      currentSessionId = data.session_id || webSocketSessionId;
      console.log(`Conversation started with session ID: ${currentSessionId}`);
      return true;
    } else {
      console.error("Failed to start conversation:", data.error);
      return false;
    }
  } catch (error) {
    console.error("Error starting agent conversation:", error);
    return false;
  }
}

/**
 * Stop the currently running simulated conversation
 * @returns Promise<boolean> - True if the conversation was successfully stopped
 */
export async function stopAgentConversation(): Promise<boolean> {
  if (!currentSessionId) {
    console.warn("No active conversation session to stop");
    return false;
  }

  try {
    const response = await fetch(`${CONVERSATION_SIMULATOR_URI}/stop`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ session_id: currentSessionId }),
    });

    if (!response.ok) {
      throw new Error(
        `Failed to stop agent conversation: ${response.statusText}`
      );
    }

    const data = await response.json();

    if (data.success) {
      console.log(
        `Conversation with session ID ${currentSessionId} stopped successfully`
      );

      // Cleanup the session
      await cleanupSession(currentSessionId);

      // Clear the session ID
      currentSessionId = null;

      return true;
    } else {
      console.error("Failed to stop conversation:", data.error);
      return false;
    }
  } catch (error) {
    console.error("Error stopping agent conversation:", error);
    return false;
  }
}

/**
 * Poll for new messages from the simulated conversation
 * @returns Promise<ConversationSimulatorMessage[]> - Array of new messages
 */
export async function getNextAgentMessage(): Promise<
  ConversationSimulatorMessage[]
> {
  if (!currentSessionId) {
    console.warn("No active conversation session to poll messages from");
    return [];
  }

  try {
    console.log(`Polling for messages with session ID: ${currentSessionId}`);

    // Get the next message from the conversation
    const response = await fetch(
      `${CONVERSATION_SIMULATOR_URI}/next?session_id=${currentSessionId}`
    );

    if (!response.ok) {
      console.error(
        `Failed to fetch agent messages: ${response.status} ${response.statusText}`
      );
      return [];
    }

    const data = await response.json();
    console.log("Poll response:", data);

    if (!data.success) {
      console.warn(`Poll unsuccessful: ${data.error || "Unknown error"}`);
      if (data.is_running === false) {
        console.log("Conversation has ended");
        // Cleanup the session
        await cleanupSession(currentSessionId);
        currentSessionId = null;
      }
      return [];
    }

    // If there's no message (conversation ended) or the conversation is no longer running
    if (!data.message || !data.is_running) {
      console.log("Conversation has ended or no more messages");
      // Cleanup the session
      if (currentSessionId) {
        await cleanupSession(currentSessionId);
        currentSessionId = null;
      }
      return [];
    }

    console.log(`Received message: ${JSON.stringify(data.message)}`);
    // Return the message as an array
    return [data.message];
  } catch (error) {
    console.error("Error polling agent messages:", error);
    return [];
  }
}

/**
 * Cleanup a conversation session
 * @param sessionId - The session ID to cleanup
 * @returns Promise<boolean> - True if the session was successfully cleaned up
 */
async function cleanupSession(sessionId: string): Promise<boolean> {
  try {
    const response = await fetch(`${CONVERSATION_SIMULATOR_URI}/cleanup`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
      throw new Error(`Failed to cleanup session: ${response.statusText}`);
    }

    const data = await response.json();
    return data.success || false;
  } catch (error) {
    console.error("Error cleaning up session:", error);
    return false;
  }
}

/**
 * Convert Redis role format to UserRole enum
 * @param redisRole The role string from Redis ('advisor' or 'customer')
 * @returns UserRole - The corresponding UserRole enum value
 */
export function convertRoleToUserRole(role: string): UserRole {
  if (role.toLowerCase() === "advisor") {
    return UserRole.ADVISOR;
  } else {
    return UserRole.CUSTOMER;
  }
}
