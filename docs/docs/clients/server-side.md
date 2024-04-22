---
description: Manage your Feature Flags and Remote Config in your Server Side Applications.
sidebar_label: Server Side
sidebar_position: 2
---

import Tabs from '@theme/Tabs'; import TabItem from '@theme/TabItem';

# Server Side SDKs

:::tip

Server Side SDKs can run in 2 different modes: `Local Evaluation` and `Remote Evaluation`. We recommend
[reading up about the differences](/clients/overview#server-side-sdks) first before integrating the SDKS into your
applications.

:::

## SDK Overview

<Tabs groupId="language" queryString>
<TabItem value="python" label="Python">

- Version Compatibility: **Python 3.8+**
- Source Code: https://github.com/Flagsmith/flagsmith-python-client

</TabItem>
<TabItem value="java" label="Java">

- Version Compatibility: **JDK 11+**
- Source Code: https://github.com/Flagsmith/flagsmith-java-client

</TabItem>
<TabItem value="dotnet" label=".NET">

- Version Compatibility: **.NET core 6.0+**
- Source Code: https://github.com/Flagsmith/flagsmith-dotnet-client

</TabItem>
<TabItem value="nodejs" label="NodeJS">

- Version Compatibility: **Node 14+**
- Source Code:
  - https://github.com/Flagsmith/flagsmith-nodejs-client

</TabItem>
<TabItem value="ruby" label="Ruby">

- Version Compatibility: **Ruby 2.4+**
- Source Code: https://github.com/Flagsmith/flagsmith-ruby-client

</TabItem>
<TabItem value="php" label="PHP">

- Version Compatibility: **php 7.4+**
- Source Code: https://github.com/Flagsmith/flagsmith-php-client

</TabItem>
<TabItem value="go" label="Go">

- Version Compatibility: **Go 1.18+**
- Source Code: https://github.com/Flagsmith/flagsmith-go-client

</TabItem>
<TabItem value="rust" label="Rust">

- Version Compatibility: **2021 edition (1.56.0)+**
- Source Code: https://github.com/Flagsmith/flagsmith-rust-client

</TabItem>
<TabItem value="elixir" label="Elixir">

- Version Compatibility: **Elixir 1.12+**
- Source Code: https://github.com/Flagsmith/flagsmith-elixir-client

</TabItem>
</Tabs>

## Add the Flagsmith package

<Tabs groupId="language">
<TabItem value="python" label="Python">

```bash
pip install flagsmith
```

</TabItem>
<TabItem value="java" label="Java">

```xml
# Check https://search.maven.org/artifact/com.flagsmith/flagsmith-java-client
# for the latest version!

# Maven
<dependency>
  <groupId>com.flagsmith</groupId>
  <artifactId>flagsmith-java-client</artifactId>
  <version>7.2.0</version>
</dependency>

# Gradle
implementation 'com.flagsmith:flagsmith-java-client:7.2.0'
```

</TabItem>
<TabItem value="dotnet" label=".NET">

```bash
# Check https://www.nuget.org/packages/Flagsmith for the latest version!

# Package Manager
Install-Package Flagsmith -Version 5.2.2

#.NET CLI
dotnet add package Flagsmith --version 5.2.2

# PackageReference
<PackageReference Include="Flagsmith" Version="5.2.2" />

# Paket CLI
paket add Flagsmith --version 5.2.2
```

</TabItem>
<TabItem value="nodejs" label="NodeJS">

```bash
# Via NPM
npm i flagsmith-nodejs --save
```

</TabItem>
<TabItem value="ruby" label="Ruby">

```ruby
gem install flagsmith
```

</TabItem>
<TabItem value="php" label="PHP">

```bash
# Requires PHP 7.4 or newer and ships with GuzzleHTTP.
composer require flagsmith/flagsmith-php-client

# You can optionally provide your own implementation of PSR-18 and PSR-16.
# You will also need some implementation of PSR-18 and PSR-17,
# for example Guzzle and PSR-16, for example Symfony Cache.
composer require flagsmith/flagsmith-php-client guzzlehttp/guzzle symfony/cache

# or
composer require flagsmith/flagsmith-php-client symfony/http-client nyholm/psr7 symfony/cache
```

</TabItem>
<TabItem value="go" label="Go">

```bash
# Check https://github.com/Flagsmith/flagsmith-go-client/releases for the latest version!

go get github.com/Flagsmith/flagsmith-go-client/v3
```

</TabItem>
<TabItem value="rust" label="Rust">

```bash
# Check https://crates.io/crates/flagsmith/versions for the latest version!

# Cargo.toml
[dependencies]
flagsmith = "~1"
```

</TabItem>
<TabItem value="elixir" label="Elixir">

```elixir
def deps do
  [
    {:flagsmith_engine, "~> 1.0"}
  ]
end
```

</TabItem>
</Tabs>

## Initialise the SDK

:::tip

Server-side SDKs must be initialised with Server-side Environment keys. These can be created in the Environment settings
area and should be considered secret.

:::

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
from flagsmith import Flagsmith

flagsmith = Flagsmith(
    environment_key = "FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY"
)
```

</TabItem>
<TabItem value="java" label="Java">

```java
private static FlagsmithClient flagsmith = FlagsmithClient
    .newBuilder()
    .setApiKey(System.getenv("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY"))
    .build();
```

</TabItem>
<TabItem value="dotnet" label=".NET">

```csharp
using Flagsmith;

FlagsmithClient _flagsmithClient;

_flagsmithClient = new("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY");
```

</TabItem>
<TabItem value="nodejs" label="NodeJS">

```javascript
const Flagsmith = require('flagsmith-nodejs');

const flagsmith = new Flagsmith({
 environmentKey: 'FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY',
});
```

</TabItem>
<TabItem value="ruby" label="Ruby">

```ruby
require "flagsmith"

$flagsmith = Flagsmith::Client.new(
  environment_key: 'FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY'
)
```

</TabItem>
<TabItem value="php" label="PHP">

```php
use Flagsmith\Flagsmith;

$flagsmith = new Flagsmith('FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY');
```

</TabItem>
<TabItem value="go" label="Go">

```go
import (
  "os"
  flagsmith "github.com/Flagsmith/flagsmith-go-client/v3"
)
// Initialise the Flagsmith client
client := flagsmith.NewClient(os.Getenv("FLAGSMITH_ENVIRONMENT_KEY"))
```

</TabItem>
<TabItem value="rust" label="Rust">

```rust
use std::env;
use flagsmith::{Flag, Flagsmith, FlagsmithOptions};

let options = FlagsmithOptions {..Default::default()};
let flagsmith = Flagsmith::new(
        env::var("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY")
            .expect("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY not found in environment"),
        options,
    );
```

</TabItem>
<TabItem value="elixir" label="Elixir">

```elixir
client_configuration = Flagsmith.Client.new(environment_key: "MY_SDK_KEY")
```

Or use global configuration in which case you don't need to create a client or pass configuration options to requests.
All configuration is optional with exception of the `:environment_key`. For instance in `config/config.exs`:

```elixir
config :flagsmith_engine, :configuration,
       environment_key: "<YOUR SDK KEY>",
       api_url: "https://edge.api.flagsmith.com/api/v1>",
       default_flag_handler: function_defaults_to_not_found,
       custom_headers: [{"to add to", "the requests"}],
       request_timeout_milliseconds: 5000,
       enable_local_evaluation: false,
       environment_refresh_interval_milliseconds: 60_000,
       retries: 0,
       enable_analytics: false
```

</TabItem>
</Tabs>

## Get Flags for an Environment

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
# The method below triggers a network request
flags = flagsmith.get_environment_flags()
show_button = flags.is_feature_enabled("secret_button")
button_data = json.loads(flags.get_feature_value("secret_button"))
```

</TabItem>
<TabItem value="java" label="Java">

```java
Flags flags = flagsmith.getEnvironmentFlags();
Boolean showButton = flags.isFeatureEnabled(featureName);
Object value = flags.getFeatureValue(featureName);
```

</TabItem>
<TabItem value="dotnet" label=".NET">

```csharp
# Sync
# The method below triggers a network request
var flags = _flagsmithClient.GetEnvironmentFlags().Result;  # This method triggers a network request
var showButton = flags.IsFeatureEnabled("secret_button").Result;
var buttonData = flags.GetFeatureValue("secret_button").Result;

# Async
# The method below triggers a network request
var flags = await _flagsmithClient.GetEnvironmentFlags();  # This method triggers a network request
var showButton = await flags.IsFeatureEnabled("secret_button");
var buttonData = await flags.GetFeatureValue("secret_button");
```

</TabItem>
<TabItem value="nodejs" label="NodeJS">

```javascript
const flags = await flagsmith.getEnvironmentFlags();
var showButton = flags.isFeatureEnabled('secret_button');
var buttonData = flags.getFeatureValue('secret_button');
```

</TabItem>
<TabItem value="ruby" label="Ruby">

```ruby
$flags = $flagsmith.get_environment_flags()
$show_button = $flags.is_feature_enabled('secret_button')
$button_data = $flags.get_feature_value('secret_button')
```

</TabItem>
<TabItem value="php" label="PHP">

```php
$flags = $flagsmith->getEnvironmentFlags();
$flags->isFeatureEnabled('secret_button');
$flags->getFeatureValue('secret_button');
```

</TabItem>
<TabItem value="go" label="Go">

```go
// The method below triggers a network request
flags, _ := client.GetEnvironmentFlags(ctx)
showButton, _ := flags.IsFeatureEnabled("secret_button")
buttonData, _ := flags.GetFeatureValue("secret_button")
```

</TabItem>
<TabItem value="rust" label="Rust">

```rust
// The method below triggers a network request
let flags = flagsmith.get_environment_flags().unwrap();

let show_button = flags.is_feature_enabled("secret_button").unwrap();

let button_data = flags.get_feature_value_as_string("secret_button").unwrap();
```

</TabItem>
<TabItem value="elixir" label="Elixir">

```elixir
# The method below triggers a network request
{:ok, %Flagsmith.Schemas.Flags{} = flags} = Flagsmith.Client.get_environment_flags(client_configuration)

secret_button_enabled? = Flagsmith.Client.is_feature_enabled(flags, "secret_button")
secret_button_feature_value = Flagsmith.Client.get_feature_value(flags, "secret_button")
```

</TabItem>
</Tabs>

## Get Flags for an Identity

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
identifier = "delboy@trotterstraders.co.uk"
traits = {"car_type": "robin_reliant"}

# The method below triggers a network request
identity_flags = flagsmith.get_identity_flags(identifier=identifier, traits=traits)
show_button = identity_flags.is_feature_enabled("secret_button")
button_data = json.loads(identity_flags.get_feature_value("secret_button"))
```

</TabItem>
<TabItem value="java" label="Java">

```java
String identifier = "delboy@trotterstraders.co.uk"
Map<String, Object> traits = new HashMap<String, Object>();
traits.put("car_type", "robin_reliant");

// The method below triggers a network request
Flags flags = flagsmith.getIdentityFlags(identifier, traits);
Boolean showButton = flags.isFeatureEnabled(featureName);
Object value = flags.getFeatureValue(featureName);
```

</TabItem>
<TabItem value="dotnet" label=".NET">

```csharp
var identifier = "delboy@trotterstraders.co.uk";
var traitKey = "car_type";
var traitValue = "robin_reliant";
var traitList = new List<Trait> { new Trait(traitKey, traitValue) };

# Sync
# The method below triggers a network request
var flags = _flagsmithClient.GetIdentityFlags(identifier, traitList).Result;
var showButton = flags.IsFeatureEnabled("secret_button").Result;

# Async
# The method below triggers a network request
var flags = await _flagsmithClient.GetIdentityFlags(identifier, traitList);
var showButton = await flags.IsFeatureEnabled("secret_button");
```

</TabItem>
<TabItem value="nodejs" label="NodeJS">

```javascript
const identifier = 'delboy@trotterstraders.co.uk';
const traitList = { car_type: 'robin_reliant' };

const flags = await flagsmith.getIdentityFlags(identifier, traitList);
var showButton = flags.isFeatureEnabled('secret_button');
var buttonData = flags.getFeatureValue('secret_button');
```

</TabItem>
<TabItem value="ruby" label="Ruby">

```ruby
$identifier = 'delboy@trotterstraders.co.uk'
$traits = {'car_type': 'robin_reliant'}

$flags = $flagsmith.get_identity_flags($identifier, **$traits)
$show_button = $flags.is_feature_enabled('secret_button')
$button_data = $flags.get_feature_value('secret_button')
```

</TabItem>
<TabItem value="php" label="PHP">

```php
$identifier = 'delboy@trotterstraders.co.uk';
$traits = (object) [ 'car_type' => 'robin_reliant' ];

$flags = $flagsmith->getIdentityFlags($identifier, $traits);
$showButton = $flags->isFeatureEnabled('secret_button');
$buttonData = $flags->getFeatureValue('secret_button');
```

</TabItem>
<TabItem value="go" label="Go">

```go
trait := flagsmith.Trait{TraitKey: "trait", TraitValue: "trait_value"}
traits = []*flagsmith.Trait{&trait}

// The method below triggers a network request
flags, _ := client.GetIdentityFlags(ctx, identifier, traits)

showButton, _ := flags.IsFeatureEnabled("secret_button")
buttonData, _ := flags.GetFeatureValue("secret_button")
```

</TabItem>
<TabItem value="rust" label="Rust">

```rust
use flagsmith_flag_engine::identities::Trait;
use flagsmith_flag_engine::types::{FlagsmithValue, FlagsmithValueType};

let identifier = "delboy@trotterstraders.co.uk";

let traits = vec![Trait {
            trait_key: "car_type".to_string(),
            trait_value: FlagsmithValue {
                value: "robin_reliant".to_string(),
                value_type: FlagsmithValueType::String,
            },
        }];

// The method below triggers a network request
let identity_flags = flagsmith.get_identity_flags(identifier, Some(traits)).unwrap();

let show_button = identity_flags.is_feature_enabled("secret_button").unwrap();
let button_data = identity_flags.get_feature_value_as_string("secret_button").unwrap();
```

</TabItem>
<TabItem value="elixir" label="Elixir">

```elixir
# The method below triggers a network request
{:ok, flags} = Flagsmith.Client.get_identity_flags(
      client_configuration,
      "user-a",
      [%{trait_key: "is_subscribed", trait_value: false}]
)

secret_button_enabled? = Flagsmith.Client.is_feature_enabled(flags, "secret_button")
secret_button_feature_value = Flagsmith.Client.get_feature_value(flags, "secret_butteon")
```

</TabItem>
</Tabs>

### When running in [Remote Evaluation mode](/clients/overview#remote-evaluation)

- When requesting Flags for an Identity, all the Traits defined in the SDK will automatically be persisted against the
  Identity within the Flagsmith API.
- Traits passed to the SDK will be added to all the other previously persisted Traits associated with that Identity.
- This full set of Traits are then used to evaluate the Flag values for the Identity.
- This all happens in a single request/response.

### When running in [Local Evaluation mode](/clients/overview#local-evaluation)

- _Only_ the Traits provided to the SDK at runtime will be used. Local Evaluation mode, by design, does not make any
  network requests to the Flagsmith API when evaluating Flags for an Identity.
  - When running in Local Evaluation Mode, the SDK requests the
    [Environment Document](/clients/overview#the-environment-document) from the Flagsmith API. This contains all the
    information required to make Flag Evaluations, but it does _not_ contain any Trait data.

## Managing Default Flags

Default Flags are configured by passing in a function that is called when a Flag cannot be found or if the network
request to the API fails when retrieving flags.

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
from flagsmith import Flagsmith
from flagsmith.models import DefaultFlag

def default_flag_handler(feature_name: str) -> DefaultFlag:
    """
    Function that will be used if the API doesn't respond, or an unknown
    feature is requested
    """
    if feature_name == "secret_button":
        return DefaultFlag(
            enabled=False,
            value=json.dumps({"colour": "#b8b8b8"}),
            feature_name="secret_button",
        )
    ],
    return DefaultFlag(False, None)

flagsmith = Flagsmith(
    environment_key="FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY",
    default_flag_handler=default_flag_handler,
)
```

</TabItem>
<TabItem value="java" label="Java">

```java
private static FlagsmithClient flagsmith = FlagsmithClient
    .newBuilder()
    .setDefaultFlagValueFunction(HelloController::defaultFlagHandler)
    .setApiKey(System.getenv("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY"))
    .build();

private static DefaultFlag defaultFlagHandler(String featureName) {
    DefaultFlag flag = new DefaultFlag();
    flag.setEnabled(Boolean.FALSE);

    if (featureName.equals("secret_button")) {
        flag.setValue("{\"colour\": \"#ababab\"}");
    } else {
        flag.setValue(null);
    }

    return flag;
}
```

</TabItem>
<TabItem value="dotnet" label=".NET">

```csharp
using Flagsmith;

FlagsmithClient _flagsmithClient;
_flagsmithClient = new("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY", defaultFlagHandler: defaultFlagHandler);

static Flag defaultFlagHandler(string featureName)
{
    // Function that will be used if the API doesn't respond, or an unknown
    // feature is requested
    if (featureName == "secret_button")
        return new Flag(new Feature("secret_button"), enabled: false, value: JsonConvert.SerializeObject(new { colour = "#b8b8b8" }).ToString());
    else return new Flag() { };
}
```

</TabItem>
<TabItem value="nodejs" label="NodeJS">

```javascript
const flagsmith = new Flagsmith({
 environmentKey,
 enableLocalEvaluation: true,
 defaultFlagHandler: (str) => {
  return { enabled: false, isDefault: true, value: { colour: '#ababab' } };
 },
});
```

</TabItem>
<TabItem value="ruby" label="Ruby">

```ruby
$flagsmith = Flagsmith::Client.new(
    environment_key: '<FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY'>,
    default_flag_handler: lambda { |feature_name|
        Flagsmith::Flags::DefaultFlag.new(
            enabled: false, value: {'colour': '#ababab'}.to_json
        )
    }
)
```

</TabItem>
<TabItem value="php" label="PHP">

```php
$flagsmith = (new Flagsmith('FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY'))
    ->withDefaultFlagHandler(function ($featureName) {
        $defaultFlag = (new DefaultFlag())
            ->withEnabled(false)->withValue(null);
        if ($featureName === 'secret_button') {
            return $defaultFlag->withValue('{"colour": "#ababab"}');
        }

        return $defaultFlag;
    });
```

</TabItem>
<TabItem value="go" label="Go">

```go
func DefaultFlagHandler(featureName string) (flagsmith.Flag, error) {
	return flagsmith.Flag{
		FeatureName: featureName,
		IsDefault:   true,
		Value:       `{"colour": "#FFFF00"}`,
		Enabled:     true,
	}, nil
}

client := flagsmith.NewClient(os.Getenv("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY"),
		flagsmith.WithDefaultHandler(DefaultFlagHandler),
)

```

</TabItem>
<TabItem value="rust" label="Rust">

```rust

use flagsmith::{Flag, Flagsmith, FlagsmithOptions};

fn default_flag_handler(feature_name: &str) -> Flag {
    let mut flag: Flag = Default::default();
    if feature_name == "secret_button" {
        flag.value.value_type = FlagsmithValueType::String;
        flag.value.value = serde_json::json!({"colour": "#b8b8b8"}).to_string();
    }
    return flag;
}

let options = FlagsmithOptions {
    default_flag_handler: Some(default_flag_handler),
    ..Default::default()
};

let flagsmith = Flagsmith::new(
        env::var("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY")
            .expect("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY not found in environment"),
        options,
    );

```

</TabItem>
<TabItem value="elixir" label="Elixir">

```elixir
flag_handler =
    fn name ->
        case name == "special_feature" do
            true ->
            %Flagsmith.Schemas.Flag{feature_name: name, value: "special", enabled: true}
            _ -> :not_found
        end
    end

client_configuration = Flagsmith.Client.new(environment_key: "FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY", default_flag_handler: flag_handler)
```

</TabItem>
</Tabs>

### Using an Offline Handler

:::info

Offline handlers are still in active development. We are building them for all our SDKs; those that are production ready
are listed below.

Progress on the remaining SDKs can be seen [here](https://github.com/Flagsmith/flagsmith/issues/2024).

:::

Flagsmith SDKs can be configured to include an offline handler which has 2 functions:

1. It can be used alongside [Offline Mode](server-side.md#offline-mode) to evaluate flags in environments with no
   network access
2. It can be used as a means of defining the behaviour for evaluating default flags, when something goes wrong with the
   regular evaluation process. To do this, simply set the offline handler initialisation parameter without enabling
   offline mode.

To use it as a default handler, we recommend using the [flagsmith CLI](https://github.com/Flagsmith/flagsmith-cli) to
generate the [Environment Document](/clients/overview#the-environment-document) and use our LocalFileHandler class, but
you can also create your own offline handlers, by extending the base class.

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
# Using the built-in local file handler

local_file_handler = LocalFileHandler(environment_document_path="/app/environment.json")
flagsmith = Flagsmith(..., offline_handler=local_file_handler)

# Defining a custom offline handler

class MyCustomOfflineHandler(BaseOfflineHandler):
    def get_environment(self) -> EnvironmentModel:
        return some_function_to_get_the_environment()
```

</TabItem>

<TabItem value="java" label="Java">

```java
// Using the built-in local file handler

FlagsmithConfig flagsmithConfig = FlagsmithConfig.newBuilder()
    .withOfflineHandler(new LocalFileHandler("/app/environment.json"))
    ...
    .build()

// Defining a custom offline handler

public class MyCustomOfflineHandler implements IOfflineHandler:
    public EnvironmentModel getEnvironment() {
        return someMethodToGetTheEnvironment()
    }
```

</TabItem>
<TabItem value="dotnet" label=".NET">

```csharp
// Using the built-in local file handler
var localFileHandler = new LocalFileHandler("path_to_environment_file/environment_file.json");

var flagsmithClient = new FlagsmithClient(
    offlineMode: true,
    offlineHandler: localFileHandler
);

// Defining a custom offline handler
public class MyCustomOfflineHandler: BaseOfflineHandler
{
    public override EnvironmentModel GetEnvironment()
    {
        return someMethodToGetTheEnvironment();
    }
}
```

</TabItem>
<TabItem value="nodejs" label="NodeJS">

```javascript
// Using the built-in local file handler
const localFileHandler = new LocalFileHandler('path_to_environment_file/environment_file.json');
const flagsmith = new Flagsmith({ offlineMode: true, offlineHandler: localFileHandler });

// Defining a custom offline handler
class CustomOfflineHandler extends BaseOfflineHandler {
 getEnvironment(): EnvironmentModel {
  return someMethodToGetTheEnvironment();
 }
}
```

</TabItem>
<TabItem value="ruby" label="Ruby">

```ruby
# Using the built-in local file handler

offline_handler = \
Flagsmith::OfflineHandlers::LocalFileHandler.new("environment.json")

# Instantiate the client with offline mode set to true

flagsmith = Flagsmith::Client.new(
  offline_mode: true,
  offline_handler: offline_handler,
)

# Defining a custom offline handler

class MyCustomOfflineHandler
  def environment
    # Some code providing the environment for the handler
  end
end
```

</TabItem>

</Tabs>

## Network Behaviour

The Server Side SDKS share the same network behaviour across the different languages:

### Remote Evaluation Mode Network Behaviour

- A blocking network request is made every time you make a call to get an Environment Flags. In Python, for example,
  `flagsmith.get_environment_flags()` will trigger this request.
- A blocking network request is made every time you make a call to get an Identities Flags. In Python, for example,
  `flagsmith.get_identity_flags(identifier=identifier, traits=traits)` will trigger this request.

### Local Evaluation Mode Network Behaviour

:::info

When using Local Evaluation, it's important to read up on the
[Pros, Cons and Caveats](overview.md#pros-cons-and-caveats).

To use Local Evaluation mode, you must use a Server Side key.

:::

- When the SDK is initialised, it will make an asynchronous network request to retrieve details about the Environment.
- Every 60 seconds (by default), it will repeat this aysnchronous request to ensure that the Environment information it
  has is up to date.

To achieve Local Evaluation, in most languages, the SDK spawns a separate thread (or equivalent) to poll the API for
changes to the Environment. In certain languages, you may be required to terminate this thread before cleaning up the
instance of the Flagsmith client. Languages in which this is necessary are provided below.

<Tabs groupId="language">
<TabItem value="java" label = "Java">

```java
// available from v5.0.5
flagsmith.close();
```

</TabItem>
<TabItem value="nodejs" label = "NodeJS">

```javascript
// available from v2.2.1
flagsmith.close();
```

</TabItem>
<TabItem value="php" label="PHP">

Since PHP does not share state between requests, you **have** to implement caching to get the benefits of Local
Evaluation mode. Please see [caching](#caching) below.

</TabItem>
</Tabs>

### Offline Mode

:::info

Offline mode is still in active development for some SDKs. We are building it for all our SDKs; those that are
production ready are listed below.

Progress on the remaining SDKs can be seen [here](https://github.com/Flagsmith/flagsmith/issues/2024).

:::

To run the SDK in a fully offline mode, you can set the client to offline mode. This will prevent the SDK from making
any calls to the Flagsmith API. To use offline mode, you must also provide an
[offline handler](server-side.md#using-an-offline-handler). See
[Configuring the SDK](server-side.md#configuring-the-sdk) for more details on initialising the SDK in offline mode.

## Configuring the SDK

You can modify the behaviour of the SDK during initialisation. Full configuration options are shown below.

<Tabs groupId="language">
<TabItem value="python" label="Python">

```python
flagsmith = Flagsmith(
    # Your API Token.
    # Note that this is either the `Environment API` key or the `Server Side SDK Token`
    # depending on if you are using Local or Remote Evaluation
    # Required.
    environment_key = "FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY",

    # Controls which mode to run in; local or remote evaluation.
    # See the `SDKs Overview Page` for more info
    # Optional.
    # Defaults to False.
    enable_local_evaluation = False,

    # Override the default Flagsmith API URL if you are self-hosting.
    # Optional.
    # Defaults to https://edge.api.flagsmith.com/api/v1/
    api_url = "https://api.yourselfhostedflagsmith.com/api/v1/",

    # The network timeout in seconds.
    # Optional.
    # Defaults to 10 seconds
    request_timeout_seconds = 10,

    # When running in local evaluation mode, defines
    # how often to request an updated Environment document in seconds
    # Optional
    # Defaults to 60 seconds
    environment_refresh_interval_seconds: int = 60,

    # A `urllib3` Retries object to control network retry policy
    # See https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.html#urllib3.util.Retry
    # Optional
    # Defaults to None
    retries: Retry = None,

    # Controls whether Flag Analytics data is sent to the Flagsmith API
    # See https://docs.flagsmith.com/advanced-use/flag-analytics
    # Optional
    # Defaults to False
    enable_analytics: bool = False,

    # You can pass custom headers to the Flagsmith API with this Dictionary.
    # This can be helpful, for example, when sending request IDs to help trace requests.
    # Optional
    # Defaults to None
    custom_headers: typing.Dict[str, typing.Any] = None,

    # You can specify a function to handle returning defaults in the case that
    # the request to flagsmith fails or the flag requested is not included in the
    # response
    # Optional
    default_flag_handler = lambda feature_name: return DefaultFlag(enabled=False, value=None),

    # (Available in 3.2.0+) Pass a mapping of protocol to proxy URL as per
    # https://requests.readthedocs.io/en/latest/api/#requests.Session.proxies
    # Optional
    proxies: typing.Dict[str, str] = None,

    # (Available in 3.4.0+) Set the SDK into offline mode.
    # Optional
    # Defaults to False
    offline_mode: bool = False,

    # (Available in 3.4.0+) Provide an offline handler to use with offline mode, or
    # as a means of returning default flags.
    # Optional
    # Defaults to None
    offline_handler: BaseOfflineHander = None,
)
```

</TabItem>
<TabItem value="java" label="Java">

```java
// The configuration for the Java client is currently split across the FlagsmithClient and
// FlagsmithConfig class, we are working to improve that in a future release.

private static FlagsmithClient flagsmith = FlagsmithClient
    .newBuilder()
    // Your API Token.
    // Note that this is either the `Environment API` key or the `Server Side SDK Token`
    // depending on if you are using Local or Remote Evaluation
    // Required.
    .setApiKey(System.getenv("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY"))

    // You can specify default Flag values on initialisation.
    // Optional
    .setDefaultFlagValueFunction(HelloController::defaultFlagHandler)

    // Controls which mode to run in; local or remote evaluation.
    // See the `SDKs Overview Page` for more info
    // Optional.
    // Defaults to False.
    .withLocalEvaluation(True)

    // Add custom headers which will be sent with each network request
    // to the Flagsmith API.
    // Optional.
    // Defaults to no custom headers.
    .withCustomHttpHeaders(new HashMap<string, string>() {{
        put("header", "value");
    }})

    // Enable in-memory caching for the Flagsmith API.
    // Optional.
    // Defaults to not cache anything.
    .withCache(FlagsmithCacheConfig.builder().enableEnvLevelCaching("cache-key").build())

    .withConfiguration(FlagsmithConfig.builder()
        // Override the default Flagsmith API URL if you are self-hosting.
        // Optional.
        // Defaults to https://edge.api.flagsmith.com/api/v1/
        .baseUri("https://api.yourselfhostedflagsmith.com/api/v1/")

        // The network timeout in milliseconds.
        // See https://square.github.io/okhttp/4.x/okhttp/okhttp3/ for details
        // Defaults are:
        //   connect: 2000
        //   write: 5000
        //   read: 5000
        // Optional.
        .connectTimeout(<millisecond int>)
        .writeTimeout(<millisecond int>)
        .readTimeout(<millisecond int>)

        // Override the sslSocketFactory
        // See https://square.github.io/okhttp/4.x/okhttp/okhttp3/ for details
        // Optional.
        .sslSocketFactory(SSLSocketFactory sslSocketFactory, X509TrustManager trustManager)

        // Add a custom HTTP interceptor in the form of an okhttp3.Interceptor
        // object
        // Optional
        .addHttpInterceptor(interceptor)

        // Add a custom java.net.Proxy to the OkHttp client
        // Optional
        .withProxy(proxy)

        // Add a custom com.flagsmith.config.Retry object to configure the
        // backoff / retry configuration
        // Optional
        // Defaults to Retry(3)
        .retries(retries)

        // Enable local evaluation mode
        // ()
        // Optional
        // Defaults to false
        .withLocalEvaluation(true)

        // Set environment refresh rate with polling manager.
        // Only needed when local evaluation is true.
        // Optional.
        // Defaults to 60 seconds
        .withEnvironmentRefreshIntervalSeconds(Integer seconds)

        // Controls whether Flag Analytics data is sent to the Flagsmith API
        // See https://docs.flagsmith.com/advanced-use/flag-analytics
        // Optional
        // Defaults to False
        .withEnableAnalytics(Boolean enable)

        // (Available in v7.2.0+) Set the SDK into offline mode.
        // Optional
        // Defaults to False
        .withOfflineMode(Boolean enable)

        // (Available in v7.2.0+) Provide an offline handler to use with offline mode, or as a means of returning default flags.
        // Optional
        .withOfflineHandler(IOfflineHandler offlineHandler)

        .build())

    .build();
```

</TabItem>
<TabItem value="dotnet" label=".NET">

```csharp
_flagsmithClient = new FlagsmithClient(
    # Your API Token.
    # Note that this is either the `Environment API` key or the `Server Side SDK Token`
    # depending on if you are using Local or Remote Evaluation
    # Required.
    environmentKey: "FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY",

    # Pass in a default Flag Handler method
    # Optional
    defaultFlagHandler: defaultFlagHandler,

    # Override the default Flagsmith API URL if you are self-hosting.
    # Optional.
    # Defaults to https://edge.api.flagsmith.com/api/v1/
    apiUrl: "https://flagsmith.myproject.com"

    # Controls which mode to run in; local or remote evaluation.
    # See the `SDKs Overview Page` for more info
    # Optional.
    # Defaults to False.
    enableClientSideEvaluation: false;

    # Controls whether Flag Analytics data is sent to the Flagsmith API
    # See https://docs.flagsmith.com/advanced-use/flag-analytics
    # Optional
    # Defaults to false
    enableAnalytics: false

    # When running in local evaluation mode, defines
    # how often to request an updated Environment document in seconds
    # Optional
    # Defaults to 60 seconds
    environmentRefreshIntervalSeconds: 60

    # You can pass custom headers to the Flagsmith API with this Dictionary.
    # This can be helpful, for example, when sending request IDs to help trace requests.
    # Optional
    # Defaults to None
    customHeaders: <Dictionary>

    # How often to retry failed HTTP requests
    # Optional
    # Defaults to 1
    retries: 1

    # The network timeout in seconds.
    # Optional.
    # Defaults to null (http client default)
    requestTimeout: null,
)
```

### Singleton Initialization

Singleton ensures a single instance of FlagsmithClient throughout the application, optimizing resources and maintaining
consistency in configuration.

Below you can find an example implementation of the client instantiated as a Singleton with its configuration defined in
a file called `FlagsmithSettings.cs` (found below), which stores Flagsmith-specific settings.

```csharp

builder.Services.AddOptions<FlagsmithSettings>().Bind(builder.Configuration.GetSection(FlagsmithSettings.ConfigSection));
builder.Services.AddSingleton(provider => provider.GetRequiredService<IOptions<FlagsmithSettings>>().Value);
builder.Services.AddSingleton<IFlagsmithClient, FlagsmithClient>(provider =>
{
    var settings = provider.GetService<FlagsmithSettings>();
    return new FlagsmithClient(settings);
});


```

`FlagsmithSettings.cs`

```csharp
using Example.Controllers;
using Flagsmith;
using Newtonsoft.Json;

namespace Example.Settings
{
    public class FlagsmithSettings : IFlagsmithConfiguration
    {
        public static string ConfigSection => "FlagsmithConfiguration";
        public string ApiUrl { get; set; } = "https://edge.api.flagsmith.com/api/v1/";
        public string EnvironmentKey { get; set; } = String.Empty;
        public bool EnableClientSideEvaluation { get; set; } = false;
        public int EnvironmentRefreshIntervalSeconds { get; set; } = 60;
        public ILogger Logger { get; set; }
        public bool EnableAnalytics { get; set; } = false;
        public Double? RequestTimeout { get; set; }
        public Dictionary<string, string> CustomHeaders { get; set; }
        public int? Retries { get; set; } = 1;
        public CacheConfig CacheConfig { get; set; } = new(false);
    }
}

```

In the `appsettings.json` file you can configure the necessary flagsmith values.

```json
{
 "AllowedHosts": "*",
 "FlagsmithConfiguration": {
  "EnvironmentKey": "FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY",
  "EnableClientSideEvaluation": false,
  "EnvironmentRefreshIntervalSeconds": 60,
  "EnableAnalytics": true,
  "RequestTimeout": 10,
  "Retries": 3
 }
}
```

</TabItem>
<TabItem value="ruby" label="Ruby">

```ruby
$flagsmith = Flagsmith::Client.new(
    # Your API Token.
    # Note that this is either the `Environment API` key or the `Server Side SDK Token`
    # depending on if you are using Local or Remote Evaluation
    # Required.
    environment_key = "FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY",

    # Controls which mode to run in; local or remote evaluation.
    # See the `SDKs Overview Page` for more info
    # Optional.
    # Defaults to false.
    enable_local_evaluation = false,

    # Override the default Flagsmith API URL if you are self-hosting.
    # Optional.
    # Defaults to https://edge.api.flagsmith.com/api/v1/
    api_url = "https://api.yourselfhostedflagsmith.com/api/v1/",

    # The network timeout in seconds.
    # Optional.
    # Defaults to 10 seconds
    request_timeout_seconds = 10,

    # When running in local evaluation mode, defines
    # how often to request an updated Environment document in seconds
    # Optional
    # Defaults to 60 seconds
    environment_refresh_interval_seconds = 60,

    # A faraday retry object to control network retry policy
    # See https://www.rubydoc.info/gems/faraday/0.15.3/Faraday/Request/Retry
    # Optional
    # Defaults to nil
    retries = nil,

    # Controls whether Flag Analytics data is sent to the Flagsmith API
    # See https://docs.flagsmith.com/advanced-use/flag-analytics
    # Optional
    # Defaults to False
    enable_analytics = false,

    # You can pass custom headers to the Flagsmith API with this Dictionary.
    # This can be helpful, for example, when sending request IDs to help trace requests.
    # Optional
    # Defaults to nill
    custom_headers = nil,

    # You can specify a function to handle returning defaults in the case that
    # the request to flagsmith fails or the flag requested is not included in the
    # response
    # Optional
    default_flag_handler = lambda { |feature_name| Flagsmith::DefaultFlag.new(enabled=false, value=nil) }
)
```

</TabItem>
<TabItem value="nodejs" label="NodeJS">

```typescript
import { bool, number } from 'prop-types';

const flagsmith = new Flagsmith({
 /*
   Your API Token.
   Note that this is either the `Environment API` key or the `Server Side SDK Token`
   depending on if you are using Local or Remote Evaluation
   Required.
   */
 environmentKey: 'FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY',

 /*
   Override the default Flagsmith API URL if you are self-hosting.
   Optional.
   Defaults to https://edge.api.flagsmith.com/api/v1/
   */
 apiUrl: 'https://api.yourselfhostedflagsmith.com/api/v1/',

 /*
   Adds caching support
   Optional
   See https://docs.flagsmith.com/clients/server-side#caching
   */
 cache: {
  has: (key: string) => bool,
  get: (key: string) => string | number | null,
  set: (k: string, v: Flags) => (cache[k] = v),
 },

 /*
   Custom http headers can be added to the http client
   Optional
   */
 customHeaders: { aHeader: 'aValue' },

 /*
   Controls whether Flag Analytics data is sent to the Flagsmith API
   See https://docs.flagsmith.com/advanced-use/flag-analytics
   Optional
   Defaults to false
   */
 enableAnalytics: true,

 /*
   Controls which mode to run in; local or remote evaluation.
   See the `SDKs Overview Page` for more info
   Optional.
   Defaults to false.
   */
 enableLocalEvaluation: true,

 /*
   Set environment refresh rate with polling manager.
   Only needed when local evaluation is true.
   Optional.
   Defaults to 60 seconds
   */
 environmentRefreshIntervalSeconds: 60,

 /*
   The network timeout in seconds.
   Optional.
   Defaults to 10 seconds
   */
 requestTimeoutSeconds: 30,

 /*
   You can specify default Flag values on initialisation.
   Optional
   */
 defaultFlagHandler: (featureName: string) => {
  return { enabled: false, isDefault: true, value: null };
 },

 /*
    A callback for whenever the environment model is updated or there is an error retrieving it.
    This is only used in local evaluation mode.
    Optional
    */
 onEnvironmentChange: (error: Error | null, result: EnvironmentModel) => {},
});
```

</TabItem>
<TabItem value="php" label="PHP">

```php
$flagsmith = new Flagsmith(
    /*
    Your API Token.
    Note that this is either the `Environment API` key or the `Server Side SDK Token`
    depending on if you are using Local or Remote Evaluation
    Required.
    */
    string $apiKey,

    /*
    Override the default Flagsmith API URL if you are self-hosting.
    Optional.
    Defaults to https://edge.api.flagsmith.com/api/v1/
    */
    string $host = self::DEFAULT_API_URL,

    /*
    Custom http headers can be added to the http client
    Optional
    */
    object $customHeaders = null,

    /*
    Set environment refresh rate with polling manager.
    This also enables local evaluation.
    Optional.
    Defaults to null
    */
    int $environmentTtl = null,

    /*
    Retry Object, instance of Flagsmith\Utils\Retry
    Retry configuration for api calls.
    Defaults to 3 retries for every api call.
    */
    Retry $retries = null,

    /*
    Controls whether Flag Analytics data is sent to the Flagsmith API
    See https://docs.flagsmith.com/advanced-use/flag-analytics
    Optional
    Defaults to false
    */
    bool $enableAnalytics = false,

    /*
    You can specify default Flag values on initialisation.
    Optional
    */
    Closure $defaultFlagHandler = null
);
```

</TabItem>
<TabItem value="go" label="Go">

```go
client := flagsmith.NewClient(os.Getenv("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY"),
        // Override the default Flagsmith API URL if you are self-hosting.
        // Defaults to https://edge.api.flagsmith.com/api/v1/
        flagsmith.WithBaseURL("http://localhost:8080/api/v1/"),

        // Controls which mode to run in; local or remote evaluation.
        // See the `SDKs Overview Page` for more info
        // Defaults to False
        func WithLocalEvaluation(ctx context.Context),

        // The network timeout in seconds.
        flagsmith.WithRequestTimeout(10*time.Second),

        // When running in local evaluation mode, defines
        // how often to request an updated Environment document
        // Defaults to 60 seconds
        flagsmith.WithEnvironmentRefreshInterval(60*time.Second),

        // Controls whether Flag Analytics data is sent to the Flagsmith API
        // See https://docs.flagsmith.com/advanced-use/flag-analytics
        flagsmith.WithAnalytics(ctx),

        // Sets `resty.Client` options.  `SetRetryCount` and `SetRetryWaitTime`
        // Ref: https://pkg.go.dev/github.com/go-resty/resty/v2#Client.SetRetryCount
        // https://pkg.go.dev/github.com/go-resty/resty/v2#Client.SetRetryWaitTime
        flagsmith.WithRetries(3, 5*time.Second),

        // You can pass custom headers to the Flagsmith API with this Dictionary.
        // This can be helpful, for example, when sending request IDs to help trace requests.
        flagsmith.WithCustomHeaders(map[string]string{
          "Content-Type": "application/json",
          "Accept":       "application/json",
        }),

        // You can specify a function to handle returning defaults in the case that
        // the request to flagsmith fails or the flag requested is not included in the
        // response
        flagsmith.WithDefaultHandler(defaultFlagHandler),

        // Allows the client to use any logger that implements the `Logger` interface.
        flagsmith.WithLogger(ctx),

        // WithProxy returns an Option function that sets the proxy(to be used by internal resty client).
        // The proxyURL argument is a string representing the URL of the proxy server to use, e.g. "http://proxy.example.com:8080".
        func WithProxy(proxyURL string) Option {
            return func(c *Client) {
                c.client.SetProxy(proxyURL)
            }
        }
)
```

</TabItem>
<TabItem value="rust" label="Rust">

```rust
use reqwest::header::{self, HeaderMap};
// Optional Arguments
let options = FlagsmithOptions {
    // Override the default Flagsmith API URL if you are self-hosting.
    // Defaults to https://edge.api.flagsmith.com/api/v1/
    api_url: "https://edge.flagsmith.com/api/v1/".to_string(),

    // You can pass custom headers to the Flagsmith API with this HashMap
    // This can be helpful, for example, when sending request IDs to help trace requests.
    // Defaults to an empty header::HeaderMap.
    custom_headers: header::HeaderMap::new(),

    // The network timeout in seconds.
    // Defaults to 10 seconds
    request_timeout_seconds: 10,

    // Controls which mode to run in; local or remote evaluation.
    // See the `SDKs Overview Page` for more info
    // Defaults to False.
    enable_local_evaluation: false,

    // When running in local evaluation mode, defines
    // how often to request an updated Environment document in milliseconds.
    // Defaults to 60 seconds
    environment_refresh_interval_mills: 60* 1000,

    // Controls whether Flag Analytics data is sent to the Flagsmith API
    // See https://docs.flagsmith.com/advanced-use/flag-analytics
    // Defaults to False
    enable_analytics: false,

    //Function that will be used if the API doesn't respond, or an unknown
    // feature is Requested
    // Defaults to None
    default_flag_handler: None
};

// Required Arguments
// Your API Token.
// Note that this is either the `Environment API` key or the `Server Side SDK Token`
// depending on if you are using Local or Remote Evaluation
let FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY = "some_key".to_string();

let flagsmith = Flagsmith::new(
        FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY,
        options,
    );


```

</TabItem>
<TabItem value="elixir" label="Elixir">

Application level Configuration

```elixir
# The only required option is the `:environment_key`

config :flagsmith_engine, :configuration,
       #
       # Your API Token.
       # Note that this is either the `Environment API` key or the
       # `Server Side SDK Token` depending on if you are using Local or
       # Remote Evaluation
       environment_key: "FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY",
       #
       # Override the default Flagsmith API URL if you are self-hosting.
       # Defaults to https://edge.api.flagsmith.com/api/v1/
       api_url: "https://api.yourselfhostedflagsmith.com/api/v1",
       #
       # You can specify a function to handle returning defaults in the case that
       # the request to flagsmith fails or the flag requested is not included in the
       # response, defaults to returning :not_found`
       default_flag_handler: function_defaults_to_not_found,
       #
       # You can pass custom headers to the Flagsmith API as a list of `header` `value`
       # tuples, for example, when sending request IDs to help trace requests, defaults
       # to an empty list.
       custom_headers: [{"to add to", "the requests"}],
       #
       # Network timeout in milliseconds, defaults to 5_000
       request_timeout_milliseconds: 5000,
       #
       # Controls which mode to run in; local or remote evaluation.
       # See the `SDKs Overview Page` for more info, defaults to false
       enable_local_evaluation: false,
       #
       # When running in local evaluation mode, defines how often to request
       # an updated Environment document in milliseconds, defaults to 1 minute
       environment_refresh_interval_milliseconds: 60_000,
       #
       # Defines how many retries the HTTP adapter is allowed to execute before
       # deeming the request failed, defaults to 0
       retries: 0,
       #
       # Controls whether Flag Analytics data is sent to the Flagsmith API
       # See https://docs.flagsmith.com/advanced-use/flag-analytics, defaults to false
       enable_analytics: false

```

Or when starting a client or making a request, allows the exact same options as when configuring through the application
configuration.

```elixir
client_configuration = Flagsmith.Client.new(
        environment_key: "FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY",
        api_url: "https://api.yourselfhostedflagsmith.com/api/v1",
        default_flag_handler: function_defaults_to_not_found,
        custom_headers: [{"to add to", "the requests"}],
        request_timeout_milliseconds: 5000,
        enable_local_evaluation: false,
        environment_refresh_interval_milliseconds: 60_000,
        retries: 0,
        enable_analytics: false
)

{:ok, flags} = Flagsmith.Client.get_environment_flags(client_configuration)

# or

{:ok, flags} = Flagsmith.Client.get_environment_flags(
        environment_key: "FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY",
        api_url: "https://api.yourselfhostedflagsmith.com/api/v1",
        default_flag_handler: function_defaults_to_not_found,
        custom_headers: [{"to add to", "the requests"}],
        request_timeout_milliseconds: 5000,
        enable_local_evaluation: false,
        environment_refresh_interval_milliseconds: 60_000,
        retries: 0,
        enable_analytics: false
)
```

</TabItem>
</Tabs>

## Caching

The following SDKs have code and functionality related to caching flags.

<Tabs groupId="language">
<TabItem value="java" label="Java">

If you would like to use in-memory caching, you will need to enable it (it is disabled by default). The main advantage
of using in-memory caching is that you can reduce the number of HTTP calls performed to fetch flags.

Flagsmith uses [Caffeine](https://github.com/ben-manes/caffeine), a high performance, near optimal caching library.

If you enable caching on the Flagsmith client without setting any values (as shown below), the following default values
will be set for you:

- `maxSize(10)`
- `expireAfterWrite(5, TimeUnit.MINUTES)`
- project level caching will be disabled by default (i.e. only enabled if you configure a caching key)

```java
// use in-memory caching with Flagsmith defaults as described above
final FlagsmithClient flagsmithClient = FlagsmithClient.newBuilder()
                .setApiKey("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY")
                .withConfiguration(FlagsmithConfig
                        .newBuilder()
                        .baseURI("http://yoururl.com")
                        .build())
                .withCache(FlagsmithCacheConfig
                        .newBuilder()
                        .build())
                .build();
```

If you would like to change the default settings, you can overwrite them by using the available builder methods:

```java
// use in-memory caching with custom configuration
final FlagsmithClient flagsmithClient = FlagsmithClient.newBuilder()
                .setApiKey("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY")
                .withConfiguration(FlagsmithConfig
                        .newBuilder()
                        .baseURI("http://yoururl.com")
                        .build())
                .withCache(FlagsmithCacheConfig
                        .newBuilder()
                        .maxSize(100)
                        .expireAfterWrite(10, TimeUnit.MINUTES)
                        .recordStats()
                        .enableEnvLevelCaching("some-key-to-avoid-clashing-with-user-identifiers")
                        .build())
                .build();
```

The user identifier is used as the cache key, this provides granular control over the cache should you require it. If
you would like to manipulate the cache:

```java
// this will return null if caching is disabled
final FlagsmithCache cache = flagsmithClient.getCache();
// you can now discard a single or all entries in the cache
cache.invalidate("user-identifier");
// or
cache.invalidateAll();
// get stats (if you have enabled them in the cache configuration, otherwise all values will be zero)
final CacheStats stats = cache.stats();
// check if flags for a user identifier are cached
final FlagsAndTraits flags = cache.getIfPresent("user-identifier");
```

Since the user identifier is used as the cache key, you need to configure a cache key to enable project level caching.
Make sure you select a project level cache key that will never be a user identifier.

```java
// use in-memory caching with Flagsmith defaults and project level caching enabled
final String projectLevelCacheKey = "some-key-to-avoid-clashing-with-user-identifiers";
final FlagsmithClient flagsmithClient = FlagsmithClient.newBuilder()
                .setApiKey("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY")
                .withConfiguration(FlagsmithConfig
                        .newBuilder()
                        .baseURI("http://yoururl.com")
                        .build())
                .withCache(FlagsmithCacheConfig
                        .newBuilder()
                        .enableEnvLevelCaching(projectLevelCacheKey)
                        .build())
                .build();

// if you need to access the cache directly, you can do this:
final FlagsmithCache cache = flagsmithClient.getCache();
// invalidate project level cache
cache.invalidate(projectLevelCacheKey);
// check if project level flags have been cached
final FlagsAndTraits flags = cache.getIfPresent(projectLevelCacheKey);
```

</TabItem>
<TabItem value="nodejs" label="NodeJS">

You can initialise the SDK with something like this:

```javascript
flagsmith.init({
  cache: {
    has:(key)=> return Promise.resolve(!!cache[key]) , // true | false
    get: (k)=> cache[k] // return flags or flags for user
    set: (k,v)=> cache[k] = v // gets called if has returns false with response from API for Identify or getFlags
  }
})
```

The core concept is that if `has` returns false, the SDK will make the required API calls under the hood. The keys are
either `flags` or `flags_traits-${identity}`.

An example of a concrete implemention is below.

```javascript
const flagsmith = require('flagsmith-nodejs');
const redis = require('redis');

const redisClient = redis.createClient({
 host: 'localhost',
 port: 6379,
});

flagsmith.init({
 environmentID: 'FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY',
 cache: {
  has: (key) =>
   new Promise((resolve, reject) => {
    redisClient.exists(key, (err, reply) => {
     console.log('check ' + key + ' from cache', err, reply);
     resolve(reply === 1);
    });
   }),
  get: (key) =>
   new Promise((resolve) => {
    redisClient.get(key, (err, cacheValue) => {
     console.log('get ' + key + ' from cache');
     resolve(cacheValue && JSON.parse(cacheValue));
    });
   }),
  set: (key, value) =>
   new Promise((resolve) => {
    // Expire the key after 60 seconds
    redisClient.set(key, JSON.stringify(value), 'EX', 60, (err, reply) => {
     console.log('set ' + key + ' to cache', err);
     resolve();
    });
   }),
 },
});

router.get('/', function (req, res, next) {
 flagsmith.getValue('background_colour').then((value) => {
  res.render('index', {
   title: value,
  });
 });
});
```

</TabItem>
<TabItem value="php" label="PHP">

```php
$flagsmith = (new Flagsmith("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY"));
// This will load the environment from cache (or API, if cache does not exist.)
$flagsmith->updateEnvironment();
```

It is recommended to use a psr simple-cache implementation to cache the environment document between multiple requests.

```sh
composer require symfony/cache
```

```php
$flagsmith = (new Flagsmith("FLAGSMITH_SERVER_SIDE_ENVIRONMENT_KEY"))
  ->withCache(new Psr16Cache(new FilesystemAdapter()));
// Cache the environment call to reduce network calls for each and every evaluation.
// This will load the environment from cache (or API, if cache does not exist.)
$flagsmith->updateEnvironment();
```

An optional cron job can be added to refresh this cache at a set time depending on your choice. Please set
EnvironmentTTL value for this purpose.

```php
// the environment will be cached for 100 seconds.
$flagsmith = $flagsmith->withEnvironmentTtl(100);
$flagsmith->updateEnvironment();
```

```sh
* * * 1 40 php index.php # using cli
* * * 1 40 curl http://localhost:8000/ # using http
```

Note:

- For the environment cache, please use the server key generated from the Flagsmith Settings menu. The key's prefix is
  `ser.`.
- The cache is important for concurrent requests. Without the cache, each request in PHP is a different process with its
  own memory objects. The cache (filesystem or other) would enforce that the network call is reduced to a file system
  one.

</TabItem>
</Tabs>

## Logging

The following SDKs have code and functionality related to logging.

<Tabs groupId="language">
<TabItem value="java" label="Java">

Logging is disabled by default. If you would like to enable it then call `.enableLogging()` on the client builder:

```java
FlagsmithClient flagsmithClient = FlagsmithClient.newBuilder()
                // other configuration as shown above
                .enableLogging()
                .build();
```

Flagsmith uses [SLF4J](http://www.slf4j.org) and we only implement its API. If your project does not already have SLF4J,
then include an implementation, i.e.:

```xml
<dependency>
  <groupId>org.slf4j</groupId>
  <artifactId>slf4j-simple</artifactId>
  <version>${slf4j.version}</version>
</dependency>
```

</TabItem>
</Tabs>

## Contribute to the SDKs

All our SDKs are Open Source.

<Tabs groupId="language">
<TabItem value="python" label="Python">

https://github.com/Flagsmith/flagsmith-python-client

</TabItem>
<TabItem value="java" label="Java">

https://github.com/Flagsmith/flagsmith-java-client

</TabItem>
<TabItem value="dotnet" label=".NET">

https://github.com/Flagsmith/flagsmith-dotnet-client

</TabItem>
<TabItem value="nodejs" label="NodeJS">

https://github.com/Flagsmith/flagsmith-nodejs-client

</TabItem>
<TabItem value="ruby" label="Ruby">

https://github.com/Flagsmith/flagsmith-ruby-client

</TabItem>
<TabItem value="php" label="PHP">

https://github.com/Flagsmith/flagsmith-php-client

</TabItem>
<TabItem value="go" label="Go">

https://github.com/Flagsmith/flagsmith-go-client

</TabItem>
<TabItem value="rust" label="Rust">

https://github.com/Flagsmith/flagsmith-rust-client

</TabItem>
<TabItem value="elixir" label="Elixir">

https://github.com/Flagsmith/flagsmith-elixir-client

</TabItem>
</Tabs>
