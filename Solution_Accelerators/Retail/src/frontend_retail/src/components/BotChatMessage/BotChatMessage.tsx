import styles from "./BotChatMessage.module.css";
import { useState } from "react";
import { Stack, ActionButton } from "@fluentui/react";
import { UIBotMessage, ProductResult } from "../../api";
import { BotChatMessageIcon, ShowMoreIcon, ShowLessIcon } from "./BotChatMessageIcon";
import { BotChatMessageProduct } from "./BotChatMessageProduct";

interface Props {
    botMessage: UIBotMessage;
    checkable: boolean;
    checkedResults: string[];
    isLast: boolean;
    onResultSelect: (productResult: ProductResult) => void;
    onResultDeselect: (productResult: ProductResult) => void;
    onResultDetailsClicked: (productResult: ProductResult) => void;
    onImageLoaded: () => void;
}

export const BotChatMessage = ({ botMessage, checkable, checkedResults, onResultSelect, onResultDeselect, onResultDetailsClicked, onImageLoaded }: Props) => {
    const [showMoreResults, setShowMoreResults] = useState<boolean>(false);

    const onShowMoreButtonToggled = () => setShowMoreResults(!showMoreResults);
    const showLessResultsCount = 3;
    const showMoreItemsText = showMoreResults ? "Show less" : "Show more";

    return (
        <div className={styles.container}>
            <Stack className={styles.message} verticalAlign="space-between">
                <Stack.Item>
                    <BotChatMessageIcon />
                </Stack.Item>

                <Stack.Item>
                    {botMessage.answer && (
                        <span className={styles.text}>
                            {botMessage.answer.introMessage}
                            <br /> <br />
                            <ul>
                                {botMessage.answer.items.map((item, i) => (
                                    <li style={{ display: !showMoreResults && i >= showLessResultsCount ? "none" : undefined }}>
                                        <b>{`• ${item.productName}`}</b>
                                        {`: ${item.description}`}
                                    </li>
                                ))}
                            </ul>
                            {botMessage.answer.items.length > showLessResultsCount && (
                                <ActionButton onClick={onShowMoreButtonToggled} title={showMoreItemsText}>
                                    {showMoreResults ? <ShowLessIcon /> : <ShowMoreIcon />}
                                    {`${showMoreItemsText}${showMoreResults ? "" : ` (${botMessage.answer.items.length - showLessResultsCount})`}`}
                                </ActionButton>
                            )}
                        </span>
                    )}
                </Stack.Item>

                <Stack.Item grow>
                    <div className={styles.productContainer}>
                        <Stack horizontal className={styles.scrollable}>
                            {botMessage.results &&
                                botMessage.results.map((result, _) => {
                                    const checked = checkedResults.some(articleId => articleId == result.id);
                                    return (
                                        <BotChatMessageProduct
                                            key={`BotChatMessageProduct_${result.id}`}
                                            checkable={checkable}
                                            checked={checked}
                                            result={result}
                                            onResultSelect={onResultSelect}
                                            onResultDeselect={onResultDeselect}
                                            onResultDetailsClicked={searchResult => onResultDetailsClicked(searchResult)}
                                            onImageLoaded={onImageLoaded}
                                        />
                                    );
                                })}
                        </Stack>
                    </div>
                </Stack.Item>
            </Stack>
        </div>
    );
};
