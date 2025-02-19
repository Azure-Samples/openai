import { useState, useEffect } from "react";
import styles from "./BotChatMessage.module.css";

import { Stack } from "@fluentui/react";
import { animated, useSpring } from "@react-spring/web";

import { BotChatMessageIcon } from "./BotChatMessageIcon";
import { ChatResponse } from "../../api";

type AnswerLoadingProps = {
    intermediate_chat_responses: ChatResponse[];
};

export const BotChatMessageLoading = ({ intermediate_chat_responses }: AnswerLoadingProps) => {
    const animatedStyles = useSpring({
        from: { opacity: 0 },
        to: { opacity: 1 }
    });

    // // State for the loading text and whether it's loading
    // const [loadingText, setLoadingText] = useState(".");
    // const [isLoading, setIsLoading] = useState(true);

    // // Array of pre-canned responses
    // const responses = [
    //     "Hang tight, we're picking out the perfect outfit for you!",
    //     "Just a moment, we're rummaging through our virtual wardrobe",
    //     "Styling in progress, please hold on!",
    //     "Hunting down the best options for you",
    //     "Just a moment, we're stitching together some great options for you",
    //     "Hold on, our stylists are working on your request",
    //     "We're tailoring your search results, hang on a bit!",
    //     "Just a moment, we're accessorizing your look!",
    //     "We'e on a fashion hunt for your request, please wait!",
    //     "Your fashion request is being processed, please wait",
    //     "We're diving into our fashion pool to find your request, hang tight!",
    //     "Just a moment, we're rolling out the fashion runway for you",
    //     "We're busy arranging your personal fashion show, stay tuned!",
    //     "We're putting the final touches on your style recommendations, hang on!",
    //     "We're in our virutal fitting room, finding the best fit for you. Please wait!",
    //     "We're busy sorting through the latest trends for your request, please wait!",
    //     "Our fashion gurus are in session, conjuring up the ideal enseble for you",
    //     "Your style request is under the designer's lens, crafting the perfect fit!",
    //     "Our style scanners are in full swing, pinpointing your next favorite outfit!",
    //     "We're busy creating your next favorite look, please wait!"
    // ];

    // const getRandomResponse = () => {
    //     const randomIndex = Math.floor(Math.random() * responses.length);
    //     return responses[randomIndex];
    // };

    // useEffect(() => {
    //     const timer = setTimeout(() => {
    //         setLoadingText(getRandomResponse() + loadingText);
    //         setIsLoading(false);
    //     }, 2000);

    //     // Clean up the timer
    //     return () => clearTimeout(timer);
    // }, []);

    return (
        <animated.div style={{ ...animatedStyles }}>
            <div className={styles.container}>
                <Stack className={styles.message} verticalAlign="space-between">
                    <Stack.Item>
                        <BotChatMessageIcon />
                    </Stack.Item>
                    <Stack.Item grow>
                        {/* <p className={styles.text}>
                            {isLoading ? loadingText : loadingText}
                            <span className={styles.loadingdots} />
                        </p> */}
                        {intermediate_chat_responses.map((answer, index) => (answer.answer ? <p key={index}>{answer.answer.answer_string}</p> : null))}
                    </Stack.Item>
                </Stack>
            </div>
        </animated.div>
    );
};
