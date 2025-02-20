/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */
import { useRef, useState, useEffect } from "react";
import { Checkbox, Panel, DefaultButton, TextField, SpinButton, ChoiceGroup, IChoiceGroupOption, Label, Dropdown, IDropdownOption } from "@fluentui/react";
import { Delete24Regular, Person24Regular, Settings24Regular, SparkleFilled, ArrowReset24Filled, SpeakerMute24Filled } from "@fluentui/react-icons";
import styles from "./Chat.module.css";
import { v4 as uuidv4 } from "uuid";

import { ChatResponse, ConfigID, getConfigurations, UserProfile, ApproachType, UserQuestion, getSpeechToken, getICEData, ChatRequest } from "../../api";
import { Answer, AnswerLoading } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { UserChatMessage } from "../../components/UserChatMessage";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { TopBarButton } from "../../components/TopBarButton";
import { ErrorToast } from "../../components/ErrorToast";

import * as speechSdk from "microsoft-cognitiveservices-speech-sdk";
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../../authConfig";
import { LoadingPanel } from "../../components/LoadingPanel";
import { ErrorPanel } from "../../components/ErrorPanel";

var CHAT_WS_URL = import.meta.env.VITE_BACKEND_URI + "/ws/chat";

if (CHAT_WS_URL.startsWith("http")) {
    CHAT_WS_URL = CHAT_WS_URL.replace("http", "ws");
} else {
    CHAT_WS_URL = CHAT_WS_URL.replace("https", "wss");
}

const SPEECH_INPUT_LOCALES = import.meta.env.VITE_SPEECH_INPUT_LOCALES.split(",");
var SPEECH_OUTPUT_LOCALES = import.meta.env.VITE_SPEECH_OUTPUT_MAPPING.split(",");
const speechOutputLocaleMap = SPEECH_OUTPUT_LOCALES.reduce((acc: Record<string, string>, locale: string) => {
    const [inputLocale, outputLocale] = (locale as string).split(":");
    acc[inputLocale] = outputLocale;
    return acc;
}, {} as Record<string, string>);

type Props = {
    userProfiles: UserProfile[];
};

