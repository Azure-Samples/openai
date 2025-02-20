import styles from "./BotChatMessage.module.css";

import { ProductResult } from "../../api";

import { Checkbox, ImageLoadState, Image } from "@fluentui/react";

type Props = {
    checkable: boolean;
    checked: boolean;
    result: ProductResult;
    onResultSelect: (productResult: ProductResult) => void;
    onResultDeselect: (productResult: ProductResult) => void;
    onResultDetailsClicked: (productResult: ProductResult) => void;
    onImageLoaded: () => void;
};

export const BotChatMessageProduct = ({ checkable, checked, result, onResultSelect, onResultDeselect, onResultDetailsClicked, onImageLoaded }: Props) => {
    const onCheckBoxChange = (checked: boolean | undefined) => {
        if (checked) {
            onResultSelect(result);
        } else {
            onResultDeselect(result);
        }
    };

    const onImageLoadingStateChanged = (loadState: ImageLoadState) => {
        if (loadState === ImageLoadState.loaded) {
            onImageLoaded();
        }
    };

    return (
        <div title={result.description} className={styles.product}>
            <div>{checkable && <Checkbox className={styles.checkbox} onChange={(_, checked) => onCheckBoxChange(checked)} checked={checked} />}</div>
            <Image src={result.imageUrl} className={styles.productImage} onLoadingStateChange={loadState => onImageLoadingStateChanged(loadState)} />
            <span className={styles.title}>{result.name}</span>
            <span className={styles.category}>{result.category}</span>
            <div className={styles.detailsButton} onClick={() => onResultDetailsClicked(result)}>
                <span>Details</span>
            </div>
        </div>
    );
};
