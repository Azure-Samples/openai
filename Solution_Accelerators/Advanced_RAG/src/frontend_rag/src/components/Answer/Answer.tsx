/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */
import { useMemo } from "react";
import { Stack, IconButton, PrimaryButton, Label } from "@fluentui/react";
import DOMPurify from "dompurify";

import styles from "./Answer.module.css";

import { ChatResponse, getCitationFilePath } from "../../api";
import { parseAnswerToHtml } from "./AnswerParser";
import { AnswerIcon } from "./AnswerIcon";
import { ErrorCircle20Regular } from "@fluentui/react-icons";

interface Props {
    chatResponse: ChatResponse;
    intermediateResponses: ChatResponse[];
    isSelected?: boolean;
    onCitationClicked: (filePath: string) => void;
    onThoughtProcessClicked: () => void;
    onSupportingContentClicked: () => void;
    onRetryClicked?: () => void;
    retryable: boolean;
    sessionManagerConfigVersion?: string;
}

export const Answer = ({
    chatResponse,
    intermediateResponses,
    isSelected,
    onCitationClicked,
    onThoughtProcessClicked,
    onSupportingContentClicked,
    onRetryClicked,
    retryable,
    sessionManagerConfigVersion
}: Props) => {
    const parsedAnswer = useMemo(() => parseAnswerToHtml(chatResponse, onCitationClicked), [chatResponse]);
    const sanitizedAnswerHtml = DOMPurify.sanitize(parsedAnswer.answerHtml);

    return (
        <Stack className={`${styles.answerContainer} ${isSelected && styles.selected}`} verticalAlign="space-between">
            <Stack.Item>
                <Stack horizontal horizontalAlign="space-between">
                    <AnswerIcon />
                    <div>
                        <IconButton
                            style={{ color: "black" }}
                            iconProps={{ iconName: "Lightbulb" }}
                            title="Show thought process"
                            ariaLabel="Show thought process"
                            onClick={() => onThoughtProcessClicked()}
                            disabled={intermediateResponses.length === 0}
                        />
                        <IconButton
                            style={{ color: "black" }}
                            iconProps={{ iconName: "ClipboardList" }}
                            title="Show supporting content"
                            ariaLabel="Show supporting content"
                            onClick={() => onSupportingContentClicked()}
                            disabled={!chatResponse.answer.data_points?.length}
                        />
                    </div>
                </Stack>
            </Stack.Item>

            <Stack.Item grow>
                <div className={styles.answerText} dangerouslySetInnerHTML={{ __html: sanitizedAnswerHtml }}></div>
                {retryable && onRetryClicked && (
                    <div className={styles.retryContainer}>
                        <ErrorCircle20Regular />
                        <Label className={styles.retryText}>
                            Looks like this search ran into an issue. Would you like me to try again with an expanded scope?
                        </Label>
                        <PrimaryButton className={styles.retryButton} onClick={onRetryClicked} text="Retry" />
                    </div>
                )}
            </Stack.Item>

            {!!parsedAnswer.citations.length && (
                <Stack.Item>
                    <Stack horizontal wrap tokens={{ childrenGap: 5 }}>
                        <span className={styles.citationLearnMore}>Citations:</span>
                        {parsedAnswer.citations.map((x, i) => {
                            const path = getCitationFilePath(x, sessionManagerConfigVersion);
                            return (
                                <a key={i} className={styles.citation} title={x} onClick={() => onCitationClicked(path)}>
                                    {`${++i}. ${x}`}
                                </a>
                            );
                        })}
                    </Stack>
                </Stack.Item>
            )}
        </Stack>
    );
};
