import { Text } from "@fluentui/react";
import { FluentIconsProps } from "@fluentui/react-icons";

import styles from "./TopBarButton.module.css";
import { ReactElement } from "react";

interface Props {
    className?: string;
    label: string;
    icon: ReactElement<FluentIconsProps>;
    onClick: () => void;
    disabled?: boolean;
}

export const TopBarButton = ({ className, label, icon, disabled, onClick }: Props) => {
    return (
        <div className={`${styles.container} ${className ?? ""} ${disabled && styles.disabled}`} onClick={onClick}>
            {icon}
            <Text>{label}</Text>
        </div>
    );
};
