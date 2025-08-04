// Session Manager WebSocket API client

import {
  SessionManagerRequest,
  SessionManagerResponse,
  WebSocketError,
  ChatMessage,
} from "./types";

// WebSocket configuration
const WS_URL = "ws://localhost:5000/api/query";

class SessionManagerClient {
  private websocket: WebSocket | null = null;
  private currentSessionId: string | null = null;
  private messageCallbacks: Map<
    string,
    (response: SessionManagerResponse) => void
  > = new Map();
  private reconnectCount: number = 0;
  private maxReconnectAttempts: number = 3;
  // Event handlers
  private onMessageHandler: ((message: ChatMessage) => void) | null = null;
  private onErrorHandler: ((error: string) => void) | null = null;
  private onConnectHandler: (() => void) | null = null;
  private onDisconnectHandler: (() => void) | null = null;
  private onIntermediateMessageHandler: ((message: string) => void) | null =
    null;

  /**
   * Connect to the Session Manager WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      // Generate a new session ID
      this.currentSessionId = this.generateUUID();
      const wsUrl = `${WS_URL}?session_id=${this.currentSessionId}`;

      this.websocket = new WebSocket(wsUrl);

      this.websocket.onopen = () => {
        console.log("Connected to Session Manager WebSocket");
        this.reconnectCount = 0;
        if (this.onConnectHandler) {
          this.onConnectHandler();
        }
        resolve();
      };

      this.websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
        const errorMessage = "Failed to connect to Session Manager";
        if (this.onErrorHandler) {
          this.onErrorHandler(errorMessage);
        }
        reject(new WebSocketError(errorMessage));
      };

      this.websocket.onclose = () => {
        console.log("WebSocket connection closed");
        if (this.onDisconnectHandler) {
          this.onDisconnectHandler();
        }

        // Attempt to reconnect if not intentionally closed
        if (this.reconnectCount < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectCount++;
            console.log(
              `Attempting to reconnect (${this.reconnectCount}/${this.maxReconnectAttempts})`
            );
            this.connect().catch(() => {
              if (this.onErrorHandler) {
                this.onErrorHandler(
                  "Connection lost. Please refresh the page."
                );
              }
            });
          }, 1000 * this.reconnectCount);
        }
      };

      this.websocket.onmessage = (event) => {
        try {
          const response: SessionManagerResponse = JSON.parse(event.data);
          console.log("Received response from Session Manager:", response); // Handle error responses
          if (response.error) {
            const errorMessage =
              response.error.error_str || "Unknown error occurred";
            const canRetry = response.error.retry || false;

            // Create an error chat message instead of calling onErrorHandler
            const errorChatMessage: ChatMessage = {
              sender: "bot",
              text: errorMessage,
              timestamp: Date.now(),
              error: {
                error_str: errorMessage,
                retry: canRetry,
                status_code: response.error.status_code || 500,
              },
            };

            if (this.onMessageHandler) {
              this.onMessageHandler(errorChatMessage);
            }
            return;
          } // Handle final responses by displaying them as chat messages
          if (response.answer?.is_final) {
            const chatMessage: ChatMessage = {
              sender: "bot",
              text: response.answer.answer_string || "No response received",
              timestamp: Date.now(),
              bingGroundingMetadata:
                response.answer.additional_metadata?.bing_grounding_metadata,
              images: response.answer.data_points || [],
            };

            if (this.onMessageHandler) {
              this.onMessageHandler(chatMessage);
            }
          } else if (response.answer && !response.answer.is_final) {
            // Handle intermediate messages
            if (
              this.onIntermediateMessageHandler &&
              response.answer.answer_string
            ) {
              this.onIntermediateMessageHandler(response.answer.answer_string);
            }
          }

          // Execute any registered callbacks for this dialog
          if (
            response.dialog_id &&
            this.messageCallbacks.has(response.dialog_id)
          ) {
            const callback = this.messageCallbacks.get(response.dialog_id);
            if (callback) {
              callback(response);
              this.messageCallbacks.delete(response.dialog_id);
            }
          }
        } catch (error) {
          console.error("Error processing WebSocket message:", error);
          if (this.onErrorHandler) {
            this.onErrorHandler("Error processing server response");
          }
        }
      };
    });
  }

  /**
   * Send a message to the Session Manager
   */
  sendMessage(message: string, authToken: string): string {
    if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
      throw new WebSocketError("WebSocket is not connected");
    }

    if (!this.currentSessionId) {
      throw new WebSocketError("No active session");
    }

    const dialogId = this.generateUUID();

    const request: SessionManagerRequest = {
      user_id: "anonymous",
      dialog_id: dialogId,
      message: {
        payload: [
          {
            type: "text",
            value: message,
          },
        ],
      },
      authorization: authToken,
      user_profile: {
        id: "anonymous",
        user_name: "anonymous",
        gender: "Other",
        age: 30,
        description: "No description",
        role: "customer",
      },
      additional_metadata: {},
    };

    console.log("Sending message to Session Manager:", request);
    this.websocket.send(JSON.stringify(request));

    return dialogId;
  }

  /**
   * Register a callback for a specific dialog ID
   */
  registerCallback(
    dialogId: string,
    callback: (response: SessionManagerResponse) => void
  ): void {
    this.messageCallbacks.set(dialogId, callback);
  }

  /**
   * Disconnect from the WebSocket
   */
  disconnect(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.currentSessionId = null;
    this.messageCallbacks.clear();
  }
  /**
   * Set event handlers
   */
  setEventHandlers(handlers: {
    onMessage?: (message: ChatMessage) => void;
    onError?: (error: string) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
    onIntermediateMessage?: (message: string) => void;
  }): void {
    this.onMessageHandler = handlers.onMessage || null;
    this.onErrorHandler = handlers.onError || null;
    this.onConnectHandler = handlers.onConnect || null;
    this.onDisconnectHandler = handlers.onDisconnect || null;
    this.onIntermediateMessageHandler = handlers.onIntermediateMessage || null;
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return this.websocket?.readyState === WebSocket.OPEN;
  }

  /**
   * Get current session ID
   */
  getSessionId(): string | null {
    return this.currentSessionId;
  }

  /**
   * Generate a UUID for session and dialog IDs
   */
  private generateUUID(): string {
    return crypto.randomUUID();
  }
}

// Export a singleton instance
export const sessionManagerClient = new SessionManagerClient();
