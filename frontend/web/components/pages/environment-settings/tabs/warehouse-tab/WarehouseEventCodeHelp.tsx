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

// Records a conversion. Only the event name is required.
flagsmith.trackEvent(
  'purchase',
  user: user, // optional, defaults to the identified user
  value: 99.5, // optional
  traits: {'plan': 'premium'}, // optional
  metadata: {'source': 'app'}, // optional
);`,
  'Go': `import (
    "context"

    flagsmith "github.com/Flagsmith/flagsmith-go-client/v5"
)

ctx := context.Background()
client := flagsmith.NewClient("YOUR_ENVIRONMENT_KEY", flagsmith.WithEvents(ctx))
ec := flagsmith.NewEvaluationContext("user_42", nil)

// Evaluates the flag and records an exposure
flag, err := client.GetExperimentFlag(ctx, "checkout_button", ec)

// Records a conversion. Only the event name is required; opts may be nil.
err = client.TrackEvent("purchase", &flagsmith.EventOptions{
    Identifier: "user_42",                                 // optional, links the event to the exposure
    Value:      99.5,                                      // optional
    Traits:     map[string]interface{}{"plan": "premium"}, // optional
    Metadata:   map[string]interface{}{"source": "api"},   // optional
})`,
  'Java': `import com.flagsmith.FlagsmithClient;
import com.flagsmith.config.FlagsmithConfig;
import com.flagsmith.models.BaseFlag;
import java.util.Map;

FlagsmithClient flagsmith = FlagsmithClient
    .newBuilder()
    .setApiKey("YOUR_ENVIRONMENT_KEY")
    .withConfiguration(FlagsmithConfig.newBuilder().withEnableEvents(true).build())
    .build();

// Evaluates the flag and records an exposure
BaseFlag flag = flagsmith.getExperimentFlag("checkout_button", "user_42");

// Records a conversion. Only the event name is required.
// Overloads: trackEvent(event), trackEvent(event, identifier),
// trackEvent(event, identifier, value, traits, metadata).
flagsmith.trackEvent(
    "purchase",
    "user_42",                 // identifier, optional, links the event to the exposure
    99.5,                      // value, optional (or null)
    Map.of("plan", "premium"), // traits, optional (or null)
    Map.of("source", "api")    // metadata, optional (or null)
);`,
  'JavaScript': `import flagsmith from '@flagsmith/flagsmith';

await flagsmith.init({
  environmentID: 'YOUR_ENVIRONMENT_KEY',
  enableEvents: true,
});
await flagsmith.identify('user_42');

// Evaluates the flag and records an exposure
const flag = flagsmith.getExperimentFlag('checkout_button');

// Records a conversion. Only the event name is required.
flagsmith.trackEvent('purchase', {
  identifier: 'user_42', // optional, defaults to the identified user
  value: 99.5, // optional
  traits: { plan: 'premium' }, // optional
  metadata: { source: 'web' }, // optional
});`,
  'Node JS': `import { Flagsmith } from '@flagsmith/nodejs';

const flagsmith = new Flagsmith({
  environmentKey: 'YOUR_ENVIRONMENT_KEY',
  enableEvents: true,
});

// Evaluates the flag and records an exposure
const flag = await flagsmith.getExperimentFlag('checkout_button', 'user_42');

// Records a conversion. Only the event name is required.
flagsmith.trackEvent('purchase', {
  identifier: 'user_42', // optional, links the event to the exposure
  value: 99.5, // optional
  traits: { plan: 'premium' }, // optional
  metadata: { source: 'api' }, // optional
});`,
  'Python': `from flagsmith import Flagsmith

flagsmith = Flagsmith(
    environment_key="YOUR_ENVIRONMENT_KEY",
    enable_events=True,
)

# Evaluates the flag and records an exposure
flag = flagsmith.get_experiment_flag("checkout_button", identifier="user_42")

# Records a conversion. Only the event name is required.
flagsmith.track_event(
    "purchase",
    identifier="user_42",  # optional, links the event to the exposure
    value=99.5,  # optional
    traits={"plan": "premium"},  # optional
    metadata={"source": "api"},  # optional
)`,
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
