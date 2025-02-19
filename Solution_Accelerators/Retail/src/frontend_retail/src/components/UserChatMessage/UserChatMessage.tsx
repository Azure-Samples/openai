import styles from "./UserChatMessage.module.css";

import { InputText, InputImage, InputProduct } from "../../api";
import { ProductInput } from "../QuestionInput/ProductInput";

interface Props {
    message: (InputText | InputImage | InputProduct)[];
}

export const UserChatMessage = ({ message }: Props) => {
    return (
        <div className={styles.container}>
            <div className={styles.message}>
                {message.map((input, index) => {
                    if (input.hasOwnProperty("text")) {
                        var textInput = input as InputText;
                        return (
                            <div key={`UserChatMessageText_${textInput.text}`} className={styles.text}>
                                {textInput.text === "\n" ? <br /> : textInput.text}
                            </div>
                        );
                    } else if (input.hasOwnProperty("imageUrl") && input.hasOwnProperty("imageName")) {
                        var imageInput = input as InputImage;
                        return (
                            <img
                                key={`UserChatMessageImage_${imageInput.imageUrl}`}
                                className={styles.image}
                                src={imageInput.imageUrl}
                                alt={imageInput.imageName}
                            />
                        );
                    } else if (input.hasOwnProperty("articleId") && input.hasOwnProperty("productImageUrl") && input.hasOwnProperty("productName")) {
                        var productInput = input as InputProduct;
                        return (
                            <ProductInput
                                key={`UserChatMessageProduct_${productInput.articleId}`}
                                id={productInput.articleId}
                                name={productInput.productName}
                                imageUrl={productInput.productImageUrl}
                            />
                        );
                    }
                })}
            </div>
        </div>
    );
};
