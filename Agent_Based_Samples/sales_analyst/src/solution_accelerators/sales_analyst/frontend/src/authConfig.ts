// MSAL configuration for Azure AD authentication
// Replace the placeholder values with your actual Azure AD app registration details
import { Configuration } from '@azure/msal-browser';

export const msalConfig: Configuration = {
  auth: {
    clientId: process.env.REACT_APP_CLIENT_ID || '', // Use new env var
    authority: `https://login.microsoftonline.com/${process.env.REACT_APP_TENANT_ID || 'common'}`,
    redirectUri: "http://localhost:3000", // Ensures redirect returns to your app
  },
  cache: {
    cacheLocation: 'sessionStorage', // or 'localStorage' for persistent login
    storeAuthStateInCookie: false, // Set to true if issues on IE11/Edge
  },
};