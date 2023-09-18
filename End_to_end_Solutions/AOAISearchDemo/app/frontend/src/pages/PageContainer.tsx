import { useState, useEffect } from "react";

import { SearchSettings, UserProfile, getAllUsers, getSearchSettings } from "../api";
import Chat from "./chat/Chat";
import { LoadingPanel } from "../components/LoadingPanel";
import { ErrorPanel } from "../components/ErrorPanel";

const PageContainer = () => {
    const [isDataLoading, setIsDataLoading] = useState<boolean>(true);
    const [dataError, setDataError] = useState<unknown>();
    const [users, setUsers] = useState<UserProfile[]>([]);
    const [searchSettings, setSearchSettings] = useState<SearchSettings>({ vectorization_enabled: false });

    const fetchData = async () => {
        try {
            const users = await getAllUsers();
            const searchSettings = await getSearchSettings();
            setUsers(users);
            setSearchSettings(searchSettings);
            setDataError(undefined);
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
                <LoadingPanel />
            ) : dataError ? (
                <ErrorPanel error={dataError.toString()} onRetry={() => fetchData()} />
            ) : (
                <Chat users={users} searchSettings={searchSettings} />
            )}
        </div>
    );
};

export default PageContainer;
