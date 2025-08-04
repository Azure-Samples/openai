import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { sessionManagerClient } from "./api/sessionManager";
import { ChatMessage } from "./api/types";
import { Citations } from "./components/Citations";
import { TextWithCitations } from "./components/TextWithCitations";
import { ImageGallery } from "./components/ImageGallery";

function App() {
  const [message, setMessage] = useState("");
  const [chatLog, setChatLog] = useState<ChatMessage[]>([]);
  const [profileOpen, setProfileOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [connectError, setConnectError] = useState<string>("");
  const [wsConnected, setWsConnected] = useState(false);
  const [intermediateMessage, setIntermediateMessage] = useState<string>("");
  const [textAnimationKey, setTextAnimationKey] = useState(0);
  const { instance, accounts } = useMsal();
  const isAuthenticated = useIsAuthenticated();
  const chatLogRef = useRef<HTMLDivElement>(null);

  const BACKEND_CLIENT_ID = process.env.REACT_APP_BACKEND_CLIENT_ID;
  const SCOPES = [
    `api://${BACKEND_CLIENT_ID}/access_as_user`,
    "openid",
    "profile",
    "offline_access",
  ];

  // Function to smoothly scroll to bottom of chat
  const scrollToBottom = () => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTo({
        top: chatLogRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  // Scroll to bottom when chat log changes
  useEffect(() => {
    scrollToBottom();
  }, [chatLog]);
  // Scroll to bottom when loading state changes (to show loading indicator)
  useEffect(() => {
    if (loading) {
      // Small delay to ensure the loading indicator is rendered
      setTimeout(scrollToBottom, 100);
    }
  }, [loading]);

  // Scroll to bottom when intermediate message changes
  useEffect(() => {
    if (intermediateMessage) {
      // Small delay to ensure the intermediate message is rendered
      setTimeout(scrollToBottom, 100);
    }
  }, [intermediateMessage]);

  // Connect to Session Manager WebSocket after authentication
  useEffect(() => {
    if (!isAuthenticated || !accounts[0]) return;

    setConnecting(true);
    setConnectError(""); // Set up event handlers for the WebSocket client
    sessionManagerClient.setEventHandlers({
      onMessage: (chatMessage: ChatMessage) => {
        setChatLog((prev) => [...prev, chatMessage]);
        setLoading(false); // Stop loading when we receive a message
        setIntermediateMessage(""); // Clear intermediate message when final answer arrives
      },
      onError: (error: string) => {
        setConnectError(error);
        setWsConnected(false);
        setLoading(false); // Stop loading on error
        setIntermediateMessage(""); // Clear intermediate message on error
      },
      onConnect: () => {
        setWsConnected(true);
        setConnecting(false);
        setConnectError("");
      },
      onDisconnect: () => {
        setWsConnected(false);
        setLoading(false); // Stop loading on disconnect
        setIntermediateMessage(""); // Clear intermediate message on disconnect
      },
      onIntermediateMessage: (message: string) => {
        setIntermediateMessage(message); // Set the latest intermediate message
        setTextAnimationKey((prev) => prev + 1); // Trigger animation by changing key
      },
    });

    // Connect to the WebSocket
    sessionManagerClient
      .connect()
      .then(() => {
        console.log("Successfully connected to Session Manager");
      })
      .catch((error) => {
        console.error("Failed to connect to Session Manager:", error);
        setConnectError("Failed to connect to Session Manager");
        setConnecting(false);
      });

    // Cleanup on unmount
    return () => {
      sessionManagerClient.disconnect();
    };
  }, [isAuthenticated, accounts]);
  const sendMessage = async () => {
    if (!isAuthenticated || !accounts[0]) {
      setChatLog((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "Please sign in to chat.",
          timestamp: Date.now(),
        },
      ]);
      return;
    }

    if (connectError || !wsConnected) {
      setChatLog((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "Please resolve connection issues before chatting.",
          timestamp: Date.now(),
        },
      ]);
      return;
    }
    if (!message.trim()) return;

    return await sendMessageInternal(message);
  };

  const sendMessageInternal = async (messageText: string) => {
    setLoading(true);
    setTextAnimationKey(0); // Reset animation key when starting new request
    const userMessage: ChatMessage = {
      sender: "user",
      text: messageText,
      timestamp: Date.now(),
    };
    setChatLog((prev) => [...prev, userMessage]);

    try {
      // Get the auth token
      const tokenResp = await instance.acquireTokenSilent({
        scopes: SCOPES,
        account: accounts[0],
      }); // Send message through WebSocket
      const dialogId = sessionManagerClient.sendMessage(
        messageText,
        tokenResp.accessToken
      );
      // Register a callback to handle special error cases
      sessionManagerClient.registerCallback(dialogId, (response) => {
        if (response.error) {
          setLoading(false); // Stop loading on error
          const error = response.error; // Store error reference to avoid null checks
          if (error.error_str === "consent_required") {
            // Handle consent_required by adding it to chat log with special error type
            setChatLog((prev) => [
              ...prev,
              {
                sender: "bot",
                text: "Permissions are missing to access Databricks.",
                timestamp: Date.now(),
                error: {
                  error_str: "consent_required",
                  retry: false,
                  status_code: 403,
                },
              },
            ]);
          } else {
            setChatLog((prev) => [
              ...prev,
              {
                sender: "bot",
                text: `Error: ${error.error_str || "Unknown error"}`,
                timestamp: Date.now(),
                error: {
                  error_str: error.error_str,
                  retry: error.retry || false,
                  status_code: error.status_code || 500,
                },
              },
            ]);
          }
        }
      });
    } catch (err) {
      console.error("Error sending message:", err);
      setLoading(false); // Stop loading on error
      setChatLog((prev) => [
        ...prev,
        {
          sender: "bot",
          text: "Error: Could not send message to server.",
          timestamp: Date.now(),
        },
      ]);
    }

    setMessage("");
  };

  const handleLogin = () => {
    instance.loginPopup({ scopes: SCOPES });
  };

  const handleLogout = () => {
    instance.logoutPopup();
  };
  const user =
    isAuthenticated && accounts[0]
      ? {
          name: accounts[0].name,
          email: accounts[0].username,
        }
      : null;
  const BotFluentIcon = <span className="bot-avatar">SA</span>;

  const getUserInitials = (name?: string) => {
    if (!name) return "U";
    const parts = name.split(" ");
    return parts.length > 1
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : parts[0][0].toUpperCase();
  };
  const formatTime = (ts: number) => {
    const date = new Date(ts);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };
  // Sign-in page component
  const SignInPage = () => (
    <div className="signin-page">
      <div className="signin-container">
        <div className="signin-header">
          <h1 className="signin-title">Sales Analyst AI Agent</h1>
          <h1 className="signin-subtitle">
            Microsoft CoreAI Solution Accelerator
          </h1>
          <h1 className="signin-flavortext">
            This AI agent analyzes sales and revenue trends to identify
            prescriptive insights & sales improvement opportunities - Empowering
            business leaders in decision-making.
          </h1>
          <h1 className="signin-flavortext">
            Built using Semantic Kernel and enabled with Enterprise Security:
            featuring Azure AI Foundry, Grounding with Bing Search, AI Content
            safety & the Azure Databricks connector.
          </h1>
        </div>
        <div className="signin-card">
          <h2 className="signin-card-title">Sign In to Sales Analyst</h2>
          <p className="signin-card-description">
            Sign in using Microsoft Entra ID Single Sign On.{" "}
            <a
              href="https://learn.microsoft.com/en-us/entra/identity/"
              className="signin-learn-more"
              target="_blank"
              rel="noopener noreferrer"
            >
              Learn more
            </a>
          </p>{" "}
          <button className="signin-button" onClick={handleLogin}>
            Continue with Microsoft Entra ID
          </button>
          <p className="signin-footer">
            Contact your site administrator to request access.
          </p>
        </div>
      </div>
    </div>
  );
  return (
    <div className="App">
      {!isAuthenticated ? (
        <SignInPage />
      ) : (
        <>
          {" "}
          <div className="top-bar">
            <div className="app-title compact-header-text">
              Sales Analyst AI Agent - Microsoft CoreAI Solution Accelerator
            </div>
            <div className="header-actions">
              <div className="profile-section">
                <span
                  className="user-avatar"
                  onClick={() => setProfileOpen(true)}
                >
                  {getUserInitials(user?.name)}
                </span>
                {profileOpen && user && (
                  <div
                    className="profile-popup"
                    onClick={() => setProfileOpen(false)}
                  >
                    <div
                      className="profile-popup-content"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <span className="user-avatar profile-avatar-large">
                        {getUserInitials(user.name)}
                      </span>
                      <div className="profile-name">{user.name}</div>
                      <div className="profile-email">{user.email}</div>
                      <button
                        className="signout-btn compact-button"
                        onClick={handleLogout}
                      >
                        Sign Out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="main-content">
            <div className="left-pane">
              {" "}
              <div className="card">
                <div className="section-header compact-header-text">Chat</div>{" "}
                {/* Show spinner while connecting */}
                {connecting && (
                  <div className="connecting-message">
                    <span className="spinner"></span> Connecting to Session
                    Manager...
                  </div>
                )}
                {/* Show consent error if present */}
                {connectError === "consent_required" && (
                  <div className="consent-error">
                    Permissions are missing to access Databricks.
                    <br />
                    <a
                      href={`https://login.microsoftonline.com/${process.env.REACT_APP_TENANT_ID}/oauth2/v2.0/authorize?client_id=${process.env.REACT_APP_BACKEND_CLIENT_ID}&response_type=code&redirect_uri=http://localhost:5000/consent-callback&response_mode=query&scope=2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default&prompt=consent`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <button className="send-btn compact-button consent-button">
                        Grant Databricks Permission
                      </button>
                    </a>
                  </div>
                )}                {/* Show other connection errors */}
                {connectError && connectError !== "consent_required" && (
                  <div className="connection-error">{connectError}</div>
                )}{" "}
                <div className="chat-log" ref={chatLogRef}>
                  {chatLog.map((entry, index) => (
                    <div
                      key={index}
                      className={`chat-msg ${entry.sender} fade-in`}
                    >
                      <div className="chat-msg-row">
                        {entry.sender === "user" ? (
                          <span className="user-avatar">
                            {getUserInitials(user?.name)}
                          </span>
                        ) : (
                          BotFluentIcon
                        )}{" "}
                        <div
                          className={`chat-bubble-content ${
                            entry.sender === "bot" && entry.error
                              ? "error-bubble"
                              : ""
                          }`}
                        >
                          {entry.sender === "bot" && entry.error && (
                            <div className="error-label">Error</div>
                          )}
                          <div className="chat-msg-text compact-message-text">
                            {entry.sender === "bot" ? (
                              <TextWithCitations
                                text={entry.text}
                                bingGroundingMetadata={
                                  entry.bingGroundingMetadata
                                }
                              />
                            ) : (
                              entry.text
                            )}
                          </div>
                          {entry.sender === "bot" &&
                            entry.images &&
                            entry.images.length > 0 && (
                              <ImageGallery images={entry.images} />
                            )}{" "}
                          {entry.sender === "bot" &&
                            entry.bingGroundingMetadata && (
                              <div className="citations-container">
                                <Citations
                                  bingGroundingMetadata={
                                    entry.bingGroundingMetadata
                                  }
                                  messageText={entry.text}
                                />{" "}
                              </div>
                            )}{" "}
                          {/* Show consent button for consent_required errors */}
                          {entry.sender === "bot" &&
                            entry.error &&
                            entry.error.error_str === "consent_required" && (
                              <div className="consent-button-container">
                                <a
                                  href={`https://login.microsoftonline.com/${process.env.REACT_APP_TENANT_ID}/oauth2/v2.0/authorize?client_id=${process.env.REACT_APP_BACKEND_CLIENT_ID}&response_type=code&redirect_uri=http://localhost:5000/consent-callback&response_mode=query&scope=2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default&prompt=consent`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  <button className="send-btn compact-button consent-button">
                                    Grant Databricks Permission
                                  </button>
                                </a>
                              </div>
                            )}
                          <div className="chat-msg-meta">
                            {formatTime(entry.timestamp)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}{" "}
                  {loading && (
                    <div className="chat-msg bot fade-in">
                      <div className="chat-msg-row">
                        {BotFluentIcon}
                        <div className="chat-bubble-content">
                          <div className="loading-indicator">
                            <span className="spinner"></span>
                            <span
                              key={textAnimationKey}
                              className="loading-text fade-in"
                            >
                              {intermediateMessage || "Agent is working..."}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>{" "}
                <div className="chat-input-row">
                  {" "}
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Ask me about sales data, trends, or analytics..."
                    className="chat-input compact-input"
                    onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                    disabled={
                      !isAuthenticated ||
                      loading ||
                      connecting ||
                      !!connectError ||
                      !wsConnected
                    }
                  />
                  <button
                    onClick={sendMessage}
                    className="send-btn compact-button"
                    disabled={
                      !isAuthenticated ||
                      loading ||
                      connecting ||
                      !!connectError ||
                      !wsConnected
                    }
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default App;
