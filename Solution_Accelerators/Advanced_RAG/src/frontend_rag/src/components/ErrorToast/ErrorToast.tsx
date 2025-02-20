import { Stack, PrimaryButton } from "@fluentui/react";
import { ErrorCircle24Regular } from "@fluentui/react-icons";

import styles from "./ErrorToast.module.css";

interface Props {
    message?: string;
    retryable: boolean;
    onRetry?: () => void;
}

export const ErrorToast = ({ message, retryable, onRetry }: Props) => {
    return (
        <Stack className={styles.errorToast} verticalAlign="space-between">
            <ErrorCircle24Regular aria-hidden="true" aria-label="Error icon" primaryFill="red" />

            <Stack.Item grow>
                <p className={styles.errorText}>{message ?? "An unexpected error occurred."}</p>
            </Stack.Item>

            {retryable && onRetry && (
                <div className={styles.retryButtonContainer}>
                    <PrimaryButton className={styles.retryButton} onClick={onRetry} text="Retry" />
                </div>
            )}
        </Stack>
    );
};
