import { useEffect, useState } from "react";
import { Stack, TextField } from "@fluentui/react";
import { Send28Filled, Mic28Filled } from "@fluentui/react-icons";

import styles from "./QuestionInput.module.css";
import { SpeechKeyResponse, getSpeechToken, isSpeechTokenValid } from "../../api";

import * as speechsdk from "microsoft-cognitiveservices-speech-sdk";
import React from "react";

const SPEECH_LOCALES = import.meta.env.VITE_SPEECH_INPUT_LOCALES.split(",");

interface Props {
    onSend: (question: string, SSTOutput: boolean, questionLocale?: string) => void;
    disabled: boolean;
    placeholder?: string;
    clearOnSend?: boolean;
}

export const QuestionInput = ({ onSend, disabled, placeholder, clearOnSend }: Props) => {
    const [question, setQuestion] = useState<string>("");
    const [questionLocale, setQuestionLocale] = useState<string | undefined>(undefined);
    const [uiText, setUiText] = useState<string>("");
    const [isRecognizing, setIsRecognizing] = useState(false);
    const [speechRecognizer, setSpeechRecognizer] = useState<speechsdk.SpeechRecognizer | null>(null);

    useEffect(() => {
        console.log("isRecognizing: ", isRecognizing, " question: ", question);
        if (!isRecognizing) {
            sendQuestionSTT();
        }
    }, [isRecognizing]);

    useEffect(() => {
        setUpSpeechRecognizer();
    }, []);

    const sendQuestion = () => {
        console.log("Questions: ", question);
        if (disabled || !question.trim()) {
            return;
        }

        onSend(question, false, questionLocale);

        if (clearOnSend) {
            setQuestion("");
        }
    };

    const sendQuestionSTT = () => {
        if (disabled || !question.trim()) {
            return;
        }

        onSend(question, true, questionLocale);

        if (clearOnSend) {
            setQuestion("");
        }
    };

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

    const setUpSpeechRecognizer = async () => {
        const tokenObj = await getSpeechTokenLocal();
        const speechConfig = speechsdk.SpeechConfig.fromAuthorizationToken(tokenObj.token, tokenObj.region);
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
            var autoDetectSourceLanguageConfig = speechsdk.AutoDetectSourceLanguageConfig.fromLanguages(SPEECH_LOCALES);
            recognizer = speechsdk.SpeechRecognizer.FromConfig(speechConfig, autoDetectSourceLanguageConfig, audioConfig);
        }

        recognizer.recognizing = (s, e) => {
            console.log(`RECOGNIZING: Text=${e.result.text}`);
            setQuestion(question + " " + e.result.text);
            setQuestionLocale(e.result.language);
        };

        let timerId: number | undefined = undefined;

        recognizer.recognized = (s, e) => {
            if (e.result.reason == speechsdk.ResultReason.RecognizedSpeech) {
                console.log(`RECOGNIZED: Text=${e.result.text}`);
                setQuestion(question + " " + e.result.text);
                setQuestionLocale(e.result.language);
                clearTimeout(timerId);
                timerId = setTimeout(() => {
                    recognizer.stopContinuousRecognitionAsync();
                }, 1250); // Stop recognition after 5 seconds of silence
            } else if (e.result.reason == speechsdk.ResultReason.NoMatch) {
                console.log("NOMATCH: Speech could not be recognized.");
            }
        };

        recognizer.sessionStopped = (s, e) => {
            console.log("\n    Session stopped event.");
            recognizer.stopContinuousRecognitionAsync();
            setIsRecognizing(false);
        };
        setSpeechRecognizer(recognizer);
    };

    const voiceInput = async () => {
        if (!speechRecognizer) {
            return;
        }

        if (isRecognizing) {
            speechRecognizer.stopContinuousRecognitionAsync(() => {
                console.log("Stopped recognition");
                setQuestion("");
                setIsRecognizing(false);
            });
        } else {
            speechRecognizer.startContinuousRecognitionAsync();
            setIsRecognizing(true);
        }
    };

    const onEnterPress = (ev: React.KeyboardEvent<Element>) => {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            sendQuestion();
        }
    };

    const onQuestionChange = (_ev: React.FormEvent<HTMLInputElement | HTMLTextAreaElement>, newValue?: string) => {
        if (!newValue) {
            setQuestion("");
        } else if (newValue.length <= 1000) {
            setQuestion(newValue);
        }
    };

    const sendQuestionDisabled = disabled || !question.trim();

    return (
        <Stack horizontal className={styles.questionInputContainer}>
            <TextField
                className={styles.questionInputTextArea}
                placeholder={placeholder}
                multiline
                resizable={false}
                borderless
                value={question}
                onChange={onQuestionChange}
                onKeyDown={onEnterPress}
            />
            <div className={styles.questionInputButtonsContainer}>
                <div
                    className={`${styles.questionInputSendButton} ${sendQuestionDisabled ? styles.questionInputSendButtonDisabled : ""}`}
                    aria-label="Ask question button"
                    onClick={sendQuestion}
                >
                    <Send28Filled primaryFill="rgba(115, 118, 225, 1)" />
                </div>

                {
                    <div className={`${styles.questionInputSendButton} `} aria-label="Ask question button" onClick={voiceInput}>
                        {isRecognizing ? <Mic28Filled primaryFill="rgba(255, 118, 225, 1)" /> : <Mic28Filled primaryFill="rgba(225, 200, 200, 1)" />}
                    </div>
                }
            </div>
        </Stack>
    );
};
