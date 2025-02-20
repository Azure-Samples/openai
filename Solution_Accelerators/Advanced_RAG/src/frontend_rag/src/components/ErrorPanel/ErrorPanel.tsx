import { ErrorToast } from "../ErrorToast/ErrorToast";
import styles from "./ErrorPanel.module.css";

interface Props {
    error: string;
    onRetry: () => void;
}

export const ErrorPanel = ({ error, onRetry }: Props) => {
    return (
        <div className={styles.errorContainer}>
            <ErrorToast message={error} retryable={true} onRetry={onRetry} />
        </div>
    );
};
