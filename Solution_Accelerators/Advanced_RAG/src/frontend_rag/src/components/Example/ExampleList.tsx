import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

interface Props {
    onExampleClicked: (value: string) => void;
    examples: string[];
}

export const ExampleList = ({ onExampleClicked, examples }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {examples.map((example, i) => (
                <li key={i}>
                    <Example text={example} value={example} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
