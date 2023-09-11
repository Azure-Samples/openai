import { useRef, useState, useEffect } from "react";
import { Checkbox, Panel, DefaultButton, TextField, SpinButton, ChoiceGroup, IChoiceGroupOption, Label } from "@fluentui/react";
import { Delete24Regular, Person24Regular, Settings24Regular, SparkleFilled } from "@fluentui/react-icons";

import styles from "./Chat.module.css";

import {
    chatApi,
    clearChatSession,
    ChatResponse,
    ChatRequest,
    UserProfile,
    ApproachType,
    ChatError,
    ChatResponseError,
    UserQuestion,
    SearchSettings
} from "../../api";
import { Answer, AnswerLoading } from "../../components/Answer";
import { QuestionInput } from "../../components/QuestionInput";
import { ExampleList } from "../../components/Example";
import { UserChatMessage } from "../../components/UserChatMessage";
import { AnalysisPanel, AnalysisPanelTabs } from "../../components/AnalysisPanel";
import { TopBarButton } from "../../components/TopBarButton";
import { ErrorToast } from "../../components/ErrorToast";

type Props = {
    users: UserProfile[];
    searchSettings: SearchSettings;
};

const Chat = ({ users, searchSettings }: Props) => {
    const [isUserPanelOpen, setIsUserPanelOpen] = useState(false);
    const [isConfigPanelOpen, setIsConfigPanelOpen] = useState(false);
    const [retrieveCount, setRetrieveCount] = useState<number>(20);
    const [useSemanticRanker, setUseSemanticRanker] = useState<boolean>(true);
    const [useSemanticCaptions, setUseSemanticCaptions] = useState<boolean>(false);
    const [excludeCategory, setExcludeCategory] = useState<string>("");
    const [useSuggestFollowupQuestions, setUseSuggestFollowupQuestions] = useState<boolean>(false);
    const [useVectorSearch, setUseVectorSearch] = useState<boolean>(searchSettings.vectorization_enabled);

    const chatMessageStreamEnd = useRef<HTMLDivElement | null>(null);

    const [conversationID, setConversationID] = useState<string>();

    const [selectedUser, setSelectedUser] = useState<UserProfile>();

    const [lastQuestion, setLastQuestion] = useState<UserQuestion | undefined>(undefined);
    const [isAnswerLoading, setIsAnswerLoading] = useState<boolean>(false);
    const [answerError, setAnswerError] = useState<ChatError | undefined>();

    const [activeCitation, setActiveCitation] = useState<string>();
    const [activeAnalysisPanelTab, setActiveAnalysisPanelTab] = useState<AnalysisPanelTabs | undefined>(undefined);

    const [selectedAnswer, setSelectedAnswer] = useState<number>(0);
    const [dialog, setDialog] = useState<[user: string, response: ChatResponse][]>([]);

    useEffect(() => {
        if (users.length > 0) {
            setSelectedUser(users[0]);
        }

        setConversationID(crypto.randomUUID());
    }, []);

    useEffect(() => chatMessageStreamEnd.current?.scrollIntoView({ behavior: "smooth" }), [isAnswerLoading]);

    useEffect(() => {
        if (lastQuestion) {
            getQuestionAnswer(lastQuestion.question, lastQuestion.classificationOverride);
        }
    }, [lastQuestion]);

    const updateLastQuestion = (question?: string, classificationOverride: ApproachType | undefined = undefined) => {
        if (question) {
            setLastQuestion({ question, classificationOverride });
        } else {
            setLastQuestion(undefined);
        }
    };

    const getQuestionAnswer = async (question: string, classificationOverride: ApproachType | undefined = undefined) => {
        answerError && setAnswerError(undefined);
        setIsAnswerLoading(true);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);

        try {
            const request: ChatRequest = {
                userID: selectedUser ? selectedUser.user_id : "",
                conversationID: conversationID ? conversationID : "",
                dialogID: crypto.randomUUID(),
                dialog: question,
                overrides: {
                    excludeCategory: excludeCategory.length === 0 ? undefined : excludeCategory,
                    top: retrieveCount,
                    semanticRanker: useSemanticRanker,
                    semanticCaptions: useSemanticCaptions,
                    suggestFollowupQuestions: useSuggestFollowupQuestions,
                    vectorSearch: useVectorSearch,
                    classificationOverride
                }
            };
            const result = await chatApi(request);
            setDialog([...dialog, [question, result]]);
        } catch (e) {
            if (e instanceof ChatResponseError) {
                setAnswerError({ message: e.message, retryable: e.retryable });
            } else if (e instanceof Error) {
                setAnswerError({ message: e.message, retryable: true });
            }
            console.log(`Error getting answer from /chat API: ${e}`);
        } finally {
            setIsAnswerLoading(false);
        }
    };

    const retryWithOverride = (classificationOverride: ApproachType) => {
        setIsAnswerLoading(true);
        const lastUserQuestion = dialog[dialog.length - 1][0];
        setActiveAnalysisPanelTab(undefined);
        setDialog(dialog.slice(0, -1)); // Don't show previous dialog in the chat
        updateLastQuestion(lastUserQuestion, classificationOverride);
    };

    const clearChat = async () => {
        updateLastQuestion(undefined);
        answerError && setAnswerError(undefined);
        setActiveCitation(undefined);
        setActiveAnalysisPanelTab(undefined);
        setDialog([]);
        try {
            if (selectedUser && conversationID) {
                await clearChatSession(selectedUser.user_id, conversationID);
            }
        } catch (e) {
            console.log(`Failed to clear chat session in server: ${e}`);
        }
    };

    const onUserSelectionChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, option?: IChoiceGroupOption) => {
        if (option) {
            const profile = users.find(user => user.user_id == option.key);
            if (profile) {
                updateLastQuestion(undefined);
                answerError && setAnswerError(undefined);
                setActiveCitation(undefined);
                setActiveAnalysisPanelTab(undefined);
                setDialog([]);
                setConversationID(crypto.randomUUID());
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

    const onUseSemanticCaptionsChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSemanticCaptions(!!checked);
    };

    const onUseVectorSearchChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseVectorSearch(!!checked);
    };

    const onExcludeCategoryChanged = (_ev?: React.FormEvent, newValue?: string) => {
        setExcludeCategory(newValue || "");
    };

    const onUseSuggestFollowupQuestionsChange = (_ev?: React.FormEvent<HTMLElement | HTMLInputElement>, checked?: boolean) => {
        setUseSuggestFollowupQuestions(!!checked);
    };

    const onExampleClicked = (example: string) => {
        updateLastQuestion(example);
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

    return (
        <div className={styles.container}>
            <div className={styles.commandsContainer}>
                <TopBarButton
                    className={styles.commandButton}
                    label={"Clear chat"}
                    icon={<Delete24Regular />}
                    onClick={clearChat}
                    disabled={!lastQuestion || isAnswerLoading}
                />
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
            </div>
            <div className={styles.chatRoot}>
                <div className={styles.chatContainer}>
                    {!lastQuestion ? (
                        <div className={styles.chatEmptyState}>
                            <SparkleFilled fontSize={"120px"} primaryFill={"rgba(115, 118, 225, 1)"} aria-hidden="true" aria-label="Chat logo" />
                            <h1 className={styles.chatEmptyStateTitle}>Chat with your data</h1>
                            <h2 className={styles.chatEmptyStateSubtitle}>Ask anything or try an example</h2>
                            <ExampleList onExampleClicked={onExampleClicked} examples={selectedUser?.sample_questions ? selectedUser.sample_questions : []} />
                        </div>
                    ) : (
                        <div className={styles.chatMessageStream}>
                            {dialog.map((answer, index) => (
                                <div key={index}>
                                    <UserChatMessage message={answer[0]} />
                                    <div className={styles.chatMessageGpt}>
                                        <Answer
                                            key={index}
                                            chatResponse={answer[1]}
                                            isSelected={selectedAnswer === index && activeAnalysisPanelTab !== undefined}
                                            onCitationClicked={c => onShowCitation(c, index)}
                                            onThoughtProcessClicked={() => onToggleTab(AnalysisPanelTabs.ThoughtProcessTab, index)}
                                            onSupportingContentClicked={() => onToggleTab(AnalysisPanelTabs.SupportingContentTab, index)}
                                            onFollowupQuestionClicked={q => updateLastQuestion(q)}
                                            showFollowupQuestions={useSuggestFollowupQuestions && dialog.length - 1 === index}
                                            onRetryClicked={() => {
                                                if (answer[1].suggested_classification) {
                                                    retryWithOverride(answer[1].suggested_classification as ApproachType);
                                                }
                                            }}
                                            retryable={index == dialog.length - 1 && !!answer[1].show_retry && !isAnswerLoading && !answerError}
                                        />
                                    </div>
                                </div>
                            ))}
                            {isAnswerLoading && (
                                <>
                                    <UserChatMessage message={lastQuestion.question} />
                                    <div className={styles.chatMessageGptMinWidth}>
                                        <AnswerLoading />
                                    </div>
                                </>
                            )}
                            {answerError ? (
                                <>
                                    <UserChatMessage message={lastQuestion.question} />
                                    <div className={styles.chatMessageGptMinWidth}>
                                        <ErrorToast
                                            message={answerError.message}
                                            retryable={answerError.retryable}
                                            onRetry={() => updateLastQuestion(lastQuestion.question)}
                                        />
                                    </div>
                                </>
                            ) : null}
                            <div ref={chatMessageStreamEnd} />
                        </div>
                    )}

                    <div className={styles.chatInput}>
                        <QuestionInput
                            clearOnSend
                            placeholder="Type a new question"
                            disabled={isAnswerLoading}
                            onSend={question => updateLastQuestion(question)}
                        />
                    </div>
                </div>

                {dialog.length > 0 && activeAnalysisPanelTab && (
                    <AnalysisPanel
                        className={styles.chatAnalysisPanel}
                        activeCitation={activeCitation}
                        onActiveTabChanged={x => onToggleTab(x, selectedAnswer)}
                        citationHeight="810px"
                        chatResponse={dialog[selectedAnswer][1]}
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
                        options={users.map(user => ({ key: user.user_id, text: user.user_name }))}
                        onChange={onUserSelectionChange}
                        defaultSelectedKey={selectedUser?.user_id}
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
                    <SpinButton
                        className={styles.chatSettingsSeparator}
                        label="Retrieve this many documents from search:"
                        min={1}
                        max={50}
                        defaultValue={retrieveCount.toString()}
                        onChange={onRetrieveCountChange}
                    />
                    <TextField className={styles.chatSettingsSeparator} label="Exclude category" onChange={onExcludeCategoryChanged} />
                    <Checkbox
                        className={styles.chatSettingsSeparator}
                        checked={useSemanticRanker}
                        label="Use semantic ranker for retrieval"
                        onChange={onUseSemanticRankerChange}
                    />
                    <Checkbox
                        className={styles.chatSettingsSeparator}
                        checked={useSemanticCaptions}
                        label="Use query-contextual summaries instead of whole documents"
                        onChange={onUseSemanticCaptionsChange}
                        disabled={!useSemanticRanker}
                    />
                    <Checkbox
                        className={styles.chatSettingsSeparator}
                        checked={useVectorSearch}
                        label="Use vector search for retrieval"
                        onChange={onUseVectorSearchChange}
                        disabled={!searchSettings.vectorization_enabled}
                    />
                    {/* <Checkbox
                        className={styles.chatSettingsSeparator}
                        checked={useSuggestFollowupQuestions}
                        label="Suggest follow-up questions"
                        onChange={onUseSuggestFollowupQuestionsChange}
                    /> */}
                </Panel>
            </div>
        </div>
    );
};

export default Chat;
