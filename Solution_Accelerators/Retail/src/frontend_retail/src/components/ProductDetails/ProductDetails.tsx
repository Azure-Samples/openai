import styles from "./ProductDetails.module.css";

import { ProductResult } from "../../api";

interface Props {
    result: ProductResult | null;
}

export const ProductDetails = ({ result }: Props) => {
    return (
        result && (
            <div className={styles.detailsContainer}>
                <img className={styles.detailsImage} alt={result.name} src={result.imageUrl} />
                <span className={styles.detailsTitle}>{result.name}</span>
                <div className={styles.detailsCategoryContainer}>
                    <span className={styles.detailsCategoryText}>{result.category}</span>
                    <span className={styles.detailsCategoryText}>{result.id}</span>
                </div>
                <span className={styles.detailsDescriptionText}>{result.description}</span>
                <div className={styles.attributesContainer}>
                    {result.attributes.map((attribute, _) => {
                        return (
                            <div key={`SidePanelAttribute_${attribute}`} className={styles.attribute}>
                                <span>{attribute}</span>
                            </div>
                        );
                    })}
                </div>
            </div>
        )
    );
};
