"use client";

import {
  PublicClientApplication,
  type Configuration,
  LogLevel,
} from "@azure/msal-browser";

const msalConfig: Configuration = {
  auth: {
    clientId: process.env.NEXT_PUBLIC_AZURE_CLIENT_ID ?? "",
    authority: process.env.NEXT_PUBLIC_AZURE_AUTHORITY ?? "",
    redirectUri:
      process.env.NEXT_PUBLIC_AZURE_REDIRECT_URI ??
      (typeof window !== "undefined" ? window.location.origin : ""),
    postLogoutRedirectUri: "/",
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii || process.env.NODE_ENV !== "development") return;
        console.log(`[MSAL ${LogLevel[level]}]`, message);
      },
    },
  },
};

export const msalInstance = new PublicClientApplication(msalConfig);

export const loginRequest = {
  scopes: ["openid", "profile", "email"],
};
