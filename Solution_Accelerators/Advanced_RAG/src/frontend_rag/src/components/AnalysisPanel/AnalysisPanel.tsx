/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */
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
    intermediateResponses: ChatResponse[];
}

const pivotItemDisabledStyle = { disabled: true, style: { color: "grey" } };

export const AnalysisPanel = ({
    chatResponse: answer,
    activeTab,
    activeCitation,
    citationHeight,
    className,
    onActiveTabChanged,
    intermediateResponses
}: Props) => {
    const isDisabledThoughtProcessTab: boolean = intermediateResponses.length === 0;
    const isDisabledSupportingContentTab: boolean = !answer.answer.data_points || answer.answer.data_points.length === 0;
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
                    {intermediateResponses.map((response, index) => (
                        <div key={index} className={styles.thoughtProcessItem}>
                            <div className={styles.thoughtProcessContent}>{response.answer.answer_string}</div>
                        </div>
                    ))}
                </div>
            </PivotItem>
            <PivotItem
                itemKey={AnalysisPanelTabs.SupportingContentTab}
                headerText="Supporting content"
                headerButtonProps={isDisabledSupportingContentTab ? pivotItemDisabledStyle : undefined}
            >
                <SupportingContent supportingContent={answer.answer.data_points || []} />
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
