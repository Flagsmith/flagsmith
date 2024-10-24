---
title: Transient Traits and Identities
---

By default, Flagsmith [stores all Traits](/basic-features/managing-identities#identity-and-trait-storage) associated
with an Identity to evaluate flags. This default behavior works for most use cases. However, there are scenarios where
you may want more control over which Traits or Identities are stored. Using the Flagsmith API and SDKs, you can mark
Traits and Identities as transient — meaning they are used for flag evaluation but are not stored.

## Overview and Use Cases

Transient Identities and Traits are particularly useful when you need to run flag evaluations without storing specific
data in Flagsmith. Below are common scenarios where transient Traits or Identities come in handy.

### Anonymous Identities

If you choose to provide an empty or blank (`""`) identifier is provided, Flagsmith will automatically treat the
Identity as transient. In this case, an auto-generated identifier is returned, based on a hash of the provided Traits.
This ensures consistent flag evaluations without persisting the Identity in the Flagsmith dashboard.

```javascript
flagsmith.init({
 evaluationContext: {
  identity: {
   identifier: null,
   traits: { paymentPreference: 'cash' },
  },
 },
});
let identifierToUseLater = flagsmith.getContext().identity.identifier;
```

This approach is useful for scenarios such as A/B testing in e-commerce, where you want to include users who haven't
registered or logged in.

### Ephemeral Contexts

In some cases, you may need to temporarily override certain Traits for a session or device without overwriting the
stored value. For example, imagine you’ve persisted the `screenOrientation` Trait as `landscape` for a user:

```javascript
flagsmith.init({
 evaluationContext: {
  identity: {
   identifier: 'my-user',
   traits: { screenOrientation: 'landscape' },
  },
 },
});
```

If you want to switch the `screenOrientation` to `portrait` for a specific session without overwriting the existing
value, you can mark the Trait as transient:

```javascript
flagsmith.setTrait('screenOrientation', { value: 'portrait', transient: true });
```

In this case, `portrait` will be used for one specific flag evaluation, but the stored `landscape` value will remain
unchanged.

### Skipping Personal Identifiable Information (PII)

You can mark sensitive Traits, such as `email`, `phoneNumber`, or `locality`, as transient to enable segmentation
without storing the actual data. For example, you may want to target users based on email domains while avoiding the
storage of email addresses.

Considering you have a Segment condition where `"email"` ends with `"example.com"`. To get flags for this Segment:

```javascript
flagsmith.updateContext({
 identity: {
  identifier: 'test-user-with-transient-email',
  traits: {
   email: { value: 'alice@example.com', transient: true },
  },
 },
});
```

After making the SDK call, if you check the Identities tab, you'll see the `test-user-with-transient-email` Identity
without the `email` Trait being stored.

## Usage

<Tabs groupId="language" queryString>
<TabItem value="curl" label="API (curl)">

Mark a Trait as transient:

```bash
curl --request POST 'https://edge.api.flagsmith.com/api/v1/identities/' \
--header 'X-Environment-Key: <Your Env Key>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "identifier":"identifier_5",
    "traits": [
        {
            "trait_key": "my_trait_key",
            "trait_value": 123.5,
            "transient": true
        },
        {
            "trait_key": "my_other_key",
            "trait_value": true
        }
    ]
}'
```

Mark the whole Identity as transient:

```bash
curl --request POST 'https://edge.api.flagsmith.com/api/v1/identities/' \
--header 'X-Environment-Key: <Your Env Key>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "identifier":"identifier_5",
    "traits": [
        {
            "trait_key": "my_trait_key",
            "trait_value": 123.5
        },
        {
            "trait_key": "my_other_key",
            "trait_value": true
        }
    ],
    "transient": true
}'
```

</TabItem>
<TabItem value="js" label="JavaScript">

:::info

Transient Traits and Identities are supported starting from JavaScript SDK version 5.0.0.

:::

Mark a Trait as transient:

```javascript
flagsmith.setTrait('my_trait_key', { value: 123.5, transient: true });
```

Mark the whole Identity as transient:

```javascript
flagsmith.setContext({
 identity: {
  identifier: 'my-user',
  transient: true,
  traits: { my_trait_key: 123.5, my_other_key: true },
 },
});
```

</TabItem>
<TabItem value="python" label="Python">

:::info

Transient Traits and Identities are supported starting from Python SDK version 3.8.0.

:::

Mark a Trait as transient:

```python
identity_flags = flagsmith.get_identity_flags(
    identifier="my-user",
    traits={
        "my_trait_key": {"value":123.5, "transient": true},
        "my_other_key": True
    }
)
```

Mark the whole Identity as transient:

```python
identity_flags = flagsmith.get_identity_flags(
    identifier="my-user",
    transient=True,
    traits={
        "my_trait_key": 123.5,
        "my_other_key": True
    }
)
```

</TabItem>
<TabItem value="java" label="Java">

:::info

Transient Traits and Identities are supported starting from Java SDK version 7.4.0.

:::

Mark a Trait as transient:

```java
import com.flagsmith.models.TraitConfig;

Map<String, Object> traits = new HashMap<String, Object>();
traits.put("my_trait_key", new TraitConfig(123.5, true));
traits.put("my_other_key", true);

Flags flags = flagsmith.getIdentityFlags("my-user", traits);
```

Mark the whole Identity as transient:

```java
import com.flagsmith.models.TraitConfig;

Map<String, Object> traits = new HashMap<String, Object>();
traits.put("my_trait_key", 123.5);
traits.put("my_other_key", true);

Flags flags = flagsmith.getIdentityFlags("my-user", traits, true);
```

</TabItem>
<TabItem value="dotnet" label=".NET">

:::info

Transient Traits and Identities are supported starting from .NET SDK version 5.4.0.

:::

Mark a Trait as transient:

```csharp
var traitList = new List<Trait> { new Trait("my-trait-key", 123.5, true), new Trait("my_other_key", true) };

var flags = _flagsmithClient.GetIdentityFlags("my-user", traitList).Result;
```

Mark the whole Identity as transient:

```csharp
var traitList = new List<Trait> { new Trait("my-trait-key", 123.5), new Trait("my_other_key", true) };

var flags = _flagsmithClient.GetIdentityFlags("my-user", traitList, true).Result;
```

</TabItem>
<TabItem value="nodejs" label="NodeJS">

:::info

Transient Traits and Identities are supported starting from NodeJS SDK version 4.0.0.

:::

Mark a Trait as transient:

```javascript
const flags = await flagsmith.getIdentityFlags('my-user', {
 my_trait_key: { value: 123.5, transient: true },
 my_other_key: true,
});
```

Mark the whole Identity as transient:

```javascript
const flags = await flagsmith.getIdentityFlags('my-user', { my_trait_key: 123.5, my_other_key: true }, true);
```

</TabItem>
<TabItem value="ruby" label="Ruby">

:::info

Transient Traits and Identities are supported starting from Ruby SDK version 4.2.0.

:::

Mark a Trait as transient:

```ruby
$flags = $flagsmith.get_identity_flags('my-user', my_trait_key: { value: 123.5, transient: true }, my_other_key: true )
```

Mark the whole Identity as transient:

```ruby
$flags = $flagsmith.get_identity_flags('my-user', true, my_trait_key: 123.5, my_other_key: true)
```

</TabItem>
<TabItem value="php" label="PHP">

:::info

Transient Traits and Identities are supported starting from Ruby SDK version 4.2.0.

:::

Mark a Trait as transient:

```ruby
$flags = $flagsmith.get_identity_flags('my-user', my_trait_key: { value: 123.5, transient: true }, my_other_key: true )
```

Mark the whole Identity as transient:

```ruby
$flags = $flagsmith.get_identity_flags('my-user', true, my_trait_key: 123.5, my_other_key: true)
```

</TabItem>
<TabItem value="go" label="Go">

:::info

Transient Traits and Identities are supported starting from Go SDK version 4.0.0.

:::

Mark a Trait as transient:

```go
flags, _ := client.GetFlags(
    ctx,
    &flagsmith.NewEvaluationContext(
        "my-user",
        map[string]*interface{}{
            "my_trait_key": NewTraitEvaluationContext(123.5, true),
            "my_other_key": true,
        },
    )
)
```

Mark the whole Identity as transient:

```go
flags, _ := client.GetFlags(
    ctx,
    &flagsmith.NewTransientEvaluationContext(
        "my-user",
        map[string]*interface{}{
            "my_trait_key": 123.5,
            "my_other_key": true,
        },
    )
)
```

</TabItem>
<TabItem value="rust" label="Rust">

:::info

Transient Traits and Identities are supported starting from Rust SDK version 2.0.0.

:::

Mark a Trait as transient:

```rust
use flagsmith::models::SDKTrait;
use flagsmith_flag_engine::types::{FlagsmithValue, FlagsmithValueType};

let identifier = "delboy@trotterstraders.co.uk";

let traits = vec![
    SDKTrait::new_with_transient(
        "my_trait_key".to_string(),
        FlagsmithValue {
            value: "123.5".to_string(),
            value_type: FlagsmithValueType::Float,
        },
        true,
    ),
    SDKTrait::new(
        "my_other_key".to_string(),
        FlagsmithValue {
            value: "true".to_string(),
            value_type: FlagsmithValueType::Bool,
        },
        true,
    ),
];

let identity_flags = flagsmith.get_identity_flags(identifier, Some(traits), None).unwrap();
```

Mark the whole Identity as transient:

```rust
use flagsmith::models::SDKTrait;
use flagsmith_flag_engine::types::{FlagsmithValue, FlagsmithValueType};

let identifier = "delboy@trotterstraders.co.uk";

let traits = vec![
    SDKTrait::new(
        "my_trait_key".to_string(),
        FlagsmithValue {
            value: "123.5".to_string(),
            value_type: FlagsmithValueType::Float,
        },
    ),
    SDKTrait::new(
        "my_other_key".to_string(),
        FlagsmithValue {
            value: "true".to_string(),
            value_type: FlagsmithValueType::Bool,
        },
        true,
    ),
];

let identity_flags = flagsmith.get_identity_flags(identifier, Some(traits), true).unwrap();
```

</TabItem>
<TabItem value="elixir" label="Elixir">

:::info

Transient Traits and Identities are supported starting from Elixir SDK version 2.2.0.

:::

Mark a Trait as transient:

```elixir
{:ok, flags} = Flagsmith.Client.get_identity_flags(
      client_configuration,
      "my-user",
      [
        %{trait_key: "my_trait_key", trait_value: 123.5, transient: true},
        %{trait_key: "my_other_key", trait_value: true},
      ]
)
```

Mark the whole Identity as transient:

```elixir
{:ok, flags} = Flagsmith.Client.get_identity_flags(
      client_configuration,
      "my-user",
      [
        %{trait_key: "my_trait_key", trait_value: 123.5},
        %{trait_key: "my_other_key", trait_value: true},
      ],
      true
)
```

</TabItem>
<TabItem value="android" label="Android">

:::info

Transient Traits and Identities are supported starting from Android SDK version 2.2.0.

:::

Mark a Trait as transient:

```kotlin
flagsmith.getFeatureFlags(identity = "my-user", traits = listOf(Trait(key = "my_trait_key", value = 123.5, transient: true), Trait(key = "my_other_key", value = true))) { result ->
    result.fold(
        onSuccess = { onFlagsSuccess },
        onFailure = { onFlagsFailure }
    )
}
```

Mark the whole Identity as transient:

```kotlin
flagsmith.getFeatureFlags(identity = "my-user", traits = listOf(Trait(key = "my_trait_key", value = 123.5), Trait(key = "my_other_key", value = true)), transient = true) { result ->
    result.fold(
        onSuccess = { onFlagsSuccess },
        onFailure = { onFlagsFailure }
    )
}
```

</TabItem>
<TabItem value="flutter" label="Flutter">

:::info

Transient Traits and Identities are supported starting from Flutter SDK version 6.0.0.

:::

Mark a Trait as transient:

```dart
var user = Identity(identifier: 'my-user');
var traits = [
    Trait(key: 'my_trait_key', value: 123.5, transient: true),
    Trait(key: 'my_other_key', value: true),
];
final flags = await fs.getFeatureFlags(user: user, traits: traits);
```

Mark the whole Identity as transient:

```dart
var user = Identity(identifier: 'my-user', transient: true);
var traits = [
    Trait(key: 'my_trait_key', value: 123.5),
    Trait(key: 'my_other_key', value: true),
];
final flags = await fs.getFeatureFlags(user: user, traits: traits);
```

</TabItem>
<TabItem value="ios" label="iOS">

</TabItem>
</Tabs>

### Transient Traits

### Multiple contexts

### Avoid storing PII in Flagsmith

### Cross-platform Segments
