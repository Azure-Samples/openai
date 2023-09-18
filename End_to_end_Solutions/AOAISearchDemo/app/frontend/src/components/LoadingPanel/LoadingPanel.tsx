import { Spinner, SpinnerSize } from "@fluentui/react";

import styles from "./LoadingPanel.module.css";

export const LoadingPanel = () => {
    return (
        <div className={styles.loaderContainer}>
            <Spinner className={styles.loader} size={SpinnerSize.large} label="Loading demo data..." />
        </div>
    );
};
