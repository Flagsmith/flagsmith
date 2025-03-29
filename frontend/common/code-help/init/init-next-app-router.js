import Constants from 'common/constants'
module.exports = (
  envId, 
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_CLIENT },
) => `// app/layout.tsx
import React from "react";
import ${LIB_NAME} from "${NPM_CLIENT}/isomorphic";
import { FeatureFlagProvider } from "./components/FeatureFlagProvider";

export default async function RootLayout({
  children,
}: Readonly&lt;{
  children: React.ReactNode;
}&gt;) {
  await flagsmith.init({
    environmentID: "${envId}",${
  Constants.isCustomFlagsmithUrl()
    ? `\n    api: "${Constants.getFlagsmithSDKUrl()}",\n`
    : ''
  }  });
  const serverState = flagsmith.getState();

  return (
    &lt;html lang="en"&gt;
      &lt;head&gt;
        &lt;meta name="viewport" content="initial-scale=1, width=device-width" /&gt;
      &lt;/head&gt;
      &lt;body&gt;
        &lt;FeatureFlagProvider serverState={serverState}&gt;
          {children}
        &lt;/FeatureFlagProvider&gt;
      &lt;/body&gt;
    &lt;/html&gt;
  );
}

// app/components/FeatureFlagProvider.tsx
"use client";

import { ReactNode, useRef } from "react";
import { FlagsmithProvider } from "flagsmith/react";
import { IState } from "flagsmith/types";
import { createFlagsmithInstance } from "flagsmith/isomorphic";

export const FeatureFlagProvider = ({
  serverState,
  children,
}: {
  serverState: IState;
  children: ReactNode;
}) =&gt; {
  const flagsmithInstance = useRef(createFlagsmithInstance());
  
  return (
    &lt;FlagsmithProvider flagsmith={flagsmithInstance.current} serverState={serverState}>
      &lt;&gt;{children}&lt;/&gt;
    &lt;/FlagsmithProvider&gt;
  );
};

// app/page.tsx
"use client";

import { useFlags } from 'flagsmith/react';

export default function HomePage() {
  const flags = useFlags(['${FEATURE_NAME}','${FEATURE_NAME_ALT}']); // only causes re-render if specified flag values / traits change
  const ${FEATURE_NAME} = flags.${FEATURE_NAME}.enabled
  const ${FEATURE_NAME_ALT} = flags.${FEATURE_NAME_ALT}.value
  
  return (
    &lt;&gt;{...}&lt;/&gt;
  );
}`
