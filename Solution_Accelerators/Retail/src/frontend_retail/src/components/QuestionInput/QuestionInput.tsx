import styles from "./QuestionInput.module.css";

import { InputText, InputImage, UserInput, ProductResult, InputProduct } from "../../api";
import { ProductInput } from "./ProductInput";

import { ChangeEvent, KeyboardEvent, ClipboardEvent, useEffect, useRef, useState, MutableRefObject } from "react";
import ReactDOMServer from "react-dom/server";
import { Stack } from "@fluentui/react";
import { ImageAdd24Filled, Send28Filled } from "@fluentui/react-icons";

interface Props {
    onSend: (question: UserInput) => void;
    onSearchResultBackspaced: (articleId: string) => void;
    disableSend: boolean;
    addSearchResultToInput: MutableRefObject<((result: ProductResult) => void) | undefined>;
    removeSearchResultFromInput: MutableRefObject<((result: ProductResult) => void) | undefined>;
    imageAccept?: string[];
}

export const QuestionInput = ({
    onSend,
    onSearchResultBackspaced,
    disableSend,
    addSearchResultToInput,
    removeSearchResultFromInput,
    imageAccept = ["image/png", "image/jpeg"]
}: Props) => {
    const inputs = useRef<(InputText | InputImage | InputProduct)[]>([]);
    const textInput = useRef<string>(""); // To keep track of text input size
    const imageInput = useRef<InputImage[]>([]); // To keep track of number of images in input
    const [displayedInput, setDisplayedInput] = useState<string[]>([]); // We will use this to re-render the ContentEditable as images and products are added
    const [sendPayloadDisabled, setSendPayloadDisabled] = useState<boolean>(true); // We will use this to disable the send button when the input is empty or disabled by parent component
    const MAX_TEXT_LENGTH = 1000;
    const MAX_NUM_IMAGES = 5;

    useEffect(() => {
        updateSendPayloadDisabled();
    }, [disableSend]);

    useEffect(() => {
        scrollToLastChild();
    }, [displayedInput]);

    const sendPayload = () => {
        if (sendPayloadDisabled) {
            return;
        }

        onSend({ message: inputs.current } as UserInput);

        inputs.current = [];
        textInput.current = "";
        imageInput.current = [];

        if (displayedInput.length > 0) {
            setDisplayedInput([]);
        } else {
            const textInput = document.getElementById("textInput");

            if (textInput) {
                textInput.innerHTML = ""; // Manually clear the contenteditable since displayedInput is already empty and setting it to empty won't re-render the contenteditable
            }
        }

        updateSendPayloadDisabled();
    };

    const onKeyDown = (ev: KeyboardEvent<Element>) => {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            sendPayload();
            return;
        }

        // Only explicitly allow Ctrl+A, Ctrl+C, Ctrl+V, and Ctrl+X
        // This is to avoid things like Ctrl+B, which will change the format of the text
        if (ev.ctrlKey && !(ev.key === "a" || ev.key === "c" || ev.key === "v" || ev.key === "x")) {
            ev.preventDefault();
            return;
        }

        // If key press will introduce a unicode character, check if we are at the max text length
        if ((/^.$/u.test(ev.key) && !ev.ctrlKey) || (ev.shiftKey && ev.key === "Enter") || (ev.ctrlKey && ev.key === "v")) {
            if (textInput.current.length >= MAX_TEXT_LENGTH) {
                alert(`You may only enter up to ${MAX_TEXT_LENGTH} characters per message.`);
                ev.preventDefault();
                return;
            }
        }
    };

    const onTextChange = () => {
        var newInputs = [] as (InputText | InputImage | InputProduct)[];
        var newTextInput = "";
        var newImageInput = [] as InputImage[];
        const childNodes = document.getElementById("textInput")?.childNodes;

        if (!childNodes) {
            return;
        }

        for (var i = 0; i < childNodes.length; i++) {
            const node = childNodes[i];

            if (node instanceof HTMLImageElement) {
                newInputs.push({
                    imageName: node.alt,
                    imageUrl: node.src
                } as InputImage);
                newImageInput.push({
                    imageName: node.alt,
                    imageUrl: node.src
                } as InputImage);
            } else if (node.nodeType === Node.TEXT_NODE && node.textContent && node.textContent.length > 0) {
                newInputs.push({
                    text: node.textContent
                } as InputText);
                newTextInput += node.textContent;
            } else if (node instanceof HTMLDivElement) {
                const productInput = inputs.current[i] as InputProduct;
                newInputs.push(productInput);
            } else if (node.nodeType === Node.ELEMENT_NODE && node.nodeName == "BR" && i != childNodes.length - 1) {
                newInputs.push({
                    text: "\n"
                } as InputText);
                newTextInput += "\n";
            }
        }

        // If the new input is smaller than the old input, then we know that the user backspaced
        if (newInputs.length < inputs.current.length) {
            let deletedInputs = inputs.current.filter(
                input =>
                    !newInputs.find(newInput => {
                        if (newInput.hasOwnProperty("articleId") && input.hasOwnProperty("articleId")) {
                            return (newInput as InputProduct).articleId === (input as InputProduct).articleId;
                        } else if (newInput.hasOwnProperty("imageUrl") && input.hasOwnProperty("imageUrl")) {
                            return (newInput as InputImage).imageUrl === (input as InputImage).imageUrl;
                        } else if (newInput.hasOwnProperty("text") && input.hasOwnProperty("text")) {
                            return (newInput as InputText).text === (input as InputText).text;
                        } else {
                            return false;
                        }
                    })
            );

            // If the user backspaced a selected search result, we need to call the parent component's callback to uncheck the search result
            if (deletedInputs.length > 0) {
                for (const deletedInput of deletedInputs) {
                    if (deletedInput.hasOwnProperty("articleId")) {
                        onSearchResultBackspaced((deletedInput as InputProduct).articleId);
                    }
                }
            }
        }

        inputs.current = newInputs;
        textInput.current = newTextInput;
        imageInput.current = newImageInput;

        updateSendPayloadDisabled();
    };

    const scrollToLastChild = () => {
        const children = document.getElementById("textInput")?.children;

        if (children && children.length > 0) {
            const lastChild = children[children.length - 1];
            if (lastChild != undefined) {
                lastChild.scrollIntoView({ behavior: "instant" as ScrollBehavior, block: "end" });
            }
        }
    };

    const tryAddImagesToInput = (files: FileList | null): boolean => {
        if (!files) {
            return false;
        }

        if (imageInput.current.length + files.length > MAX_NUM_IMAGES) {
            alert(`You may only upload up to ${MAX_NUM_IMAGES} images per message.`);
            return false;
        }

        for (let i = 0; i < files.length; i++) {
            const file = files.item(i);

            if (!file || !imageAccept.includes(file.type)) {
                continue;
            }

            const url = URL.createObjectURL(file);
            const newImageInput = { imageName: file.name, imageUrl: url } as InputImage;
            inputs.current.push(newImageInput);
            imageInput.current.push(newImageInput);
            updateDisplayedInput();
        }

        return true;
    };

    const onImageChange = (ev: ChangeEvent<HTMLInputElement>) => {
        const files = ev.target.files;
        const imagesAdded = tryAddImagesToInput(files);
        const imageInputElement = document.getElementById("imageInput") as HTMLInputElement;

        if (imageInputElement) {
            imageInputElement.value = ""; // Clear input value so the same image may be uploaded multiple times
        }

        if (!imagesAdded) {
            ev.preventDefault();
            return;
        }

        updateSendPayloadDisabled();
    };

    const onProductAdd = (result: ProductResult) => {
        const newInput = { articleId: result.id, productName: result.name, productImageUrl: result.imageUrl } as InputProduct;
        inputs.current.push(newInput);
        updateDisplayedInput();
        updateSendPayloadDisabled();
    };

    const onProductRemove = (result: ProductResult) => {
        const index = inputs.current.findIndex(element => {
            return element.hasOwnProperty("articleId") && (element as InputProduct).articleId === result.id;
        });

        if (index >= 0) {
            inputs.current.splice(index, 1);
            updateDisplayedInput();
            updateSendPayloadDisabled();
        }
    };

    addSearchResultToInput.current = onProductAdd;
    removeSearchResultFromInput.current = onProductRemove;

    const escapeForHTML = (text: string) => {
        return text.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/\n/g, "<br/>");
    };

    const updateDisplayedInput = () => {
        var newDisplayedInput = [];

        for (var i = 0; i < inputs.current.length; i++) {
            const inputElement = inputs.current[i];
            if (inputElement.hasOwnProperty("imageUrl") && inputElement.hasOwnProperty("imageName")) {
                const image = inputElement as InputImage;
                newDisplayedInput.push(`<img key=${i} src=${image.imageUrl} alt=${image.imageName} />`);
            } else if (inputElement.hasOwnProperty("text")) {
                // Escape HTML tags to avoid displaying HTML format in text input, we only want to allow plain text
                const text = inputElement as InputText;
                const escapedText = escapeForHTML(text.text);
                newDisplayedInput.push(escapedText);
            } else if (
                inputElement.hasOwnProperty("articleId") &&
                inputElement.hasOwnProperty("productName") &&
                inputElement.hasOwnProperty("productImageUrl")
            ) {
                const product = inputElement as InputProduct;
                const htmlString = ReactDOMServer.renderToString(
                    // We need to add a unique id to each ProductInput so that React can differentiate between them during state changes
                    <ProductInput id={`div_ ${new Date().getTime().toString()}`} imageUrl={product.productImageUrl} name={product.productName} />
                );
                newDisplayedInput.push(htmlString);
            }
        }

        setDisplayedInput(newDisplayedInput);
    };

    const onPaste = (ev: ClipboardEvent<HTMLDivElement>) => {
        // For now, prevent pasting anything into the contenteditable.
        // This is to avoid allowing formatted text to be pasted into the input,
        // as well as to avoid having to keep track of where the caret is at in the contenteditable at the moment,
        // and to then have to figure out where that is relative to the input list.
        ev.preventDefault();
    };

    const updateSendPayloadDisabled = () => {
        setSendPayloadDisabled(disableSend || inputs.current.length == 0);
    };

    return (
        <Stack horizontal className={styles.questionInputContainer}>
            <div className={styles.buttonContainer}>
                <input
                    id="imageInput"
                    type="file"
                    aria-label="Upload image button"
                    className={styles.imageInput}
                    multiple={true}
                    onChange={onImageChange}
                    accept={imageAccept.join(",")}
                />
                <label htmlFor="imageInput" className={styles.button}>
                    <ImageAdd24Filled />
                </label>
            </div>
            <div
                id="textInput"
                contentEditable={true}
                className={styles.questionInputTextArea}
                onInput={onTextChange}
                onKeyDown={onKeyDown}
                onPaste={onPaste}
                dangerouslySetInnerHTML={{ __html: displayedInput.join("") }}
            />
            <div className={styles.buttonContainer}>
                <div className={`${sendPayloadDisabled ? styles.disabledButton : styles.button}`} aria-label="Send payload button" onClick={sendPayload}>
                    <Send28Filled />
                </div>
            </div>
        </Stack>
    );
};
