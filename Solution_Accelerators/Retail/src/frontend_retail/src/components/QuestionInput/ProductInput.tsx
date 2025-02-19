import styles from "./QuestionInput.module.css";

interface Props {
    id: string;
    imageUrl: string;
    name: string;
}

export const ProductInput = ({ id, imageUrl, name }: Props) => {
    return (
        <div id={id} className={styles.questionInputProduct} contentEditable={false}>
            <img src={imageUrl} alt={name} />
            <span>{name}</span>
        </div>
    );
};
