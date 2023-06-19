import { Label, Pivot, PivotItem } from "@fluentui/react";

import styles from "./AnalysisPanel.module.css";

import { SupportingContent } from "../SupportingContent";
import { ChatResponse } from "../../api";
import { AnalysisPanelTabs } from "./AnalysisPanelTabs";

interface Props {
    className: string;
    activeTab: AnalysisPanelTabs;
    onActiveTabChanged: (tab: AnalysisPanelTabs) => void;
    activeCitation: string | undefined;
    citationHeight: string;
    chatResponse: ChatResponse;
}

const pivotItemDisabledStyle = { disabled: true, style: { color: "grey" } };

export const AnalysisPanel = ({ chatResponse: answer, activeTab, activeCitation, citationHeight, className, onActiveTabChanged }: Props) => {
    const isDisabledThoughtProcessTab: boolean =
        !answer.classification && !answer.answer.query && !answer.answer.query_generation_prompt && !answer.answer.query_result;
    const isDisabledSupportingContentTab: boolean = !answer.data_points.length;
    const isDisabledCitationTab: boolean = !activeCitation;

    return (
        <Pivot
            className={className}
            selectedKey={activeTab}
            onLinkClick={pivotItem => pivotItem && onActiveTabChanged(pivotItem.props.itemKey! as AnalysisPanelTabs)}
        >
            <PivotItem
                itemKey={AnalysisPanelTabs.ThoughtProcessTab}
                headerText="Thought process"
                headerButtonProps={isDisabledThoughtProcessTab ? pivotItemDisabledStyle : undefined}
            >
                <div className={styles.thoughtProcess}>
                    <Label className={styles.thoughtProcessHeader}>Classification:</Label>
                    <Label className={styles.thoughtProcessParagraph}>{answer.classification}</Label>
                    {answer.answer.query_generation_prompt && <Label className={styles.thoughtProcessHeader}>Query Generation Prompt:</Label>}
                    {answer.answer.query_generation_prompt && <Label className={styles.thoughtProcessParagraph}>{answer.answer.query_generation_prompt}</Label>}
                    {answer.answer.query && <Label className={styles.thoughtProcessHeader}>Generated Query:</Label>}
                    {answer.answer.query && <Label className={styles.thoughtProcessParagraph}>{answer.answer.query}</Label>}
                    {answer.answer.query_result && <Label className={styles.thoughtProcessHeader}>Query Result:</Label>}
                    {answer.answer.query_result && <Label className={styles.thoughtProcessParagraph}>{answer.answer.query_result}</Label>}
                </div>
            </PivotItem>
            <PivotItem
                itemKey={AnalysisPanelTabs.SupportingContentTab}
                headerText="Supporting content"
                headerButtonProps={isDisabledSupportingContentTab ? pivotItemDisabledStyle : undefined}
            >
                <SupportingContent supportingContent={answer.data_points} />
            </PivotItem>
            <PivotItem
                itemKey={AnalysisPanelTabs.CitationTab}
                headerText="Citation"
                headerButtonProps={isDisabledCitationTab ? pivotItemDisabledStyle : undefined}
            >
                <iframe title="Citation" src={activeCitation} width="100%" height={citationHeight} />
            </PivotItem>
        </Pivot>
    );
};
