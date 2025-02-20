import { renderToStaticMarkup } from "react-dom/server";
import { ApproachType, ChatResponse, getCitationFilePath } from "../../api";

type HtmlParsedAnswer = {
    answerHtml: string;
    citations: string[];
    followupQuestions: string[];
    textToSpeak?: string;
    speaker_locale?: string;
};

export function parseAnswerToHtml(chatResponse: ChatResponse, onCitationClicked: (citationFilePath: string) => void): HtmlParsedAnswer {
    const citations: string[] = [];
    const followupQuestions: string[] = [];

    const textToSpeak = chatResponse.error ? undefined : chatResponse.answer.speak_answer;
    const speaker_locale = chatResponse.answer.speaker_locale;
    // Extract any follow-up questions that might be in the answer
    let parsedAnswer = chatResponse.answer.answer_string.replace(/<<<([^>>>]+)>>>/g, (match, content) => {
        followupQuestions.push(content);
        return "";
    });

    // trim any whitespace from the end of the answer after removing follow-up questions
    parsedAnswer = parsedAnswer.trim();

    var fragments: string[] = [];
    // Updated regex pattern to match double curly braces
    const parts = parsedAnswer.split(/\{\{([^\}]+)\}\}/g); // Updated regex pattern to match double curly braces
    fragments = parts.map((part, index) => {
        if (index % 2 === 0) {
            return part;
        } else {
            // Extract citations from answer
            let citationIndex: number;
            if (citations.indexOf(part) !== -1) {
                citationIndex = citations.indexOf(part) + 1;
            } else {
                citations.push(part);
                citationIndex = citations.length;
            }

            const path = getCitationFilePath(part);

            return renderToStaticMarkup(
                <a className="supContainer" title={part} onClick={() => onCitationClicked(path)}>
                    <sup>{citationIndex}</sup>
                </a>
            );
        }
    });

    // Return the parsed answer with citations and follow-up questions
    return {
        answerHtml: fragments.join(""),
        citations,
        followupQuestions,
        textToSpeak,
        speaker_locale
    };
}
