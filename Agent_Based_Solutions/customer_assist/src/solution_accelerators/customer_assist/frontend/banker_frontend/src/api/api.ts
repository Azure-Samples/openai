// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import { v4 as uuidv4 } from "uuid";
import {
  ChatRequest,
  ChatResponse,
  ChatResponseError,
  InputImage,
  InputProduct,
  InputText,
  LoanApplicationForm,
  PayloadType,
  TranscriptMessage,
  UserGender,
  UserInput,
  UserPromptPayload,
  UserRole,
  InsightsData,
  SpeechKeyResponse,
} from "./models";

import * as speechsdk from "microsoft-cognitiveservices-speech-sdk";

export interface WebSocketResponse {
  type: "TRANSCRIPT" | "INSIGHTS" | "FORM_UPDATE" | "ERROR";
  data: any;
  message?: string;
}

export class WebSocketError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WebSocketError";
  }
}

const BACKEND_URI = import.meta.env.VITE_BACKEND_URI || "http://localhost:5000";
const WS_URL = `${BACKEND_URI}/api/query`;

const SPEECH_LOCALES = import.meta.env.VITE_SPEECH_INPUT_LOCALES.split(",");

let websocket: WebSocket | null = null;
let reconnectCount = 0;
let messageCallbacks: Map<string, (data: any) => void> = new Map();
// Store the session ID so it can be used by other functions
export let currentSessionId: string | null = null;

export async function getSpeechToken(): Promise<SpeechKeyResponse> {
  const response = await fetch(`${BACKEND_URI}/get-speech-token`, {
    method: "GET",
  });

  if (response.status > 299 || !response.ok) {
    throw Error("Received error response when fetching speech token.");
  }

  const response_date = await response.json();
  const token: SpeechKeyResponse = {
    token: response_date.token,
    region: response_date.region,
    received_at: new Date(),
  };
  return token;
}

export async function isSpeechTokenValid(
  token: SpeechKeyResponse
): Promise<boolean> {
  const currentTime = new Date();
  const tokenTime = new Date(token.received_at);
  return currentTime.getTime() - tokenTime.getTime() < 480000;
}

const getSpeechTokenLocal = async () => {
  const token = localStorage.getItem("speechToken");
  if (token) {
    const tokenObj: SpeechKeyResponse = JSON.parse(token);
    if (await isSpeechTokenValid(tokenObj)) {
      return tokenObj;
    }
  }

  const newToken = await getSpeechToken();
  localStorage.setItem("speechToken", JSON.stringify(newToken));
  return newToken;
};

export async function setUpSpeechRecognizer() {
  const tokenObj = await getSpeechTokenLocal();
  const speechConfig = speechsdk.SpeechConfig.fromAuthorizationToken(
    tokenObj.token,
    tokenObj.region
  );
  const audioConfig = speechsdk.AudioConfig.fromDefaultMicrophoneInput();

  var recognizer: speechsdk.SpeechRecognizer;
  console.log("SPEECH_LOCALES: ", SPEECH_LOCALES);

  if (SPEECH_LOCALES.length === 0) {
    speechConfig.speechRecognitionLanguage = "en-US";
    recognizer = new speechsdk.SpeechRecognizer(speechConfig, audioConfig);
  } else if (SPEECH_LOCALES.length === 1) {
    speechConfig.speechRecognitionLanguage = SPEECH_LOCALES[0];
    recognizer = new speechsdk.SpeechRecognizer(speechConfig, audioConfig);
  } else {
    var autoDetectSourceLanguageConfig =
      speechsdk.AutoDetectSourceLanguageConfig.fromLanguages(SPEECH_LOCALES);
    recognizer = speechsdk.SpeechRecognizer.FromConfig(
      speechConfig,
      autoDetectSourceLanguageConfig,
      audioConfig
    );
  }

  return recognizer;
}

