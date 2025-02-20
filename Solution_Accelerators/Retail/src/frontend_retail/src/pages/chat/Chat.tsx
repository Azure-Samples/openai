import styles from "./Chat.module.css";

import React from "react";
import { useRef, useState, useEffect } from "react";
import { Panel, PanelType, ChoiceGroup, Checkbox, IChoiceGroupOption } from "@fluentui/react";
import { Person24Regular, Settings24Regular, BuildingShopRegular } from "@fluentui/react-icons";
import { v4 as uuidv4 } from "uuid";
import { parseDescription } from "../../api/utils";

import {
    ChatResponseError,
    UserInput,
    ChatRequest,
    UIBotMessage,
    InputText,
    InputImage,
    UserPromptPayload,
    PayloadType,
    ProductResult,
    InputProduct,
    UserProfile,
    UserGender,
    ChatResponse,
    SearchResultRetail
} from "../../api";
import { BotChatMessage, BotChatMessageLoading } from "../../components/BotChatMessage";
import { QuestionInput } from "../../components/QuestionInput";
import { UserChatMessage } from "../../components/UserChatMessage";
import { ProductDetails } from "../../components/ProductDetails";
import { TopBarButton } from "../../components/TopBarButton";
import { ErrorToast } from "../../components/ErrorToast";
import { useMsal } from "@azure/msal-react";

const CHAT_WS_URL = import.meta.env.VITE_BACKEND_URI + "/ws/chat";

type Props = {
    userProfiles: UserProfile[];
};

