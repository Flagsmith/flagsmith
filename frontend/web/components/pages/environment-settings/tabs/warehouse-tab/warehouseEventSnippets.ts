export const EVENTS_URL_PLACEHOLDER = '<your event ingestion service URL>'

export type SelfHostedUrls = {
  apiUrl: string
  eventsUrl: string
}

const optionalLines = (lines: string[] | false): string =>
  lines ? lines.map((line) => `\n${line}`).join('') : ''

export const getWarehouseEventSnippets = (
  selfHosted?: SelfHostedUrls,
): Record<string, string> => {
  const api = selfHosted?.apiUrl
  const events = selfHosted?.eventsUrl
  return {
    'Flutter': `// Requires flagsmith 6.2.0+
import 'package:flagsmith/flagsmith.dart';

final flagsmith = await FlagsmithClient.init(
  apiKey: 'YOUR_CLIENT_SIDE_ENVIRONMENT_KEY',
  config: const FlagsmithConfig(
    enableEvents: true,${optionalLines(
      !!selfHosted && [`    baseURI: '${api}',`, `    eventsURI: '${events}',`],
    )}
  ),
);
final user = Identity(identifier: 'user_42');

// Evaluates the flag and records an exposure
final flag = await flagsmith.getExperimentFlag('checkout_button', user: user);

// Records a conversion. Only the event name is required.
flagsmith.trackEvent(
  'purchase',
  user: user, // optional
  value: 99.5, // optional
  traits: {'plan': 'premium'}, // optional
  metadata: {'source': 'app'}, // optional
);

// Sends buffered events before the app closes, for example when it moves to the background
await flagsmith.flushEvents();`,
    'Go': `// Requires flagsmith-go-client/v5 5.3.0+
import (
    "context"
    "time"

    flagsmith "github.com/Flagsmith/flagsmith-go-client/v5"
)

ctx := context.Background()
eventsCtx, stopEvents := context.WithCancel(ctx)

client := flagsmith.NewClient("YOUR_ENVIRONMENT_KEY",
    flagsmith.WithEvents(eventsCtx),${optionalLines(
      !!selfHosted && [
        `    flagsmith.WithBaseURL("${api}"),`,
        `    flagsmith.WithEventsBaseURL("${events}"),`,
      ],
    )}
)
ec := flagsmith.NewEvaluationContext("user_42", nil)

// Evaluates the flag and records an exposure
flag, err := client.GetExperimentFlag(ctx, "checkout_button", ec)

// Records a conversion. Only the event name is required.
err = client.TrackEvent("purchase", &flagsmith.EventOptions{
    Identifier: "user_42",                                 // optional
    Value:      99.5,                                      // optional
    Traits:     map[string]interface{}{"plan": "premium"}, // optional
    Metadata:   map[string]interface{}{"source": "api"},   // optional
})

// Sends buffered events before your application exits
flushCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()
err = client.FlushEvents(flushCtx)
stopEvents()`,
    'Java': `// Requires flagsmith-java-client 8.2.0+
import com.flagsmith.FlagsmithClient;
import com.flagsmith.config.FlagsmithConfig;
import com.flagsmith.models.BaseFlag;
import java.util.Map;

FlagsmithClient flagsmith = FlagsmithClient
    .newBuilder()
    .setApiKey("YOUR_ENVIRONMENT_KEY")
    .withConfiguration(FlagsmithConfig.newBuilder()
        .withEnableEvents(true)${optionalLines(
          !!selfHosted && [
            `        .baseUri("${api}")`,
            `        .eventsUri("${events}")`,
          ],
        )}
        .build())
    .build();

// Evaluates the flag and records an exposure
BaseFlag flag = flagsmith.getExperimentFlag("checkout_button", "user_42");

// Records a conversion. Only the event name is required.
flagsmith.trackEvent(
    "purchase",
    "user_42",                 // identifier, optional
    99.5,                      // value, optional
    Map.of("plan", "premium"), // traits, optional
    Map.of("source", "api")    // metadata, optional
);

// Sends buffered events before your application exits
flagsmith.close();`,
    'JavaScript': `// Requires @flagsmith/flagsmith 12.4.0+
import flagsmith from '@flagsmith/flagsmith';

await flagsmith.init({
  environmentID: 'YOUR_CLIENT_SIDE_ENVIRONMENT_KEY',
  enableEvents: true,${optionalLines(
    !!selfHosted && [
      `  api: '${api}',`,
      `  eventProcessorConfig: { eventsApiUrl: '${events}' },`,
    ],
  )}
});
await flagsmith.identify('user_42');

// Evaluates the flag and records an exposure
const flag = flagsmith.getExperimentFlag('checkout_button');

// Records a conversion. Only the event name is required.
flagsmith.trackEvent('purchase', {
  value: 99.5, // optional
  traits: { plan: 'premium' }, // optional
  metadata: { source: 'web' }, // optional
});

// Sends buffered events before a server-side render responds, or before the page unloads
await flagsmith.flushEvents();`,
    'Node JS': `// Requires @flagsmith/nodejs 9.1.0+
import { Flagsmith } from '@flagsmith/nodejs';

const flagsmith = new Flagsmith({
  environmentKey: 'YOUR_ENVIRONMENT_KEY',
  enableEvents: true,${optionalLines(
    !!selfHosted && [
      `  apiUrl: '${api}',`,
      `  eventProcessorConfig: { eventsApiUrl: '${events}' },`,
    ],
  )}
});

// Evaluates the flag and records an exposure
const flag = await flagsmith.getExperimentFlag('checkout_button', 'user_42');

// Records a conversion. Only the event name is required.
flagsmith.trackEvent('purchase', {
  identifier: 'user_42', // optional
  value: 99.5, // optional
  traits: { plan: 'premium' }, // optional
  metadata: { source: 'api' }, // optional
});

// Sends buffered events before your application exits
await flagsmith.close();`,
    'Python': `# Requires flagsmith 6.3.0+
from flagsmith import ${selfHosted ? 'EventProcessorConfig, ' : ''}Flagsmith

flagsmith = Flagsmith(
    environment_key="YOUR_ENVIRONMENT_KEY",
    enable_events=True,${optionalLines(
      !!selfHosted && [
        `    api_url="${api}",`,
        `    event_processor_config=EventProcessorConfig(`,
        `        events_api_url="${events}",`,
        `    ),`,
      ],
    )}
)

# Buffered events are dropped when the interpreter exits. In short-lived scripts
# and jobs, pass max_buffer_items=1 to EventProcessorConfig so each event is sent
# as it is tracked.

# Evaluates the flag and records an exposure
flag = flagsmith.get_experiment_flag("checkout_button", identifier="user_42")

# Records a conversion. Only the event name is required.
flagsmith.track_event(
    "purchase",
    identifier="user_42",  # optional
    value=99.5,  # optional
    traits={"plan": "premium"},  # optional
    metadata={"source": "api"},  # optional
)`,
    'React': `// Requires @flagsmith/flagsmith 12.4.0+
import flagsmith from '@flagsmith/flagsmith';
import {
  FlagsmithProvider,
  useExperiment,
  useFlagsmith,
} from '@flagsmith/flagsmith/react';

export function App() {
  return (
    <FlagsmithProvider
      flagsmith={flagsmith}
      options={{
        environmentID: 'YOUR_CLIENT_SIDE_ENVIRONMENT_KEY',
        identity: 'user_42',
        enableEvents: true,${optionalLines(
          !!selfHosted && [
            `        api: '${api}',`,
            `        eventProcessorConfig: { eventsApiUrl: '${events}' },`,
          ],
        )}
      }}
    >
      <CheckoutButton />
    </FlagsmithProvider>
  );
}

function CheckoutButton() {
  const flagsmith = useFlagsmith();
  // Evaluates the flag and records an exposure. null until flags load.
  const flag = useExperiment('checkout_button');

  return (
    // Records a conversion. Only the event name is required.
    <button onClick={() => flagsmith.trackEvent('purchase', { value: 99.5 })}>
      {flag?.value === 'buy_now' ? 'Buy now' : 'Checkout'}
    </button>
  );
}`,
  }
}
