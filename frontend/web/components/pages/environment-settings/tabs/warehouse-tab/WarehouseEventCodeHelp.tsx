import React, { FC } from 'react'
import CodeHelp from 'components/CodeHelp'

type SnippetEntry = {
  code: string
  enabled: boolean
}

const helloWorldSnippets: Record<string, SnippetEntry> = {
  '.NET': {
    code: `using Flagsmith;

var client = new FlagsmithClient("YOUR_ENVIRONMENT_KEY");
Console.WriteLine("Hello, Flagsmith Warehouse!");`,
    enabled: false,
  },
  'Flutter': {
    code: `import 'package:flagsmith/flagsmith.dart';

final flagsmith = FlagsmithClient(apiKey: 'YOUR_ENVIRONMENT_KEY');
print('Hello, Flagsmith Warehouse!');`,
    enabled: false,
  },
  'Go': {
    code: `import (
    flagsmith "github.com/Flagsmith/flagsmith-go-client/v5"
)

client := flagsmith.NewClient("YOUR_ENVIRONMENT_KEY")
fmt.Println("Hello, Flagsmith Warehouse!")`,
    enabled: false,
  },
  'Java': {
    code: `import com.flagsmith.FlagsmithClient;

FlagsmithClient client = FlagsmithClient
    .newBuilder()
    .setApiKey("YOUR_ENVIRONMENT_KEY")
    .build();
System.out.println("Hello, Flagsmith Warehouse!");`,
    enabled: false,
  },
  'JavaScript': {
    code: `import flagsmith from 'flagsmith';

await flagsmith.init({
  environmentID: 'YOUR_ENVIRONMENT_KEY',
  enableEvents: true,
});

flagsmith.trackEvent('purchase', {
  identifier: 'user_42',
  value: 99.5,
  traits: { plan: 'premium' },
  metadata: { source: 'web' },
});`,
    enabled: true,
  },
  'Node JS': {
    code: `import Flagsmith from 'flagsmith-nodejs';

const flagsmith = new Flagsmith({ environmentKey: 'YOUR_ENVIRONMENT_KEY' });
console.log('Hello, Flagsmith Warehouse!');`,
    enabled: false,
  },
  'PHP': {
    code: `use Flagsmith\\Flagsmith;

$flagsmith = new Flagsmith('YOUR_ENVIRONMENT_KEY');
echo "Hello, Flagsmith Warehouse!";`,
    enabled: false,
  },
  'Python': {
    code: `from flagsmith import Flagsmith

flagsmith = Flagsmith(
    environment_key="YOUR_ENVIRONMENT_KEY",
    enable_events=True,
)

flagsmith.track_event(
    "purchase",
    identifier="user_42",
    value=99.5,
    traits={"plan": "premium"},
    metadata={"source": "web"},
)`,
    enabled: true,
  },
  'Ruby': {
    code: `require "flagsmith"

flagsmith = Flagsmith::Client.new(environment_key: "YOUR_ENVIRONMENT_KEY")
puts "Hello, Flagsmith Warehouse!"`,
    enabled: false,
  },
  'Rust': {
    code: `use flagsmith::Flagsmith;

let flagsmith = Flagsmith::new("YOUR_ENVIRONMENT_KEY".to_string());
println!("Hello, Flagsmith Warehouse!");`,
    enabled: false,
  },
  'iOS': {
    code: `import FlagsmithClient

Flagsmith.shared.apiKey = "YOUR_ENVIRONMENT_KEY"
print("Hello, Flagsmith Warehouse!")`,
    enabled: false,
  },
}

const enabledSnippets = Object.fromEntries(
  Object.entries(helloWorldSnippets)
    .filter(([, entry]) => entry.enabled)
    .map(([name, entry]) => [name, entry.code]),
)

const WarehouseEventCodeHelp: FC = () => (
  <div>
    <p className='text-muted fw-bold'>
      Use our SDKs to send your first experimentation events.
    </p>
    <CodeHelp
      title='Send your first event'
      snippets={enabledSnippets}
      showInitially
      hideHeader
      hideDocs
    />
  </div>
)

WarehouseEventCodeHelp.displayName = 'WarehouseEventCodeHelp'
export default WarehouseEventCodeHelp