export function connectWebSocket(
  onTranscriptUpdate: (data: TranscriptMessage[]) => void,
  onInsightsUpdate: (data: InsightsData) => void,
  onFormUpdate: (data: LoanApplicationForm) => void,
  onError: (error: string) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const connectionID = crypto.randomUUID();
    currentSessionId = connectionID; // Store the session ID
    const wsUrl = `${WS_URL}?session_id=${connectionID}`;
    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      console.log("Connected to WebSocket!");
      reconnectCount = 0;
      resolve();
    };

    websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
      onError("Failed to connect to server");
      reject(new WebSocketError("Connection failed"));
    };

    websocket.onclose = () => {
      console.log("WebSocket connection closed");
      if (reconnectCount < 2) {
        setTimeout(() => {
          reconnectCount++;
          connectWebSocket(
            onTranscriptUpdate,
            onInsightsUpdate,
            onFormUpdate,
            onError
          )
            .then(resolve)
            .catch(reject);
        }, 1000);
      } else {
        onError("Connection lost. Please refresh the page.");
        reject(new WebSocketError("Connection lost"));
      }
    };

    websocket.onmessage = (event) => {
      try {
        // Process the incoming message as a ChatResponse type
        const response: ChatResponse = JSON.parse(event.data);
        console.log("Received ChatResponse:", response);

        // Check for error first
        if (response.error) {
          onError(response.error.error_str || "An error occurred");
          return;
        }

        // Extract data from additional_metadata
        const metadata = response.answer?.additional_metadata;
        if (metadata) {
          // Process transcript if available
          if (metadata.transcript) {
            onTranscriptUpdate(metadata.transcript);
          }

          // Process missing_fields directly if available
          if (metadata.missing_fields) {
            console.log(
              "Processing direct missing_fields:",
              metadata.missing_fields
            );
          }

          // Process insights if available
          if (metadata.insights) {
            try {
              // Parse the insights JSON string to object
              const parsedInsights =
                typeof metadata.insights === "string"
                  ? JSON.parse(metadata.insights)
                  : metadata.insights;

              // Create a complete insights object with all available data
              const completeInsights = {
                advisorInsights: {
                  // Use directly available missing_fields or parse from insights
                  missing_fields:
                    metadata.missing_fields ||
                    parsedInsights.missing_fields ||
                    [],
                  next_question: parsedInsights.next_question || "",
                  document_verification_insights:
                    parsedInsights.document_verification_insights || "",
                  document_verification_status:
                    parsedInsights.document_verification_status || "",
                  // Use loan_policy_insights if available
                  loan_policy_insights: parsedInsights.loan_policy_insights ||
                    metadata.loan_policy_insights || {
                      max_loan_amount: "",
                      min_loan_term: "",
                      max_loan_term: "",
                      min_interest_rate: "",
                      max_interest_rate: "",
                      policy_summary: "",
                    },
                },
                sentimentAnalysis: metadata.sentiment_analysis
                  ? typeof metadata.sentiment_analysis === "string"
                    ? JSON.parse(metadata.sentiment_analysis)
                    : metadata.sentiment_analysis
                  : {
                      sentiment: "Neutral",
                      reasoning: "No sentiment analysis available",
                    },
                postCallAnalysis: metadata.post_call_analysis
                  ? typeof metadata.post_call_analysis === "string"
                    ? JSON.parse(metadata.post_call_analysis)
                    : metadata.post_call_analysis
                  : { next_steps: [], summary: "" },
              };

              console.log("Parsed complete insights:", completeInsights);
              onInsightsUpdate(completeInsights);
            } catch (error) {
              console.error("Error parsing insights JSON:", error);
            }
          }

          // Process form data if available
          if (metadata.form_data) {
            try {
              // Parse the form_data JSON string to object
              const parsedFormData =
                typeof metadata.form_data === "string"
                  ? JSON.parse(metadata.form_data)
                  : metadata.form_data;

              onFormUpdate(parsedFormData);
            } catch (error) {
              console.error("Error parsing form_data JSON:", error);
            }
          }
        }

        // Process any registered callbacks for specific message IDs
        if (response.dialog_id && messageCallbacks.has(response.dialog_id)) {
          const callback = messageCallbacks.get(response.dialog_id);
          if (callback) {
            callback(response);
            messageCallbacks.delete(response.dialog_id);
          }
        }
      } catch (error) {
        console.error("Error processing WebSocket message:", error);
        onError("Error processing server message");
      }
    };
  });
}

export function disconnectWebSocket() {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.close();
  }
}

