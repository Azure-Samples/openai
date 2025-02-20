/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */
import { Spinner, SpinnerSize } from "@fluentui/react";

import styles from "./LoadingPanel.module.css";

type Props = {
    loadingMessage: string;
};

export const LoadingPanel = ({ loadingMessage }: Props) => {
    return (
        <div className={styles.loaderContainer}>
            <Spinner className={styles.loader} size={SpinnerSize.large} label={loadingMessage} />
        </div>
    );
};
