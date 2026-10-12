import React, { FC } from 'react'
import CodeHelp from 'components/CodeHelp'

const snippets: Record<string, string> = {
  'Flutter': `import 'package:flagsmith/flagsmith.dart';

final flagsmith = await FlagsmithClient.init(
  apiKey: 'YOUR_ENVIRONMENT_KEY',
  config: const FlagsmithConfig(enableEvents: true),
);
final user = Identity(identifier: 'user_42');

// Evaluates the flag and records an exposure
final flag = await flagsmith.getExperimentFlag('checkout_button', user: user);

// Records a conversion for the same identity
flagsmith.trackEvent('purchase', user: user, value: 99.5);`,
  'Go': `import (
    flagsmith "github.com/Flagsmith/flagsmith-go-client/v5"
)

client := flagsmith.NewClient("YOUR_ENVIRONMENT_KEY", flagsmith.WithEvents(ctx))
ec := flagsmith.NewEvaluationContext("user_42", nil)

// Evaluates the flag and records an exposure
flag, err := client.GetExperimentFlag(ctx, "checkout_button", ec)

// Records a conversion for the same identity
err = client.TrackEvent("purchase", &flagsmith.EventOptions{
    Identifier: "user_42",
    Value:      99.5,
})`,
  'Java': `import com.flagsmith.FlagsmithClient;
import com.flagsmith.config.FlagsmithConfig;
import com.flagsmith.models.BaseFlag;

FlagsmithClient flagsmith = FlagsmithClient
    .newBuilder()
    .setApiKey("YOUR_ENVIRONMENT_KEY")
    .withConfiguration(FlagsmithConfig.newBuilder().withEnableEvents(true).build())
    .build();

// Evaluates the flag and records an exposure
BaseFlag flag = flagsmith.getExperimentFlag("checkout_button", "user_42");

// Records a conversion for the same identity
flagsmith.trackEvent("purchase", "user_42", 99.5, null, null);`,
  'JavaScript': `import flagsmith from '@flagsmith/flagsmith';

await flagsmith.init({
  environmentID: 'YOUR_ENVIRONMENT_KEY',
  enableEvents: true,
});
await flagsmith.identify('user_42');

// Evaluates the flag and records an exposure
const flag = flagsmith.getExperimentFlag('checkout_button');

// Records a conversion for the same identity
flagsmith.trackEvent('purchase', { value: 99.5 });`,
  'Node JS': `import { Flagsmith } from '@flagsmith/nodejs';

const flagsmith = new Flagsmith({
  environmentKey: 'YOUR_ENVIRONMENT_KEY',
  enableEvents: true,
});

// Evaluates the flag and records an exposure
const flag = await flagsmith.getExperimentFlag('checkout_button', 'user_42');

// Records a conversion for the same identity
flagsmith.trackEvent('purchase', { identifier: 'user_42', value: 99.5 });`,
  'Python': `from flagsmith import Flagsmith

flagsmith = Flagsmith(
    environment_key="YOUR_ENVIRONMENT_KEY",
    enable_events=True,
)

# Evaluates the flag and records an exposure
flag = flagsmith.get_experiment_flag("checkout_button", identifier="user_42")

# Records a conversion for the same identity
flagsmith.track_event("purchase", identifier="user_42", value=99.5)`,
}

const WarehouseEventCodeHelp: FC = () => (
  <div>
    <p className='text-muted fw-bold'>
      Use our SDKs to send your first experimentation events.
    </p>
    <CodeHelp
      title='Send your first event'
      snippets={snippets}
      showInitially
      hideHeader
      hideDocs
    />
  </div>
)

WarehouseEventCodeHelp.displayName = 'WarehouseEventCodeHelp'
export default WarehouseEventCodeHelp