const Chat = ({ userProfiles }: Props) => {
    const [isUserPanelOpen, setIsUserPanelOpen] = useState(false);
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [retrieveCount, setRetrieveCount] = useState<number>(25);
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
    const [enableTTSAvatar, setEnableTTSAvatar] = useState<boolean>(false);
    const [alwaysOutputSpeech, setAlwaysOutputSpeech] = useState<boolean>(false);
    const alwaysOutputSpeechRef = useRef<boolean>(false);
    alwaysOutputSpeechRef.current = alwaysOutputSpeech;

    const reconnectCount = useRef<number>(0);

    const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);

    const [baseConversationID, setBaseConversationID] = useState<string>("");
    const [experimentID, setExperimentID] = useState<string>("");
    const [textFieldValue, setTextFieldValue] = useState("");

    const [orchestratorOptions, setOrchestratorOptions] = useState<IDropdownOption[]>([]);
    const [selectedOrchestratorOption, setSelectedOrchestratorOption] = useState<IDropdownOption | undefined>(undefined);

    const [searchOverridesOptions, setSearchOverridesOptions] = useState<IDropdownOption[]>([]);
    const [selectedSearchOverridesOption, setselectedSearchOverridesOption] = useState<IDropdownOption | undefined>(undefined);

    const [sessionManagerOverridesOptions, setSessionManagerOverridesOptions] = useState<IDropdownOption[]>([]);
    const [selectedSessionManagerOverridesOption, setselectedSessionManagerOverridesOption] = useState<IDropdownOption | undefined>(undefined);

    const [selectedUser, setSelectedUser] = useState<UserProfile>();

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    const [selectedAnswer, setSelectedAnswer] = useState<number>(0);
    const [dialog, setDialog] = useState<
        {
            dialog_id: string;
            user_question: UserQuestion;
            intermediate_responses: ChatResponse[];
            final_response: ChatResponse | undefined;
            error_reponse: ChatResponse | undefined;
        }[]
    >([]);

    const avatarSynthesizer = useRef<speechSdk.AvatarSynthesizer | null>(null);
    const avatarInterval = useRef<number | null>(null);
    const [isContentSafetyEnabled, setIsContentSafetyEnabled] = useState<boolean>(false);
    const [isSpeaking, setIsSpeaking] = useState<boolean>(false);

    const speechSynthesizer = useRef<speechSdk.SpeechSynthesizer | null>(null);
    const audioPlayer = useRef<speechSdk.SpeakerAudioDestination | null>(null);

    const [isConnectingToChat, setIsConnectingToChat] = useState<boolean>(true);
    const [websocket, setWebsocket] = useState<WebSocket | null>(null);
    const [websocketError, setWebsocketError] = useState<string | null>(null);

    const { instance, accounts } = useMsal();

    const videoDiv = useRef<HTMLVideoElement>(null);
    const audioDiv = useRef<HTMLAudioElement>(null);

    useEffect(() => {
        connectToChat();
    }, []);

    useEffect(() => {
        if (enableTTSAvatar) {
            setUpTTSAvatar();
        }
    }, [enableTTSAvatar]);

    useEffect(() => {
        setUpTTS();
    }, []);

    useEffect(() => {
        if (enableTTSAvatar) {
            avatarInterval.current = setInterval(() => {
                checkVideoDisconnected();
            }, 30000);
        } else {
            if (avatarInterval.current !== null) {
                clearInterval(avatarInterval.current);
            }
        }
    }, [enableTTSAvatar]);

    useEffect(() => {
        setBaseConversationID(uuidv4());

        if (userProfiles.length > 0) {
            setSelectedUser(userProfiles[0]);
        }

        // Fetch dropdown options
        fetchOrchestratorOptions();
        fetchSearchOverridesOptions();
        fetchSessionManagerOverridesOptions();
    }, []);

    useEffect(() => chatMessageStreamEnd.current?.scrollIntoView({ behavior: "smooth" }), [dialog]);

    const connectToChat = async () => {
        setIsConnectingToChat(true);
        setWebsocketError(null);

        const ws = new WebSocket(CHAT_WS_URL + "?connection_id=" + uuidv4() + "&scenario=rag");

        ws.onopen = () => {
            console.log("Connected to chat!");
            setWebsocket(ws);
            setIsConnectingToChat(false);
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

            setDialog(prevDialog => {
                const dialogIndex = prevDialog.findIndex(dialogItem => dialogItem.dialog_id === result.dialog_id);

                if (dialogIndex !== -1) {
                    const updatedDialog = prevDialog[dialogIndex];

                    if (result.error) {
                        // error response received
                        prevDialog[dialogIndex] = {
                            dialog_id: result.dialog_id,
                            user_question: updatedDialog.user_question,
                            intermediate_responses: updatedDialog.intermediate_responses,
                            final_response: updatedDialog.final_response,
                            error_reponse: result
                        };
                        clearAllPendingDialogs();
                    } else if (result.answer && result.answer.data_points && result.answer.data_points.length > 0) {
                        // final response received
                        if (updatedDialog.user_question.STTOutput || alwaysOutputSpeechRef.current) {
                            textToSpeech(result);
                        }
                        prevDialog[dialogIndex] = {
                            dialog_id: result.dialog_id,
                            user_question: updatedDialog.user_question,
                            intermediate_responses: updatedDialog.intermediate_responses,
                            final_response: result,
                            error_reponse: updatedDialog.error_reponse
                        };
                    } else {
                        // intermediate response received
                        prevDialog[dialogIndex] = {
                            dialog_id: result.dialog_id,
                            user_question: updatedDialog.user_question,
                            intermediate_responses: [...updatedDialog.intermediate_responses, result],
                            final_response: updatedDialog.final_response,
                            error_reponse: updatedDialog.error_reponse
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
                        dialog_id: uuidv4(), // generate new dialog id to prevent further processing
                        error_reponse: { error: { error_str: "An error occured" }, dialog_id: dialogItem.dialog_id } as ChatResponse
                    };
                }
                return dialogItem;
            });
            return updatedDialog;
        });
    };

    const retryAllErroredDialogs = () => {
        setDialog(prevDialog => {
            const updatedDialog = prevDialog.map(dialogItem => {
                if (dialogItem.error_reponse !== undefined && (dialogItem.error_reponse.error?.retry ?? true)) {
                    const userId = selectedUser?.id && selectedUser.id.trim() !== "" ? selectedUser.id : "anonymous"; // Check if user_id is empty or null and set to "anonymous"
                    const request: ChatRequest = {
                        user_id: userId,
                        conversation_id: getConversationID(),
                        dialog_id: uuidv4(),
                        message: {
                            payload: [
                                {
                                    type: "text",
                                    value: dialogItem.user_question.question,
                                    locale: dialogItem.user_question.questionLocale
                                }
                            ]
                        },
                        overrides: {
                            orchestrator_runtime: {
                                config_version: selectedOrchestratorOption?.key as string
                            },
                            search_overrides: {
                                top: retrieveCount,
                                semantic_ranker: useSemanticRanker,
                                vector_search: true,
                                config_version: selectedSearchOverridesOption?.key as string
                            },
                            session_manager_runtime: {
                                check_safe_image_content: isContentSafetyEnabled,
                                config_version: selectedSessionManagerOverridesOption?.key as string
                            }
                        }
                    };
                    websocket?.send(JSON.stringify(request));
                    return {
                        ...dialogItem,
                        dialog_id: request.dialog_id,
                        error_reponse: undefined,
                        intermediate_responses: [],
                        final_response: undefined
                    };
                }
                return dialogItem;
            });
            return updatedDialog;
        });
    };

    const fetchOrchestratorOptions = async () => {
        const available_configuration_versions = await getConfigurations(ConfigID.ORCHESTRATOR_RUNTIME);

        const options = available_configuration_versions.map((item: any) => ({ key: item, text: item }));
        setOrchestratorOptions(options);
    };

    const fetchSearchOverridesOptions = async () => {
        const available_configuration_versions = await getConfigurations(ConfigID.SEARCH_RUNTIME);

        const options = available_configuration_versions.map((item: any) => ({ key: item, text: item }));
        setSearchOverridesOptions(options);
    };

    const fetchSessionManagerOverridesOptions = async () => {
        const available_configuration_versions = await getConfigurations(ConfigID.SESSION_MANAGER_RUNTIME);

        const options = available_configuration_versions.map((item: any) => ({ key: item, text: item }));
        setSessionManagerOverridesOptions(options);
    };

    const getQuestionAnswer = async (
        question: string,
        questionLocale: string | undefined,
        classificationOverride: ApproachType | undefined = undefined,
        STTOutput: boolean = false
    ) => {
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        const token = await instance.acquireTokenSilent({ ...loginRequest, account: accounts[0] });

        try {
            const request: ChatRequest = {
                user_id: selectedUser ? selectedUser.id : "",
                conversation_id: getConversationID(),
                dialog_id: crypto.randomUUID(),
                message: {
                    payload: [
                        {
                            type: "text",
                            value: question,
                            locale: questionLocale
                        }
                    ]
                },
                overrides: {
                    orchestrator_runtime: {
                        config_version: selectedOrchestratorOption?.key as string
                    },
                    search_overrides: {
                        top: retrieveCount,
                        semantic_ranker: useSemanticRanker,
                        vector_search: true,
                        config_version: selectedSearchOverridesOption?.key as string
                    },
                    session_manager_runtime: {
                        check_safe_image_content: isContentSafetyEnabled,
                        config_version: selectedSessionManagerOverridesOption?.key as string
                    }
                }
            };

            setDialog(prevDialog => [
                ...prevDialog,
                {
                    dialog_id: request.dialog_id,
                    user_question: { question, questionLocale, classificationOverride, STTOutput },
                    intermediate_responses: [],
                    final_response: undefined,
                    error_reponse: undefined
                }
            ]);
            websocket?.send(JSON.stringify(request));
        } catch (e) {
            console.log(`Error while sending request: ${e}`);
        }
    };

    const getConversationID = () => {
        return experimentID + ":" + baseConversationID;
    };

    const newTopic = async () => {
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setDialog([]);
        setBaseConversationID(uuidv4());
    };

    const onUserSelectionChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IChoiceGroupOption) => {
        if (option) {
            const profile = userProfiles.find(userProfile => userProfile.id == option.key);
            if (profile) {
                setActiveCitation(undefined);
                setActiveAnalysisPanelTab(undefined);
                setDialog([]);
                setBaseConversationID(crypto.randomUUID());
                setSelectedUser(profile);
            }
        }
    };

    const onRetrieveCountChange = (_ev?: React.SyntheticEvent<HTMLElement, Event>, newValue?: string) => {
        setRetrieveCount(parseInt(newValue || "20"));
    };

    const onUseSemanticRankerChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSemanticRanker(!!checked);
    };

    const onEnableTTSAvatarChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setEnableTTSAvatar(!!checked);
    };

    const onAlwaysOutputSpeechChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setAlwaysOutputSpeech(!!checked);
    };

    const onSetExperimentID = () => {
        setExperimentID(textFieldValue);
        setTextFieldValue("");
        newTopic();
    };

    const onOrchestratorChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IDropdownOption) => {
        if (option) {
            setSelectedOrchestratorOption(option);
        }
    };

    const onSearchOverridesChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IDropdownOption) => {
        if (option) {
            setselectedSearchOverridesOption(option);
        }
    };

    const onSessionManagerOverridesChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IDropdownOption) => {
        if (option) {
            setselectedSessionManagerOverridesOption(option);
        }
    };

    const onShowCitation = (citation: string, index: number) => {
        if (activeCitation === citation && activeAnalysisPanelTab === AnalysisPanelTabs.CitationTab && selectedAnswer === index) {
            setActiveAnalysisPanelTab(undefined);
            setActiveCitation(undefined);
        } else {
            setActiveCitation(citation);
            setActiveAnalysisPanelTab(AnalysisPanelTabs.CitationTab);
        }

        setSelectedAnswer(index);
    };

    const onToggleTab = (tab: AnalysisPanelTabs, index: number) => {
        if (activeAnalysisPanelTab === tab && selectedAnswer === index) {
            setActiveAnalysisPanelTab(undefined);
            setActiveCitation(undefined);
        } else {
            setActiveAnalysisPanelTab(tab);

            if (selectedAnswer !== index) {
                setActiveCitation(undefined);
            }
        }

        setSelectedAnswer(index);
    };

    const textToSpeech = async (chatResponse: ChatResponse) => {
        var ssml = "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='" + chatResponse.answer.speaker_locale + "'>";
        const speakerLocale = chatResponse.answer.speaker_locale;
        if (speakerLocale && speechOutputLocaleMap[speakerLocale]) {
            ssml += "<voice name='" + speechOutputLocaleMap[speakerLocale] + "'>";
        } else {
            ssml += "<voice name='en-GB-RyanNeural'>";
        }
        ssml += chatResponse.answer.speak_answer;
        ssml += "</voice>";
        ssml += "</speak>";

        if (enableTTSAvatar) {
            if (avatarSynthesizer.current) {
                setIsSpeaking(true);
                avatarSynthesizer.current
                    .speakSsmlAsync(ssml)
                    .then(result => {
                        if (result.reason === speechSdk.ResultReason.SynthesizingAudioCompleted) {
                            console.log("Speech and avatar synthesized to video stream.");
                        } else {
                            console.log("Unable to speak. Result ID: " + result.resultId + " Reason: " + result.reason);
                        }
                        setIsSpeaking(false);
                    })
                    .catch(error => {
                        console.log(error);
                        avatarSynthesizer.current?.close();
                        setIsSpeaking(false);
                    });
            }
        } else {
            await setUpTTS();
            if (speechSynthesizer.current) {
                setIsSpeaking(true);
                speechSynthesizer.current?.speakSsmlAsync(ssml, result => {
                    if (result.reason === speechSdk.ResultReason.SynthesizingAudioCompleted) {
                        console.log("Speech synthesized.");
                    } else {
                        console.log("Unable to speak. Result ID: " + result.resultId + " Reason: " + result.reason);
                    }
                    speechSynthesizer.current?.close();
                });
            }
        }
    };

    const checkVideoDisconnected = async () => {
        const videoElement = videoDiv.current;
        if (videoElement) {
            let videoTime = videoElement.currentTime;
            setTimeout(async () => {
                if (videoElement.currentTime === videoTime) {
                    console.log("Video Disconnected. Resetting Avatar");
                    await setUpTTSAvatar();
                }
            }, 20000);
        }
    };

    const setUpTTS = async () => {
        let speechToken = await getSpeechToken();

        const tokenObj = {
            authToken: speechToken.token,
            region: speechToken.region
        };
        let speechSynthesisConfig = speechSdk.SpeechConfig.fromAuthorizationToken(tokenObj.authToken, tokenObj.region);
        var audioPlayerObj = new speechSdk.SpeakerAudioDestination();
        audioPlayerObj.onAudioEnd = () => {
            setIsSpeaking(false);
        };
        let audioConfig = speechSdk.AudioConfig.fromSpeakerOutput(audioPlayerObj);
        let speechSynthesizerObj = new speechSdk.SpeechSynthesizer(speechSynthesisConfig, audioConfig);

        audioPlayer.current = audioPlayerObj;
        speechSynthesizer.current = speechSynthesizerObj;
    };

    const setUpTTSAvatar = async () => {
        let speechToken = await getSpeechToken();

        const tokenObj = {
            authToken: speechToken.token,
            region: speechToken.region
        };
        let speechSynthesisConfig = speechSdk.SpeechConfig.fromAuthorizationToken(tokenObj.authToken, tokenObj.region);
        speechSynthesisConfig.speechSynthesisLanguage = "en-GB";
        speechSynthesisConfig.speechSynthesisVoiceName = "en-GB-RyanNeural";
        const videoFormat = new speechSdk.AvatarVideoFormat();
        const talkingAvatarCharacter = "harry";
        const talkingAvatarStyle = "business";

        const avatarConfig = new speechSdk.AvatarConfig(talkingAvatarCharacter, talkingAvatarStyle, videoFormat);
        let avatarSynthesizerObj = new speechSdk.AvatarSynthesizer(speechSynthesisConfig, avatarConfig);

        let iceData = await getICEData(tokenObj.region, tokenObj.authToken);

        const iceServerUrl = iceData.Urls[0];
        const iceServerUsername = iceData.Username;
        const iceServerCredential = iceData.Password;
        let peerConnection = new RTCPeerConnection({
            iceServers: [
                {
                    urls: [iceServerUrl],
                    username: iceServerUsername,
                    credential: iceServerCredential
                }
            ]
        });

        peerConnection.ontrack = function (event) {
            if (event.track.kind === "video") {
                console.log("Video On Track");
                const videoElement = videoDiv.current;
                if (videoElement) {
                    videoElement.setAttribute("height", "225px");
                    videoElement.setAttribute("width", "400px");
                    videoElement.id = "videoPlayer";
                    videoElement.srcObject = event.streams[0];
                    videoElement.autoplay = true;
                }
            }

            if (event.track.kind === "audio") {
                const audioElement = audioDiv.current;
                if (audioElement) {
                    audioElement.id = "audioPlayer";
                    audioElement.srcObject = event.streams[0];
                    audioElement.autoplay = true;
                }
            }
        };

        // Offer to receive one video track, and one audio track
        peerConnection.addTransceiver("video", { direction: "sendrecv" });
        peerConnection.addTransceiver("audio", { direction: "sendrecv" });

        avatarSynthesizerObj
            .startAvatarAsync(peerConnection)
            .then(r => {
                console.log("Avatar started.");
            })
            .catch(error => {
                console.log("Avatar failed to start. Error: " + error);
            });

        avatarSynthesizer.current = avatarSynthesizerObj;
    };

    return (
        <div>
            {isConnectingToChat ? (
                <LoadingPanel loadingMessage="Connecting to chat..." />
            ) : websocketError ? (
                <ErrorPanel
                    error={websocketError}
                    onRetry={() => {
                        connectToChat();
                        reconnectCount.current = 0;
                    }}
                />
            ) : (
                <div className={styles.container}>
                    <div className={styles.commandsContainer}>
                        {isSpeaking && (
                            <TopBarButton
                                className={styles.commandButton}
                                label={"Stop Speaking"}
                                icon={<SpeakerMute24Filled />}
                                onClick={() => {
                                    avatarSynthesizer?.current?.stopSpeakingAsync();
                                    audioPlayer?.current?.pause();
                                    setIsSpeaking(false);
                                    setUpTTS();
                                }}
                            />
                        )}
                        {enableTTSAvatar && (
                            <TopBarButton
                                className={styles.commandButton}
                                label={"Reset Avatar"}
                                icon={<ArrowReset24Filled />}
                                onClick={() => checkVideoDisconnected()}
                            />
                        )}
                        <TopBarButton className={styles.commandButton} label={"New Topic"} icon={<Delete24Regular />} onClick={newTopic} disabled={false} />
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
                        <div className={styles.TTSAvatar} hidden={!enableTTSAvatar || activeAnalysisPanelTab != undefined}>
                            <div id="remoteVideo">
                                <video className="videoDiv" ref={videoDiv}></video>
                                <audio className="audioDiv" ref={audioDiv}></audio>
                            </div>
                        </div>
                        <div className={styles.chatContainer}>
                            {dialog.length == 0 ? (
                                <div className={styles.chatEmptyState}>
                                    <SparkleFilled fontSize={"120px"} primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Chat logo" />
                                    <h3 className={styles.headerTitle}>Use AI to enhance your decision-making</h3>
                                </div>
                            ) : (
                                <div className={styles.chatMessageStream}>
                                    {dialog.map((answer, index) => (
                                        <div key={index}>
                                            <UserChatMessage message={answer.user_question.question} />

                                            {answer.final_response != undefined ? (
                                                <div className={styles.chatMessageGpt}>
                                                    <Answer
                                                        key={index}
                                                        chatResponse={answer.final_response}
                                                        intermediateResponses={answer.intermediate_responses}
                                                        isSelected={selectedAnswer === index && activeAnalysisPanelTab !== undefined}
                                                        onCitationClicked={c => onShowCitation(c, index)}
                                                        onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab, index)}
                                                        onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab, index)}
                                                        onRetryClicked={() => {
                                                            retryAllErroredDialogs();
                                                        }}
                                                        retryable={answer.error_reponse?.error?.retry ?? false}
                                                        sessionManagerConfigVersion={selectedSessionManagerOverridesOption?.key as string}
                                                    />
                                                </div>
                                            ) : answer.error_reponse != undefined ? (
                                                <>
                                                    <div className={styles.chatMessageGptMinWidth}>
                                                        <ErrorToast
                                                            message={answer.error_reponse.error?.error_str}
                                                            retryable={answer.error_reponse.error?.retry ?? true}
                                                            onRetry={() => retryAllErroredDialogs()}
                                                        />
                                                    </div>
                                                </>
                                            ) : (
                                                <div className={styles.chatMessageGptMinWidth}>
                                                    <AnswerLoading intermediate_chat_responses={answer.intermediate_responses} />
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                    <div ref={chatMessageStreamEnd} />
                                </div>
                            )}

                            <div className={styles.chatInput}>
                                <QuestionInput
                                    clearOnSend
                                    placeholder="Type a new question"
                                    disabled={false}
                                    onSend={(question, STTOutput, questionLocale) => getQuestionAnswer(question, questionLocale, undefined, STTOutput)}
                                />
                            </div>
                        </div>
                        {dialog.length > 0 && activeAnalysisPanelTab && (
                            <AnalysisPanel
                                className={styles.chatAnalysisPanel}
                                activeCitation={activeCitation}
                                onActiveTabChanged={x => onToggleTab(x, selectedAnswer)}
                                citationHeight="810px"
                                chatResponse={dialog[selectedAnswer].final_response!}
                                intermediateResponses={dialog[selectedAnswer].intermediate_responses}
                                activeTab={activeAnalysisPanelTab}
                            />
                        )}

                        <Panel
                            headerText="Select user profile"
                            isOpen={isUserPanelOpen}
                            isBlocking={false}
                            onDismiss={() => setIsUserPanelOpen(false)}
                            closeButtonAriaLabel="Close"
                            onRenderFooterContent={() => <DefaultButton onClick={() => setIsUserPanelOpen(false)}>Close</DefaultButton>}
                            isFooterAtBottom={true}
                        >
                            <ChoiceGroup
                                className={styles.chatSettingsSeparator}
                                label="User Profile"
                                options={userProfiles.map(user => ({ key: user.id, text: user.user_name }))}
                                onChange={onUserSelectionChange}
                                defaultSelectedKey={selectedUser?.id}
                            />

                            <Label className={styles.chatSettingsSeparator}>{selectedUser?.description}</Label>
                        </Panel>
                        <Panel
                            headerText="Configure answer generation"
                            isOpen={isConfigPanelOpen}
                            isBlocking={false}
                            onDismiss={() => setIsConfigPanelOpen(false)}
                            closeButtonAriaLabel="Close"
                            onRenderFooterContent={() => <DefaultButton onClick={() => setIsConfigPanelOpen(false)}>Close</DefaultButton>}
                            isFooterAtBottom={true}
                        >
                            <br />
                            <b>Debug Information (Click to copy):</b>
                            <br />
                            <span onClick={() => navigator.clipboard.writeText(getConversationID())} style={{ cursor: "pointer" }}>
                                <b>Conversation ID:</b> {getConversationID()}
                            </span>
                            <br />
                            <SpinButton
                                className={styles.chatSettingsSeparator}
                                label="Retrieve this many documents from search:"
                                min={1}
                                max={500}
                                defaultValue={retrieveCount.toString()}
                                onChange={onRetrieveCountChange}
                            />
                            <TextField
                                className={styles.chatSettingsSeparator}
                                label="ExperimentID (updating this will start new topic)"
                                value={textFieldValue}
                                // onKeyDown={onSetExperimentID}
                                onBlur={onSetExperimentID}
                                onChange={(_ev?: React.FormEvent, newValue?: string) => setTextFieldValue(newValue || "")}
                                placeholder={experimentID ? "Current ExperimentID: " + experimentID : "Set ExperimentID"}
                            />
                            <Checkbox
                                className={styles.chatSettingsSeparator}
                                checked={useSemanticRanker}
                                label="Use semantic ranker for retrieval"
                                onChange={onUseSemanticRankerChange}
                            />
                            <Checkbox
                                className={styles.chatSettingsSeparator}
                                checked={enableTTSAvatar}
                                label="Enable TTS Avatar"
                                onChange={onEnableTTSAvatarChange}
                            />
                            <Checkbox
                                className={styles.chatSettingsSeparator}
                                checked={alwaysOutputSpeech}
                                label="Always Output Speech"
                                onChange={onAlwaysOutputSpeechChange}
                            />
                            <Dropdown
                                className={styles.chatSettingsSeparator}
                                label="Orchestrator Runtime"
                                options={orchestratorOptions}
                                selectedKey={selectedOrchestratorOption ? selectedOrchestratorOption.key : undefined}
                                onChange={onOrchestratorChange}
                                placeholder="Select Orchestrator Runtime Configuration"
                            />
                            <Dropdown
                                className={styles.chatSettingsSeparator}
                                label="Search Overrides"
                                options={searchOverridesOptions}
                                selectedKey={selectedSearchOverridesOption ? selectedSearchOverridesOption.key : undefined}
                                onChange={onSearchOverridesChange}
                                placeholder="Select Search Overrides Configuration"
                            />
                            <Dropdown
                                className={styles.chatSettingsSeparator}
                                label="Session Manager Overrides"
                                options={sessionManagerOverridesOptions}
                                selectedKey={selectedSessionManagerOverridesOption ? selectedSessionManagerOverridesOption.key : undefined}
                                onChange={onSessionManagerOverridesChange}
                                placeholder="Select Session Manager Overrides Configuration"
                            />
                        </Panel>
                    </div>

                    {!activeAnalysisPanelTab && (
                        <div className={styles.disclaimer}>
                            <b>DISCLAIMER:</b>
                            <br />
                            This model has been developed and trained on a limited dataset solely for the purpose of a proof of concept (POC).
                            <br />
                            It may not fully represent the complexities or variations of a comprehensive dataset. Users should be aware of its potential
                            limitations when interpreting the results and making decisions based on its outputs.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default Chat;
