import "./index.css";

import React from "react";
import ReactDOM from "react-dom/client";
import { initializeIcons } from "@fluentui/react";

import PageContainer from "./pages/PageContainer";
import Login from "./pages/login/Login";
import { AuthenticatedTemplate, MsalProvider, UnauthenticatedTemplate } from "@azure/msal-react";
import { PublicClientApplication } from "@azure/msal-browser";
import { msalConfig } from "./authConfig";

const msalInstance = new PublicClientApplication(msalConfig);

initializeIcons();

export default function App() {
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
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
        <MsalProvider instance={msalInstance}>
            <App />
        </MsalProvider>
    </React.StrictMode>
);
