import { useState, useEffect } from "react";

import { UserProfile, getAllUsers } from "../api";
import Chat from "./chat/Chat";
import { LoadingPanel } from "../components/LoadingPanel";
import { ErrorPanel } from "../components/ErrorPanel";

const PageContainer = () => {
    const [areUsersLoading, setAreUsersLoading] = useState<boolean>(true);
    const [usersError, setUsersError] = useState<unknown>();
    const [users, setUsers] = useState<UserProfile[]>([]);

    const processUsers = async () => {
        setAreUsersLoading(true);
        try {
            const users = await getAllUsers();
            setUsers(users);
            setUsersError(undefined);
        } catch (e) {
            setUsersError(e);
        } finally {
            setAreUsersLoading(false);
        }
    };

    useEffect(() => {
        processUsers();
    }, []);

    return (
        <div>
            {areUsersLoading ? (
                <LoadingPanel />
            ) : usersError ? (
                <ErrorPanel error={usersError.toString()} onRetry={() => processUsers()} />
            ) : (
                <Chat users={users} />
            )}
        </div>
    );
};

export default PageContainer;
