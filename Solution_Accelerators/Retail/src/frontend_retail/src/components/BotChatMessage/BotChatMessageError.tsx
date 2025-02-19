import styles from "./BotChatMessage.module.css";

import { ErrorToast } from "../ErrorToast";

interface Props {
    message?: string;
    retryable: boolean;
    onRetry?: () => void;
}

export const BotChatMessageError = ({ message, retryable, onRetry }: Props) => {
    return (
        <div className={styles.container}>
            <div className={styles.errorMessage}>
                <ErrorToast message={message} retryable={retryable} onRetry={onRetry} />
            </div>
        </div>
    );
};