// Helper function to get Base64 data from a URL with proper formatting
const getBase64 = async (url: string): Promise<string> => {
  const response = await fetch(url);
  const blob = await response.blob();
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      // Get the base64 string and properly format it
      const base64String = reader.result as string;
      // Extract only the base64 data part, removing the prefix if it exists
      const formattedBase64 = base64String.includes("base64,")
        ? base64String.split("base64,")[1]
        : base64String;
      resolve(formattedBase64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};

// Helper function to convert user input to UserPromptPayload
const convertToUserPromptPayload = async (
  message: (InputText | InputImage | InputProduct)[]
): Promise<UserPromptPayload[]> => {
  const payloads: UserPromptPayload[] = [];

  for (const input of message) {
    if ("text" in input) {
      // InputText
      const textInput = input as InputText;
      payloads.push({
        type: PayloadType.Text,
        value: textInput.text,
      });
    } else if ("imageUrl" in input && "imageName" in input) {
      // InputImage
      const imageInput = input as InputImage;
      // Convert imageUrl to Base64 if required
      const base64 = await getBase64(imageInput.imageUrl);
      payloads.push({
        type: PayloadType.Image,
        value: base64,
      });
    }
  }
  return payloads;
};

export async function sendWebSocketMessage(
  userInput: UserInput | null,
  role: UserRole,
  additionalMetadata?: Record<string, any>
) {
  try {
    const dialog_id = uuidv4();

    // Create the base request
    const request: ChatRequest = {
      user_id: "anonymous",
      dialog_id: dialog_id,
      message: userInput
        ? { payload: await convertToUserPromptPayload(userInput.message) }
        : { payload: [] },
      user_profile: {
        id: "anonymous",
        user_name: "anonymous",
        gender: UserGender.Other,
        age: 30,
        description: "No description",
        role: role,
      },
      additional_metadata: {},
    };

    if (additionalMetadata) {
      // Add additional metadata to the request
      console.log("Adding additional metadata:", additionalMetadata);
      request.additional_metadata = additionalMetadata;
    }

    // Send the request over the WebSocket
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify(request));
      return dialog_id;
    } else {
      console.error("WebSocket is not open");
      throw new Error("WebSocket connection is not open");
    }
  } catch (e) {
    if (e instanceof ChatResponseError) {
      console.log("ChatResponseError:", e.message);
    } else if (e instanceof Error) {
      console.error("Error:", e.message);
    }
    throw e;
  }
}

export function registerCallback(
  messageId: string,
  callback: (data: any) => void
) {
  messageCallbacks.set(messageId, callback);
}

export async function submitLoanApplication(form: LoanApplicationForm) {
  // Real API implementation using WebSocket
  return new Promise((resolve, reject) => {
    const dialogId = crypto.randomUUID();
    const success = true; // TODO: Implement WebSocket message sending

    if (!success) {
      reject(new Error("WebSocket is not connected"));
      return;
    }
    // Set a timeout in case the callback never gets called
    setTimeout(() => {
      if (messageCallbacks.has(dialogId)) {
        messageCallbacks.delete(dialogId);
        reject(new Error("Request timed out"));
      }
    }, 10000);
  });
}

export async function fetchTranscript() {
  // Real API implementation using WebSocket
  return new Promise((resolve, reject) => {
    const dialogId = crypto.randomUUID();
    const success = true; // TODO: Implement WebSocket message sending

    if (!success) {
      reject(new Error("WebSocket is not connected"));
      return;
    }

    registerCallback(dialogId, (response: ChatResponse) => {
      if (response.error) {
        reject(new Error(response.error.error_str || "Unknown error"));
      } else {
        resolve(response.answer?.additional_metadata?.transcript);
      }
    });

    // Set a timeout in case the callback never gets called
    setTimeout(() => {
      if (messageCallbacks.has(dialogId)) {
        messageCallbacks.delete(dialogId);
        reject(new Error("Request timed out"));
      }
    }, 5000);
  });
}

// Text-to-Speech utility functions
export interface TTSOptions {
  text: string;
  voiceName?: string;
  language?: string;
  pitch?: number;
  rate?: number;
  onAudioStarted?: () => void;
  onAudioEnded?: () => void;
}

export async function speakText(options: TTSOptions): Promise<void> {
  const tokenObj = await getSpeechTokenLocal();
  const speechConfig = speechsdk.SpeechConfig.fromAuthorizationToken(
    tokenObj.token,
    tokenObj.region
  );

  // Set the voice based on options or use default
  if (options.voiceName) {
    speechConfig.speechSynthesisVoiceName = options.voiceName;
  } else if (options.language) {
    // Use just the language code to get a default voice for that language
    speechConfig.speechSynthesisLanguage = options.language;
  } else {
    // Default voice - female, English US
    console.log("Using default voice");
    speechConfig.speechSynthesisVoiceName = "en-US-JennyNeural";
  }

  // Create the synthesizer
  const synthesizer = new speechsdk.SpeechSynthesizer(speechConfig);

  // Use SSML if we need to specify pitch/rate
  let textToSpeak = options.text;
  return new Promise((resolve, reject) => {
    synthesizer.speakTextAsync(
      textToSpeak,
      (result) => {
        if (
          result.reason === speechsdk.ResultReason.SynthesizingAudioCompleted
        ) {
          options.onAudioEnded?.();
        } else {
          reject(new Error(result.errorDetails));
        }
        synthesizer.close();
      },
      (error) => {
        reject(error);
        synthesizer.close();
      }
    );
  });
}
