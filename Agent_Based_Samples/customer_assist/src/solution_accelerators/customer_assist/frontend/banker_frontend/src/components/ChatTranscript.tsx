// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  fetchTranscript,
  sendWebSocketMessage,
  setUpSpeechRecognizer,
  speakText,
  TTSOptions,
} from "../api/api";
import {
  startAgentConversation,
  stopAgentConversation,
  getNextAgentMessage,
  convertRoleToUserRole,
  ConversationSimulatorMessage,
} from "../api/agent_api";
import {
  UserRole,
  InputText,
  InputImage,
  UserInput,
  TranscriptMessage as ApiTranscriptMessage,
} from "../api/models";
import * as speechsdk from "microsoft-cognitiveservices-speech-sdk";
import "./components.css";

interface TranscriptMessage {
  role: "agent" | "customer";
  text: string;
  imageUrl?: string;
}

interface ChatTranscriptProps {
  transcriptData?: ApiTranscriptMessage[];
}

const ChatTranscript: React.FC<ChatTranscriptProps> = ({ transcriptData }) => {
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState("");
  const [selectedRole, setSelectedRole] = useState<UserRole>(UserRole.ADVISOR);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isAgentMode, setIsAgentMode] = useState<boolean>(false);
  const [agentRunning, setAgentRunning] = useState<boolean>(false);
  const [speechRecognizer, setSpeechRecognizer] = useState<any>(null);
  const [isRecognizing, setIsRecognizing] = useState<boolean>(false);
  const [questionLocale, setQuestionLocale] = useState<string>("");
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [ttsVoice, setTtsVoice] = useState<string>("en-US-JennyNeural");
  const [availableVoices, setAvailableVoices] = useState<
    { name: string; locale: string; gender: string }[]
  >([]);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Interval ref for polling agent messages
  const pollIntervalRef = useRef<number | null>(null);

  // TTS management with strict sequencing
  const ttsQueue = useRef<Array<{ text: string; role: string }>>([]);
  const isSpeakingRef = useRef<boolean>(false);
  const ttsProcessorActive = useRef<boolean>(false);

  // Process TTS queue with strict sequencing
  const processTTSQueue = useCallback(async () => {
    // Only one processor should run at a time
    if (ttsProcessorActive.current) {
      console.log("TTS processor is already active, skipping...");
      return;
    }

    ttsProcessorActive.current = true;

    try {
      const { text, role } = ttsQueue.current[0]; // Peek at first item
      const voiceName =
        role === "customer"
          ? "en-US-AvaMultilingualNeural"
          : "en-US-AndrewMultilingualNeural";

      console.log("voiceName", voiceName);
      // Set UI state for speaking
      isSpeakingRef.current = true;
      setIsSpeaking(true);

      try {
        // Wait for TTS to complete before processing next item
        await speakText({
          text,
          voiceName,
          onAudioStarted: () => {
            console.log(`Started speaking: ${text.substring(0, 30)}...`);
          },
          onAudioEnded: () => {
            console.log(`Finished speaking: ${text.substring(0, 30)}...`);
            // Add a delay for 1 second before allowing next TTS
            setTimeout(() => {
              isSpeakingRef.current = false;
              setIsSpeaking(false);
              console.log("TTS finished, processing next item...");
              ttsQueue.current.shift();
              ttsProcessorActive.current = false;
            }, 3000);
          },
        });
      } catch (error) {
        console.error("TTS error:", error);
      }
    } finally {
      ttsProcessorActive.current = false;
    }
  }, []);

  // Add to TTS queue and start processor if needed
  const enqueueTTS = useCallback(
    (text: string, role: string) => {
      ttsQueue.current.push({ text, role });
      processTTSQueue();
    },
    [processTTSQueue]
  );

  // Function to handle speaking a message
  const handleSpeak = useCallback(
    (text: string, role: string) => {
      // Don't try to speak very long text
      if (text.length > 2000) {
        setError("Message is too long to speak");
        return;
      }

      enqueueTTS(text, role);
    },
    [enqueueTTS, isSpeaking]
  );

  // Convert API TranscriptMessage to component format
  const convertApiMessages = useCallback(
    (apiMessages: ApiTranscriptMessage[] | undefined): TranscriptMessage[] => {
      if (!apiMessages) return [];

      return apiMessages.map((msg) => ({
        role: msg.role === "advisor" ? "agent" : "customer",
        text: msg.text,
        imageUrl: msg.image_url || undefined,
        imageDescription: msg.image_description || undefined,
      }));
    },
    []
  );

  // Use transcriptData prop if provided, otherwise load via API
  useEffect(() => {
    if (transcriptData) {
      const convertedMessages = convertApiMessages(transcriptData);
      setMessages(convertedMessages);
      setLoading(false);
    } else {
      const loadTranscript = async () => {
        try {
          const data = (await fetchTranscript()) as TranscriptMessage[];
          setMessages(data || []);
        } catch (err: any) {
          setError(err.message || "Failed to load transcript");
        } finally {
          setLoading(false);
        }
      };

      loadTranscript();
    }
  }, [transcriptData, convertApiMessages]);

  // Scroll to bottom effect
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [messages]);

  // Handle file selection with validation
  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        const file = e.target.files[0];

        // Check if it's an image file
        if (!file.type.startsWith("image/")) {
          setError("Please select an image file");
          return;
        }

        // Check file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
          setError("Image size must be less than 5MB");
          return;
        }

        setSelectedImage(file);

        // Create preview URL
        const reader = new FileReader();
        reader.onload = () => {
          setImagePreview(reader.result as string);
        };
        reader.readAsDataURL(file);

        setError(null);
      }
    },
    []
  );

  // Clear selected image
  const clearSelectedImage = useCallback(() => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  // Trigger file input click
  const handleAttachmentButtonClick = useCallback(() => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, []);

  const handleSendMessage = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      // Check if there's a text message or an image to send
      if (newMessage.trim() || selectedImage) {
        // Map UserRole enum to the TranscriptMessage role type
        const messageRole =
          selectedRole === UserRole.ADVISOR ? "agent" : "customer";

        // Create message array to hold text and/or image inputs
        const messageInputs: (InputText | InputImage)[] = [];

        // Add text if present
        if (newMessage.trim()) {
          messageInputs.push({
            text: newMessage.trim(),
          });
        }

        // Add image if present
        if (selectedImage && imagePreview) {
          // Create a new TranscriptMessage with the image URL for local display
          const newImageMessage: TranscriptMessage = {
            role: messageRole,
            text: selectedImage.name,
            imageUrl: imagePreview,
          };

          // Update local UI immediately to show the image
          setMessages((prev) => [...prev, newImageMessage]);

          // Add image to the message inputs for sending to the server
          messageInputs.push({
            imageName: selectedImage.name,
            imageUrl: imagePreview,
          });
        } else if (newMessage.trim()) {
          // If we only have text, create a text-only message for local display
          const newTextMessage: TranscriptMessage = {
            role: messageRole,
            text: newMessage.trim(),
          };

          // Update local UI immediately to show the text
          setMessages((prev) => [...prev, newTextMessage]);
        }

        // Create UserInput object with message array
        const userInput: UserInput = {
          message: messageInputs,
        };

        // Send the message via WebSocket
        try {
          const messageId = sendWebSocketMessage(userInput, selectedRole);
          console.log("Message sent with ID:", messageId);
        } catch (error) {
          console.error("Error sending message:", error);
          setError("Failed to send message. Please try again.");
        }

        // Clear input after sending
        setNewMessage("");
        clearSelectedImage();
      }
    },
    [newMessage, selectedImage, imagePreview, selectedRole, clearSelectedImage]
  );

  const handleRoleChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      setSelectedRole(e.target.value as UserRole);
    },
    []
  );

  function estimateTTSWaitTime(text: string, wps: number = 3.5): number {
    const wordCount = text.trim().split(/\s+/).length;
    const durationInSeconds = wordCount / wps;
    return Math.round(durationInSeconds * 1000) + 2000; // in ms
  }

  // Toggle agent mode
  const toggleAgentMode = useCallback(async () => {
    try {
      if (!isAgentMode) {
        // Enable agent mode
        setIsAgentMode(true);

        // Clear any pending image selection when entering agent mode
        clearSelectedImage();
        setNewMessage("");

        const success = await startAgentConversation();

        if (success) {
          // Set agent running state - this is async and won't be reflected immediately
          setAgentRunning(true);

          // Set up continuous polling with delay between calls
          if (pollIntervalRef.current === null) {
            // Create a flag variable we can access inside the polling function
            // This is needed because the closure will have stale state references
            const isRunning = { current: true };

            const pollWithDelay = async () => {
              // Use our local reference instead of the agentRunning state
              if (!isRunning.current) {
                console.log("Agent mode disabled, stopping polling...");
                return;
              }

              try {
                console.log("Polling for new messages...");
                const messages = await getNextAgentMessage();

                // Also send each message to the websocket to ensure backend systems receive it
                for (const msg of messages) {
                  // Create message array to hold text and/or image inputs
                  const messageInputs: (InputText | InputImage)[] = [];

                  // Add text message
                  if (msg.text) {
                    // First perform TTS on the message
                    while (
                      ttsQueue.current.length > 0 ||
                      isSpeakingRef.current
                    ) {
                      console.log(
                        "Waiting for TTS to finish before enqueuing again..."
                      );
                      await new Promise((resolve) => setTimeout(resolve, 100));
                    }
                    console.log("Enqueuing TTS for message:", msg.text);
                    enqueueTTS(msg.text, msg.role);
                    messageInputs.push({ text: msg.text });
                  }

                  // Add image if present
                  if (msg.image_url) {
                    messageInputs.push({
                      imageName:
                        msg.image_description || "Image from conversation",
                      imageUrl: msg.image_url,
                    });
                  }

                  // Create UserInput from the message
                  const userInput: UserInput = {
                    message: messageInputs,
                  };

                  // Map the role from the simulator message to UserRole enum
                  const role =
                    msg.role.toLowerCase() === "advisor"
                      ? UserRole.ADVISOR
                      : UserRole.CUSTOMER;

                  // Send to websocket
                  try {
                    await sendWebSocketMessage(userInput, role);
                    console.log(
                      `Message from agent "${msg.text}" sent to websocket with role: ${role}`
                    );
                  } catch (error) {
                    console.error(
                      "Error sending agent message to websocket:",
                      error
                    );
                  }
                }

                if (messages.length > 0) {
                  console.log("New messages received:", messages);
                  // Wait for all TTS to finish (wait until queue is empty and not speaking)
                  while (ttsQueue.current.length > 0 || isSpeakingRef.current) {
                    console.log(
                      "Waiting for TTS to finish before polling again..."
                    );
                    await new Promise((resolve) => setTimeout(resolve, 100));
                  }
                  // Convert Redis queue messages to TranscriptMessage format
                  const newTranscriptMessages: TranscriptMessage[] =
                    messages.map((msg: ConversationSimulatorMessage) => ({
                      role:
                        msg.role.toLowerCase() === "advisor"
                          ? "agent"
                          : "customer",
                      text: msg.text,
                      imageUrl: msg.image_url, // Include the image URL from the simulator message
                      imageDescription: msg.image_description,
                    }));

                  // Add new messages to the transcript
                  setMessages((prev) => [...prev, ...newTranscriptMessages]);

                  // Scroll to bottom after adding new messages
                  if (transcriptRef.current) {
                    transcriptRef.current.scrollTop =
                      transcriptRef.current.scrollHeight;
                  }
                  // Wait before next poll AFTER all TTS completes
                } else {
                  console.log("No new messages received");
                  // Stop polling if no new messages
                  isRunning.current = false;
                } // Schedule next poll if our local flag is still true
                if (isRunning.current) {
                  // Calculate delay based on the last message text size
                  const lastMessage =
                    messages.length > 0
                      ? messages[messages.length - 1].text
                      : "";
                  var waitTimeMs = estimateTTSWaitTime(lastMessage);
                  // If a document is attached, use a longer wait time
                  if (lastMessage.includes("Document received")) {
                    console.log("Document received, extending wait time");
                    waitTimeMs += 5000; // Add 5 seconds for document processing
                  }
                  console.log(
                    `Scheduling next poll in ${waitTimeMs}ms based on message length`
                  );
                  setTimeout(pollWithDelay, waitTimeMs);
                }
              } catch (error) {
                console.error("Error in continuous polling:", error);
                if (isRunning.current) {
                  // Calculate a reasonable wait time even after errors
                  // Use a moderate default value since we don't have a message to base it on
                  const waitTimeMs = estimateTTSWaitTime(
                    "Error occurred, waiting before retrying"
                  ); // ~5-6 seconds
                  console.log(
                    `Error encountered, scheduling next poll in ${waitTimeMs}ms`
                  );
                  setTimeout(pollWithDelay, waitTimeMs);
                }
              }
            };

            // Store our flag reference so we can update it when stopping
            pollIntervalRef.current = window.setTimeout(() => {
              // We're using setTimeout just to store our reference object
              console.log("Starting continuous polling...");
              pollWithDelay();
            }, 0);

            // Also store the flag in the ref for cleanup
            (pollIntervalRef as any).isRunning = isRunning;
          }
        } else {
          setError("Failed to start agent conversation");
          setIsAgentMode(false);
        }
      } else {
        // Disable agent mode
        const success = await stopAgentConversation();

        // Update our local flag to stop the polling
        if (
          pollIntervalRef.current !== null &&
          (pollIntervalRef as any).isRunning
        ) {
          (pollIntervalRef as any).isRunning.current = false;
        }

        // Clear timeout reference
        if (pollIntervalRef.current !== null) {
          window.clearTimeout(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }

        setAgentRunning(false);
        setIsAgentMode(false);
      }
    } catch (error) {
      console.error("Error toggling agent mode:", error);
      setError("Failed to toggle agent mode");
    }
  }, [isAgentMode, enqueueTTS, isSpeaking]);

  // Toggle voice input
  const toggleVoiceInput = useCallback(() => {
    if (!speechRecognizer) {
      setError("Speech recognition is not initialized. Please try again.");
      return;
    }

    if (isRecognizing) {
      // Stop recognition
      speechRecognizer.stopContinuousRecognitionAsync(() => {
        console.log("Stopped recognition");
        setIsRecognizing(false);
      });
    } else {
      // Start recognition
      try {
        // Configure recognition event handlers
        speechRecognizer.recognizing = (
          s: speechsdk.SpeechRecognizer,
          e: speechsdk.SpeechRecognitionEventArgs
        ) => {
          console.log(`RECOGNIZING: Text=${e.result.text}`);
          setNewMessage(e.result.text);
          setQuestionLocale(e.result.language || "");
        };

        speechRecognizer.recognized = (
          s: speechsdk.SpeechRecognizer,
          e: speechsdk.SpeechRecognitionEventArgs
        ) => {
          if (e.result.reason === speechsdk.ResultReason.RecognizedSpeech) {
            console.log(`RECOGNIZED: Text=${e.result.text}`);
            setNewMessage(e.result.text);
            setQuestionLocale(e.result.language || "");
          } else if (e.result.reason === speechsdk.ResultReason.NoMatch) {
            console.log("NOMATCH: Speech could not be recognized.");
          }
        };

        speechRecognizer.sessionStopped = (
          s: speechsdk.SpeechRecognizer,
          e: speechsdk.SpeechRecognitionEventArgs
        ) => {
          console.log("Session stopped event.");
          speechRecognizer.stopContinuousRecognitionAsync();
          setIsRecognizing(false);
        };

        // Start continuous recognition
        speechRecognizer.startContinuousRecognitionAsync();
        setIsRecognizing(true);
      } catch (error) {
        console.error("Error starting speech recognition:", error);
        setError("Failed to start speech recognition. Please try again.");
      }
    }
  }, [speechRecognizer, isRecognizing]);

  // Initialize speech recognizer when component mounts
  useEffect(() => {
    const initializeSpeechRecognizer = async () => {
      try {
        const recognizer = await setUpSpeechRecognizer();
        setSpeechRecognizer(recognizer);
        console.log("Speech recognizer initialized successfully");
      } catch (error) {
        console.error("Error initializing speech recognizer:", error);
        setError("Failed to initialize speech recognition. Please try again.");
      }
    };

    initializeSpeechRecognizer();

    // Cleanup speech recognizer on component unmount
    return () => {
      if (speechRecognizer) {
        speechRecognizer.close();
        console.log("Speech recognizer closed");
      }
    };
  }, []);

  // Clean up interval on component unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current !== null) {
        window.clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  return (
    <div className="panel transcript-panel">
      <div className="panel-header">
        <div className="panel-title">Real-time Transcription</div>
        <div className="mode-toggle-container">
          <button
            className={`mode-toggle-button ${
              isAgentMode ? "agent-mode-active" : ""
            }`}
            onClick={toggleAgentMode}
            title={
              isAgentMode ? "Switch to manual mode" : "Switch to agent mode"
            }
          >
            {isAgentMode ? "Switch to Manual Mode" : "Switch to Agent Mode"}
          </button>
          {agentRunning && (
            <span className="agent-status">Conversation Simulator Running</span>
          )}
        </div>
        <div className="status-indicator status-active"></div>
      </div>

      {loading && <div className="panel-loading">Loading transcript...</div>}

      {error && <div className="panel-error">{error}</div>}

      {!loading && !error && (
        <>
          <div className="transcription-content" ref={transcriptRef}>
            {messages.length > 0 ? (
              messages.map((msg, index) => (
                <div key={index} className={`transcription-line ${msg.role}`}>
                  <div className="message-header">
                    <strong>
                      {msg.role === "agent" ? "Advisor" : "Customer"}:
                    </strong>
                    <button
                      className="speak-button"
                      onClick={() => handleSpeak(msg.text, msg.role)}
                      disabled={isSpeaking}
                      title="Speak this message"
                    >
                      🔊
                    </button>
                  </div>
                  <div className="message-content">
                    {msg.text}
                    {msg.imageUrl && (
                      <div className="message-image-container">
                        <img
                          src={msg.imageUrl}
                          alt={"Attached image"}
                          className="message-image"
                          title={""}
                        />
                      </div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="no-data-message">
                No messages yet. Start the conversation.
              </div>
            )}
          </div>

          {/* Image preview section */}
          {imagePreview && (
            <div className="image-preview-container">
              <img
                src={imagePreview}
                alt="Selected"
                className="image-preview"
              />
              <button
                type="button"
                className="clear-image-btn"
                onClick={clearSelectedImage}
                title="Remove image"
                aria-label="Remove image"
              >
                &times;
              </button>
            </div>
          )}

          <form onSubmit={handleSendMessage} className="banker-input-form">
            <div className="input-row">
              <select
                value={selectedRole}
                onChange={handleRoleChange}
                className="role-selector"
                aria-label="Select role"
                disabled={isAgentMode}
              >
                <option value={UserRole.ADVISOR}>Banker</option>
                <option value={UserRole.CUSTOMER}>Customer</option>
              </select>
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder={
                  isAgentMode
                    ? "Input disabled in agent mode..."
                    : "Type a message..."
                }
                className="banker-chat-input"
                aria-label="Type a message"
                disabled={isAgentMode}
              />

              {/* Hidden file input */}
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: "none" }}
                accept="image/*"
                onChange={handleFileSelect}
                aria-label="Select image"
                disabled={isAgentMode}
              />

              {/* Microphone button for voice input */}
              <button
                type="button"
                className={`banker-chat-mic ${
                  isRecognizing ? "recording" : ""
                }`}
                onClick={toggleVoiceInput}
                title={isRecognizing ? "Stop recording" : "Start voice input"}
                aria-label={
                  isRecognizing ? "Stop recording" : "Start voice input"
                }
                disabled={isAgentMode}
              >
                {isRecognizing ? "🔴" : "🎤"}
              </button>

              {/* Attachment button */}
              <button
                type="button"
                className="banker-chat-attach"
                onClick={handleAttachmentButtonClick}
                title="Attach image"
                aria-label="Attach image"
                disabled={isAgentMode}
              >
                📎
              </button>

              <button
                type="submit"
                className="banker-chat-send"
                disabled={isAgentMode || (!newMessage.trim() && !selectedImage)}
              >
                Send
              </button>
            </div>
          </form>
        </>
      )}
    </div>
  );
};

export default ChatTranscript;
