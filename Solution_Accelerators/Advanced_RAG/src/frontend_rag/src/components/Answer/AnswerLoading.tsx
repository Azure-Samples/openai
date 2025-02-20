import { Stack } from "@fluentui/react";
import { animated, useSpring } from "@react-spring/web";

import styles from "./Answer.module.css";
import { AnswerIcon } from "./AnswerIcon";
import { ChatResponse } from "../../api";

type AnswerLoadingProps = {
    intermediate_chat_responses: ChatResponse[];
};

export const AnswerLoading = ({ intermediate_chat_responses }: AnswerLoadingProps) => {
    const animatedStyles = useSpring({
        from: { opacity: 0 },
        to: { opacity: 1 }
    });

    return (
        <animated.div style={{ ...animatedStyles }}>
            <Stack className={styles.answerContainer} verticalAlign="space-between">
                <AnswerIcon />
                <Stack.Item grow>
                    <p className={styles.answerText}>
                        Generating answer
                        <span className={styles.loadingdots} />
                    </p>
                    {intermediate_chat_responses.map((answer, index) => (
                        <p key={index}>{answer.answer.answer_string}</p>
                    ))}
                </Stack.Item>
            </Stack>
        </animated.div>
    );
};
