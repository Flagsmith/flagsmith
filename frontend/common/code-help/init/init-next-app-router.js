import Constants from 'common/constants'
export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_CLIENT },
) => `// app/layout.tsx
import React from "react";
import ${LIB_NAME} from "${NPM_CLIENT}/isomorphic";
import { FeatureFlagProvider } from "./components/FeatureFlagProvider";

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  await flagsmith.init({
    environmentID: "${envId}",${
  Constants.isCustomFlagsmithUrl()
    ? `\n    api: "${Constants.getFlagsmithSDKUrl()}",\n`
    : ''
}  });
  const serverState = flagsmith.getState();

  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="initial-scale=1, width=device-width" />
      </head>
      <body>
        <FeatureFlagProvider serverState={serverState}>
          {children}
        </FeatureFlagProvider>
      </body>
    </html>
  );
}

// app/components/FeatureFlagProvider.tsx
"use client";

import { ReactNode, useRef } from "react";
import { FlagsmithProvider } from "@flagsmith/flagsmith/react";
import { IState } from "@flagsmith/flagsmith/types";
import { createFlagsmithInstance } from "@flagsmith/flagsmith/isomorphic";

export const FeatureFlagProvider = ({
  serverState,
  children,
}: {
  serverState: IState;
  children: ReactNode;
}) => {
  const flagsmithInstance = useRef(createFlagsmithInstance());
  
  return (
    <FlagsmithProvider flagsmith={flagsmithInstance.current} serverState={serverState}>
      <>{children}</>
    </FlagsmithProvider>
  );
};

// app/page.tsx
"use client";

import { useFlags } from '@flagsmith/flagsmith/react';

export default function HomePage() {
  const flags = useFlags(['${FEATURE_NAME}','${FEATURE_NAME_ALT}']); // only causes re-render if specified flag values / traits change
  const ${FEATURE_NAME} = flags.${FEATURE_NAME}.enabled
  const ${FEATURE_NAME_ALT} = flags.${FEATURE_NAME_ALT}.value
  
  return (
    <>{...}</>
  );
}`
