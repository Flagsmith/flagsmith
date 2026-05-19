import React, { FC } from 'react'
import CodeHelp from './CodeHelp'

const helloWorldSnippets = {
  '.NET': `using Flagsmith;

var client = new FlagsmithClient("YOUR_ENVIRONMENT_KEY");
Console.WriteLine("Hello, Flagsmith Warehouse!");`,
  'Flutter': `import 'package:flagsmith/flagsmith.dart';

final flagsmith = FlagsmithClient(apiKey: 'YOUR_ENVIRONMENT_KEY');
print('Hello, Flagsmith Warehouse!');`,
  'Go': `import (
    flagsmith "github.com/Flagsmith/flagsmith-go-client/v5"
)

client := flagsmith.NewClient("YOUR_ENVIRONMENT_KEY")
fmt.Println("Hello, Flagsmith Warehouse!")`,
  'Java': `import com.flagsmith.FlagsmithClient;

FlagsmithClient client = FlagsmithClient
    .newBuilder()
    .setApiKey("YOUR_ENVIRONMENT_KEY")
    .build();
System.out.println("Hello, Flagsmith Warehouse!");`,
  'JavaScript': `import flagsmith from 'flagsmith';

flagsmith.init({ environmentID: 'YOUR_ENVIRONMENT_KEY' });
console.log('Hello, Flagsmith Warehouse!');`,
  'Node JS': `import Flagsmith from 'flagsmith-nodejs';

const flagsmith = new Flagsmith({ environmentKey: 'YOUR_ENVIRONMENT_KEY' });
console.log('Hello, Flagsmith Warehouse!');`,
  'PHP': `use Flagsmith\\Flagsmith;

$flagsmith = new Flagsmith('YOUR_ENVIRONMENT_KEY');
echo "Hello, Flagsmith Warehouse!";`,
  'Python': `from flagsmith import Flagsmith

flagsmith = Flagsmith(environment_key="YOUR_ENVIRONMENT_KEY")
print("Hello, Flagsmith Warehouse!")`,
  'Ruby': `require "flagsmith"

flagsmith = Flagsmith::Client.new(environment_key: "YOUR_ENVIRONMENT_KEY")
puts "Hello, Flagsmith Warehouse!"`,
  'Rust': `use flagsmith::Flagsmith;

let flagsmith = Flagsmith::new("YOUR_ENVIRONMENT_KEY".to_string());
println!("Hello, Flagsmith Warehouse!");`,
  'iOS': `import FlagsmithClient

Flagsmith.shared.apiKey = "YOUR_ENVIRONMENT_KEY"
print("Hello, Flagsmith Warehouse!")`,
}

const WarehouseEventCodeHelp: FC = () => (
  <div>
    <p className='text-center fst-italic text-muted'>
      Verify your connection by sending your first custom event using one of our
      SDKs
    </p>
    <CodeHelp
      title='Send your first event'
      snippets={helloWorldSnippets}
      showInitially
      hideHeader
    />
  </div>
)

WarehouseEventCodeHelp.displayName = 'WarehouseEventCodeHelp'
export default WarehouseEventCodeHelp
