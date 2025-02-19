import styles from "./BotChatMessage.module.css";

import { Sparkle28Filled, CaretUp20Filled, CaretDown20Filled } from "@fluentui/react-icons";

export const BotChatMessageIcon = () => {
    return <Sparkle28Filled className={styles.botMessageIcon} aria-hidden="true" aria-label="Answer logo" />;
};

export const ShowMoreIcon = () => {
    return <CaretDown20Filled className={styles.botMessageIcon} aria-hidden="true" aria-label="Show more" />;
};

export const ShowLessIcon = () => {
    return <CaretUp20Filled className={styles.botMessageIcon} aria-hidden="true" aria-label="Show less" />;
};
