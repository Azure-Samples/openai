/*
 *   Copyright (c) 2024
 *   All rights reserved.
 */
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { initializeIcons } from "@fluentui/react";

import "./index.css";

import Layout from "./pages/layout/Layout";
import NoPage from "./pages/NoPage";
import PageContainer from "./pages/PageContainer";
import Login from "./pages/login/Login";
import { AuthenticatedTemplate, MsalProvider, UnauthenticatedTemplate, useMsal } from "@azure/msal-react";
import { PublicClientApplication } from "@azure/msal-browser";
import { msalConfig } from "./authConfig";

const msalInstance = new PublicClientApplication(msalConfig);

initializeIcons();

const Index = () => {
    return (
        <div>
            <UnauthenticatedTemplate>
                <Login />
            </UnauthenticatedTemplate>
            <AuthenticatedTemplate>
                <PageContainer />
            </AuthenticatedTemplate>
        </div>
    );
};

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Layout />}>
                    <Route
                        index
                        element={
                            <div>
                                <Index />
                            </div>
                        }
                    />
                    <Route path="*" element={<NoPage />} />
                </Route>
            </Routes>
        </BrowserRouter>
    );
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <MsalProvider instance={msalInstance}>
            <App />
        </MsalProvider>
    </React.StrictMode>
);
