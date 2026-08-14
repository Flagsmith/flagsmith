import Constants from 'common/constants'

// A complete program: Go rejects unused variables, so a fragment that reads
// flags without printing them does not compile.
export default (envId, { FEATURE_NAME, FEATURE_NAME_ALT }) => `package main

import (
	"context"
	"fmt"
	flagsmith "github.com/Flagsmith/flagsmith-go-client/v5"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Initialise the Flagsmith client
	client := flagsmith.NewClient("${envId}"${
  Constants.isCustomFlagsmithUrl()
    ? `,\n\t\tflagsmith.WithBaseURL("${Constants.getFlagsmithSDKUrl()}")`
    : ''
})

	// The method below triggers a network request
	flags, _ := client.GetEnvironmentFlags(ctx)

	// Check whether the feature is enabled, or read its value
	isEnabled, _ := flags.IsFeatureEnabled("${FEATURE_NAME}")
	featureValue, _ := flags.GetFeatureValue("${FEATURE_NAME_ALT || FEATURE_NAME}")

	fmt.Println("${FEATURE_NAME} enabled:", isEnabled)
	fmt.Println("${FEATURE_NAME_ALT || FEATURE_NAME} value:", featureValue)
}
`
