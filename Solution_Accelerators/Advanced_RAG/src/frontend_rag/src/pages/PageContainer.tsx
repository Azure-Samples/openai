/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */
import { useState, useEffect } from "react";

import Chat from "./chat/Chat";
import { LoadingPanel } from "../components/LoadingPanel";
import { ErrorPanel } from "../components/ErrorPanel";
import { UserProfile, getUserProfiles } from "../api";

const PageContainer = () => {
    const [isDataLoading, setIsDataLoading] = useState<boolean>(true);
    const [dataError, setDataError] = useState<unknown>();

    const [userProfiles, setUserProfiles] = useState<UserProfile[]>([]);

    const fetchData = async () => {
        try {
            setIsDataLoading(true);
            setDataError(undefined);

            const userProfiles = await getUserProfiles();
            setUserProfiles(userProfiles);
        } catch (e) {
            setDataError(e);
        } finally {
            setIsDataLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    return (
        <div>
            {isDataLoading ? (
                <LoadingPanel loadingMessage="Loading Data..." />
            ) : dataError ? (
                <ErrorPanel error={dataError.toString()} onRetry={() => fetchData()} />
            ) : (
                <Chat userProfiles={userProfiles} />
            )}
        </div>
    );
};

export default PageContainer;