const Chat = ({ userProfiles }: Props) => {
    const [isUserPanelOpen, setIsUserPanelOpen] = useState(false);
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const reconnectCount = useRef<number>(0);

    const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);
    const chatMessageStream = useRef<HTMLDivElement | null>(null);

    const [conversationID, setConversationID] = useState<string>();

    const [lastUserInput, setLastUserInput] = useState<UserInput | undefined>(undefined);
    const [isBotResponseLoading, setIsBotResponseLoading] = useState<boolean>(false);
    const [botResponseError, setBotResponseError] = useState<ChatResponseError | undefined>();

    const [isContentSafetyEnabled, setIsContentSafetyEnabled] = useState<boolean>(true);

    const [searchResultDetailsOpened, setSearchResultDetailsOpened] = useState<ProductResult | null>(null);

    const [dialog, setDialog] = useState<
        {
            dialog_id: string;
            user_question: UserInput;
            intermediate_responses: ChatResponse[];
            final_response: ChatResponse | undefined;
            error: ChatResponse | undefined;
        }[]
    >([]);

    const [checkedResults, setCheckedResults] = useState<string[]>([]);

    const addSearchResultToInput = useRef<((result: ProductResult) => void) | undefined>(undefined);
    const removeSearchResultFromInput = useRef<((result: ProductResult) => void) | undefined>(undefined);

    const [selectedUser, setSelectedUser] = useState<UserProfile>();

    const [isConnectingToChat, setIsConnectingToChat] = useState<boolean>(true);
    const [websocket, setWebsocket] = useState<WebSocket | null>(null);
    const [websocketError, setWebsocketError] = useState<string | null>(null);

    const { instance, accounts } = useMsal();

    useEffect(() => {
        connectToChat();
    }, []);

    useEffect(() => {
        setConversationID(uuidv4());

        if (userProfiles.length > 0) {
            setSelectedUser(userProfiles[0]);
        }
    }, [userProfiles]);

    useEffect(() => {
        if (!chatMessageStream.current) return;

        // Scroll to bottom of chat when the chat window is resized
        const resizeObserver = new ResizeObserver(() => {
            scrollToBottom();
        });

        resizeObserver.observe(chatMessageStream.current);

        // Cleanup on unmount
        return () => {
            resizeObserver.disconnect();
        };
    }, [dialog]);

    useEffect(() => scrollToBottom(), [isBotResponseLoading]);

    useEffect(() => {
        if (lastUserInput) {
            sendMessage(lastUserInput);
        }
    }, [lastUserInput]);

    useEffect(() => chatMessageStreamEnd.current?.scrollIntoView({ behavior: "smooth" }), [dialog]);

    const connectToChat = async () => {
        setIsConnectingToChat(true);
        setWebsocketError(null);

        const connectionID = uuidv4();
        const scenario = "retail";
        const wsUrl = `${CHAT_WS_URL}?connection_id=${connectionID}&scenario=${scenario}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log("Connected to chat!");
            setWebsocket(ws);
            setIsConnectingToChat(false);
            reconnectCount.current = 0; // Reset reconnect count on successful connection
        };

        ws.onerror = error => {
            console.error("WebSocket error: ", error);
            setWebsocket(null);
            setWebsocketError("Failed to connect to chat");
            setIsConnectingToChat(false);
            clearAllPendingDialogs();

            if (reconnectCount.current < 5) {
                setTimeout(connectToChat, 1000);
                reconnectCount.current += 1;
            }
        };

        ws.onclose = () => {
            console.log("Disconnected from chat!");
            console.log("Retrycount: " + reconnectCount.current);
            setWebsocket(null);
            setWebsocketError("Disconnected from chat");
            setIsConnectingToChat(false);
            clearAllPendingDialogs();

            if (reconnectCount.current < 5) {
                setTimeout(connectToChat, 1000);
                reconnectCount.current += 1;
            }
        };

        ws.onmessage = async event => {
            const result: ChatResponse = JSON.parse(event.data);
            console.log("Received message: ", result);

            setDialog(prevDialog => {
                const dialogIndex = prevDialog.findIndex(dialogItem => dialogItem.dialog_id === result.dialog_id);

                if (dialogIndex !== -1) {
                    const updatedDialog = prevDialog[dialogIndex];

                    if (result.error) {
                        // Error response received
                        prevDialog[dialogIndex] = {
                            dialog_id: result.dialog_id,
                            user_question: updatedDialog.user_question,
                            intermediate_responses: updatedDialog.intermediate_responses,
                            final_response: updatedDialog.final_response,
                            error: result
                        };
                        setIsBotResponseLoading(false); // Stop loading on error
                    } else if (result.answer?.answer_string != undefined && result.answer?.steps_execution != undefined) {
                        // Final response received
                        prevDialog[dialogIndex] = {
                            dialog_id: result.dialog_id,
                            user_question: updatedDialog.user_question,
                            intermediate_responses: updatedDialog.intermediate_responses,
                            final_response: result,
                            error: updatedDialog.error
                        };
                        setIsBotResponseLoading(false); // Stop loading on final response
                    } else {
                        // Intermediate response received
                        prevDialog[dialogIndex] = {
                            dialog_id: result.dialog_id,
                            user_question: updatedDialog.user_question,
                            intermediate_responses: [...updatedDialog.intermediate_responses, result],
                            final_response: updatedDialog.final_response,
                            error: updatedDialog.error
                        };
                    }
                }
                return [...prevDialog];
            });
        };
    };

    const clearAllPendingDialogs = () => {
        setDialog(prevDialog => {
            const updatedDialog = prevDialog.map(dialogItem => {
                if (dialogItem.final_response === undefined) {
                    return {
                        ...dialogItem,
                        dialog_id: uuidv4(), // Generate new dialog id to prevent further processing
                        error: { error: { error_str: "An error occured" }, dialog_id: dialogItem.dialog_id } as ChatResponse
                    };
                }
                return dialogItem;
            });
            return updatedDialog;
        });
        setIsBotResponseLoading(false); // Stop loading when fast-failing
    };

    // Add the getBase64 function if you need to convert image URLs to Base64
    const getBase64 = async (url: string): Promise<string> => {
        const response = await fetch(url);
        const blob = await response.blob();
        return new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => {
                resolve(reader.result as string);
            };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    };

    // Helper function to convert user input to UserPromptPayload
    const convertToUserPromptPayload = async (message: (InputText | InputImage | InputProduct)[]): Promise<UserPromptPayload[]> => {
        const payloads: UserPromptPayload[] = [];

        for (const input of message) {
            if ("text" in input) {
                // InputText
                const textInput = input as InputText;
                payloads.push({
                    type: PayloadType.Text,
                    value: textInput.text
                });
            } else if ("imageUrl" in input && "imageName" in input) {
                // InputImage
                const imageInput = input as InputImage;
                // Convert imageUrl to Base64 if required
                const base64 = await getBase64(imageInput.imageUrl);
                payloads.push({
                    type: PayloadType.Image,
                    value: base64
                });
            } else if ("articleId" in input && "productName" in input && "productImageUrl" in input) {
                // InputProduct
                const productInput = input as InputProduct;
                payloads.push({
                    type: PayloadType.Product,
                    value: productInput.articleId
                });
            }
        }
        return payloads;
    };

    const convertBotResponseToUIBotMessage = (botResponse: ChatResponse): UIBotMessage => {
        const cognitiveSearchOutput = botResponse.answer?.steps_execution?.cognitiveSearchSkill?.trimmed_search_results;
        const finalAnswer = botResponse.answer?.answer_string;

        var searchResults: SearchResultRetail[] = [];
        if (cognitiveSearchOutput) {
            // Search results are returned in an array of arrays, so we need to flatten them
            // showing items in order of recommendation:
            // example: [1st item recom1, 1st item recom2, 2nd item recom1, 2nd item recom2]
            searchResults = cognitiveSearchOutput;
        }

        if (finalAnswer && !cognitiveSearchOutput) {
            const botMessage: UIBotMessage = {
                answer: {
                    introMessage: finalAnswer,
                    items: []
                },
                results: []
            };
            return botMessage;
        } else {
            const botMessage: UIBotMessage = {
                answer: {
                    introMessage: finalAnswer || "Here are some products that match your search",
                    items: searchResults.map(item => ({
                        productName: item.productName || item.articleId!,
                        description: item.summarizedDescription || item.detailDescription
                    }))
                },
                results: searchResults.map(searchResult => {
                    // TODO: We'll try to parse the description and attributes from the description field,
                    // but ideally we'd have a separate field for each of these.
                    // Change this once the search index and backend are updated.
                    const [description, attributes] = parseDescription(searchResult.detailDescription);

                    // @ts-ignore avoid breaking website after index renaming
                    return {
                        id: searchResult.articleId! || searchResult.productName,
                        name: searchResult.productName || searchResult.articleId!,
                        summarizedDescription: searchResult.summarizedDescription || searchResult.detailDescription,
                        description: searchResult.summarizedDescription || description,
                        imageUrl: searchResult.imageUrl || searchResult.image_sas_url!,
                        category: searchResult.category,
                        attributes: attributes
                    };
                })
            };
            return botMessage;
        }
    };

    const sendMessage = async (userInput: UserInput) => {
        botResponseError && setBotResponseError(undefined);
        setIsBotResponseLoading(true);

        try {
            const dialog_id = uuidv4();
            const payloads = await convertToUserPromptPayload(userInput.message);

            const request: ChatRequest = {
                conversation_id: getConversationID() || "",
                user_id: selectedUser ? selectedUser.id : "anonymous",
                dialog_id: dialog_id,
                message: { payload: payloads },
                user_profile: {
                    id: selectedUser ? selectedUser.id : "anonymous",
                    user_name: selectedUser ? selectedUser.user_name : "anonymous",
                    gender: selectedUser ? selectedUser.gender : UserGender.Other,
                    age: selectedUser ? selectedUser.age : 30,
                    description: selectedUser ? selectedUser.description : "No description"
                },
                overrides: {
                    session_manager_runtime: {
                        check_safe_image_content: isContentSafetyEnabled
                    }
                }
            };

            // Send the request over the WebSocket
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify(request));

                // Update the dialog state with the user's message
                setDialog(prevDialog => [
                    ...prevDialog,
                    {
                        dialog_id: dialog_id,
                        user_question: userInput,
                        intermediate_responses: [],
                        final_response: undefined,
                        error: undefined
                    }
                ]);
            } else {
                console.error("WebSocket is not open");
                setBotResponseError(new ChatResponseError("WebSocket is not connected"));
                setIsBotResponseLoading(false); // Stop loading if WebSocket is not connected
            }
        } catch (e) {
            if (e instanceof ChatResponseError) {
                setBotResponseError(e);
            } else if (e instanceof Error) {
                setBotResponseError(new ChatResponseError(e.message));
            }
            setIsBotResponseLoading(false); // Stop loading on error
        }
    };

    const getConversationID = () => {
        return conversationID;
    };

    const retryAllErroredDialogs = async () => {
        const dialogsToRetry = dialog.filter(dialogItem => dialogItem.error !== undefined);

        for (const dialogItem of dialogsToRetry) {
            const new_dialog_id = uuidv4();
            const payloads = await convertToUserPromptPayload(dialogItem.user_question.message);

            const request: ChatRequest = {
                conversation_id: getConversationID() || "",
                user_id: selectedUser ? selectedUser.id : "anonymous",
                dialog_id: new_dialog_id,
                message: { payload: payloads },
                user_profile: {
                    id: selectedUser ? selectedUser.id : "anonymous",
                    user_name: selectedUser ? selectedUser.user_name : "anonymous",
                    gender: selectedUser ? selectedUser.gender : UserGender.Other,
                    age: selectedUser ? selectedUser.age : 30,
                    description: selectedUser ? selectedUser.description : "No description"
                },
                overrides: {
                    session_manager_runtime: {
                        check_safe_image_content: isContentSafetyEnabled
                    }
                }
            };

            // Send the request over the WebSocket
            if (websocket && websocket.readyState === WebSocket.OPEN) {
                websocket.send(JSON.stringify(request));

                // Update the dialog state with the new dialog_id and reset error, intermediate_responses, and final_response
                setDialog(prevDialog => {
                    const updatedDialog = prevDialog.map(d => {
                        if (d.dialog_id === dialogItem.dialog_id) {
                            return {
                                ...d,
                                dialog_id: new_dialog_id,
                                error: undefined,
                                intermediate_responses: [],
                                final_response: undefined
                            };
                        }
                        return d;
                    });
                    return updatedDialog;
                });
            } else {
                console.error("WebSocket is not open");
                setBotResponseError(new ChatResponseError("WebSocket is not connected"));
                setIsBotResponseLoading(false); // Stop loading if WebSocket is not connected
            }
        }

        setIsBotResponseLoading(true); // Start loading when retrying
    };

    const onContentSafetyChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, isChecked?: boolean) => {
        setIsContentSafetyEnabled(!!isChecked);
    };

    const onToggleDetailsPanel = (searchResult: ProductResult | null) => {
        if (searchResult == searchResultDetailsOpened) {
            setSearchResultDetailsOpened(null);
            return;
        }

        setSearchResultDetailsOpened(searchResult);
    };

    const onSearchResultChecked = (result: ProductResult) => {
        setCheckedResults([...checkedResults, result.id]);
        if (addSearchResultToInput?.current) {
            addSearchResultToInput.current(result);
        }
    };

    const onSearchResultUnchecked = (result: ProductResult) => {
        const newCheckedResults = checkedResults.filter(articleId => articleId != result.id);
        setCheckedResults(newCheckedResults);
        if (removeSearchResultFromInput?.current) {
            removeSearchResultFromInput.current(result);
        }
    };

    const onSearchResultDeletedFromInput = (articleId: string) => {
        const newCheckedResults = checkedResults.filter(a => a != articleId);
        setCheckedResults(newCheckedResults);
    };

    const scrollToBottom = () => {
        chatMessageStreamEnd.current?.scrollIntoView({ behavior: "smooth" as ScrollBehavior });
    };

    const onUserSelectionChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IChoiceGroupOption) => {
        if (option) {
            const profile = userProfiles.find(userProfile => userProfile.id == option.key);
            if (profile) {
                // Clear chat window when user changes
                // clearChatWindow(false);
                setConversationID(uuidv4());
                setSelectedUser(profile);
            }
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.commandsContainer}>
                {/* <TopBarButton
                    className={styles.commandButton}
                    label={"Clear chat"}
                    icon={<Delete24Regular />}
                    onClick={() => clearChatWindow(true)}
                    disabled={(dialog.length == 0 && !botResponseError) || isBotResponseLoading}
                /> */}
                <TopBarButton
                    className={styles.commandButton}
                    label={"User profiles"}
                    icon={<Person24Regular />}
                    onClick={() => setIsUserPanelOpen(!isUserPanelOpen)}
                />
                <TopBarButton
                    className={styles.commandButton}
                    label={"Developer settings"}
                    icon={<Settings24Regular />}
                    onClick={() => setIsConfigPanelOpen(!isConfigPanelOpen)}
                />
                <TopBarButton
                    className={styles.commandButton}
                    label={"Logged in : " + accounts[0].name + " | Sign Out"}
                    icon={<Person24Regular />}
                    onClick={() =>
                        instance.logoutRedirect({
                            postLogoutRedirectUri: "/"
                        })
                    }
                />
            </div>
            <div className={styles.chatRoot}>
                <div className={styles.chatContainer}>
                    {dialog.length == 0 ? (
                        <div className={styles.chatEmptyState}>
                            <BuildingShopRegular className={styles.chatEmptyStateIcon} aria-hidden="true" aria-label="Chat logo" />
                            <h1 className={styles.chatEmptyStateTitle}>Shopping Assistant</h1>
                            <h2 className={styles.chatEmptyStateSubtitle}>
                                Ask anything about our catalog, feel free to include one or more images to assist your search
                            </h2>
                        </div>
                    ) : (
                        <div className={styles.chatScrollable} ref={chatMessageStream}>
                            <div className={styles.chatMessageStream}>
                                {dialog.map((message, index) => (
                                    <div key={`ChatMessage_${index}`}>
                                        <UserChatMessage key={`UserMessage_${index}`} message={message.user_question.message} />
                                        {message.final_response != undefined ? (
                                            <div>
                                                <BotChatMessage
                                                    key={`BotMessage_${index}`}
                                                    isLast={index == dialog.length - 1}
                                                    botMessage={convertBotResponseToUIBotMessage(message.final_response)}
                                                    checkable={index == dialog.length - 1 && !isBotResponseLoading && !botResponseError}
                                                    checkedResults={checkedResults}
                                                    onResultSelect={onSearchResultChecked}
                                                    onResultDeselect={onSearchResultUnchecked}
                                                    onResultDetailsClicked={searchResult => onToggleDetailsPanel(searchResult)}
                                                    onImageLoaded={() => scrollToBottom()}
                                                />
                                            </div>
                                        ) : message.error != undefined ? (
                                            <div className={styles.chatMessageGptMinWidth}>
                                                <ErrorToast
                                                    message={message.error?.error?.error_str || "An error occurred"}
                                                    retryable={true}
                                                    onRetry={() => retryAllErroredDialogs()}
                                                />
                                            </div>
                                        ) : (
                                            <div className={styles.chatMessageGptMinWidth}>
                                                <BotChatMessageLoading intermediate_chat_responses={message.intermediate_responses} />
                                            </div>
                                        )}
                                    </div>
                                ))}
                                <div ref={chatMessageStreamEnd} />
                            </div>
                        </div>
                    )}

                    <div className={styles.chatInput}>
                        <QuestionInput
                            disableSend={isBotResponseLoading || !websocket || websocket.readyState !== WebSocket.OPEN}
                            onSend={(userMessage: UserInput) => setLastUserInput(userMessage)}
                            onSearchResultBackspaced={onSearchResultDeletedFromInput}
                            addSearchResultToInput={addSearchResultToInput}
                            removeSearchResultFromInput={removeSearchResultFromInput}
                        />
                    </div>
                </div>

                <Panel
                    headerText="Product Details"
                    isOpen={dialog.length > 0 && !!searchResultDetailsOpened}
                    isBlocking={true}
                    isLightDismiss={true}
                    onDismiss={() => onToggleDetailsPanel(null)}
                    closeButtonAriaLabel="Close"
                    type={PanelType.medium}
                >
                    <ProductDetails result={searchResultDetailsOpened} />
                </Panel>

                <Panel
                    headerText="Select user profile"
                    isOpen={isUserPanelOpen}
                    isBlocking={true}
                    isLightDismiss={true}
                    onDismiss={() => setIsUserPanelOpen(false)}
                    closeButtonAriaLabel="Close"
                >
                    <ChoiceGroup
                        className={styles.chatSetting}
                        label="User Profile"
                        options={userProfiles.map(userProfile => ({ key: userProfile.id, text: userProfile.user_name }))}
                        onChange={onUserSelectionChange}
                        defaultSelectedKey={selectedUser?.id}
                    />

                    <div className={styles.chatSettingsDiv}>
                        <span className={styles.chatSettingsTitle}>{"Gender:"}</span>
                        <span className={styles.chatSettingsText}>{selectedUser?.gender}</span>
                    </div>
                    <div className={styles.chatSettingsDiv}>
                        <span className={styles.chatSettingsTitle}>{"Age:"}</span>
                        <span className={styles.chatSettingsText}>{selectedUser?.age ? selectedUser?.age : "None provided"}</span>
                    </div>
                    <span className={styles.chatSettingsText}>{selectedUser?.description}</span>
                </Panel>

                <Panel
                    headerText="Configure bot response"
                    isOpen={isConfigPanelOpen}
                    isBlocking={true}
                    isLightDismiss={true}
                    onDismiss={() => setIsConfigPanelOpen(false)}
                    closeButtonAriaLabel="Close"
                >
                    <br />
                    <b>Debug Information (Click to copy):</b>
                    <br />
                    <span onClick={() => navigator.clipboard.writeText(conversationID ?? "")} style={{ cursor: "pointer" }}>
                        <b>Conversation ID:</b> {conversationID}
                    </span>
                    <br />
                    <Checkbox
                        className={styles.chatSetting}
                        label="Enable content safety"
                        onChange={onContentSafetyChange}
                        defaultChecked={isContentSafetyEnabled}
                    />
                </Panel>
            </div>
        </div>
    );
};

export default Chat;
