# Edge API

:::info

The Edge API is only available with on our SaaS platform. It does not form part of our Open Source project.

:::

[The Flagsmith Architecture](/clients/overview#remote-evaluation) is based around a server-side flag engine. This comes
with a number of benefits, but it can increase latency, especially when the calls are being made from a location that is
far from the EU; the location of our current API. It also provides a single point of failure in the event of an AWS
region-wide outage.

The Edge API solves both of these issues. It provides a datastore and Edge compute API that is replicated across 8 AWS
regions, with latency-based routing and global failover in the event of a region outage.

The Edge API provides API service from the following AWS regions:

- Europe (London) - `eu-west-2`
- US East (Ohio) - `us-east-2`
- US West (N. California) - `us-west-1`
- Asia Pacific (Mumbai) - `ap-south-1`
- Asia Pacific (Sydney) - `ap-southeast-2`
- South America (São Paulo) - `sa-east-1`
- Asia Pacific (Seoul) - `ap-northeast-2`
- Asia Pacific (Singapore) - `ap-southeast-1`

## Enabling the Edge API

:::tip

Existing Organisations created before **7th June 2022** have their Projects deployed to the Core API. You can migrate
your Project over to our Edge API by going to the Project Settings page and hitting the "Start Migration" button. The
migration will take between 1 minute and an hour depending on how many Identities your Project has.

The Core API will continue to work normally during and following the migration. See the
[Migration Steps](#migration-steps) for more info.

:::

Once you have had your Projects migrated to Edge, all you will need to do is point your SDK to a new Flagsmith Edge API
URL at `edge.api.flagsmith.com`. This domain points to our Edge CDN. That's it!

The easiest way to do this is to upgrade to the latest version of the Flagsmith SDK for your language.

If you are unable to upgrade, you can manually point the existing SDK to the Edge API endpoint. So for example, in the
Java SDK we just add the `withApiUrl` line:

```java
FlagsmithClient flagsmithClient = FlagsmithClient.newBuilder()
        .setApiKey("aaa"))
        .withApiUrl("https://edge.api.flagsmith.com/api/v1/")
        .build();
```

Note that the Edge API URL is: `https://edge.api.flagsmith.com/api/v1/`.

Check the docs for your language SDK on how to override the endpoint URL prefix.

## Migration Steps

The migration process will carry out a one-way sync of your `Identity` data, from the Core API to the Edge API. All your
`Identity` data will continue to exist within the Core API, and you can continue to write `Identities` to the Core API
if you wish.

The goal is to get all of your applications running against the Edge API, where you will benefit from global low latency
as well as multi-region failover and fault tolerance.

### Step 1 - Prepare your applications

Set your applications up to point to the Flagsmith Edge API. This means going from `api.flagsmith.com` to
`edge.api.flagsmith.com`. You can either set this explicitly in our SDK or just ensure you are running the latest
version of the SDK; by default the _latest version_ of the SDKs will point to `edge.api.flagsmith.com`.

### Step 2 - Migrate your data

You can now trigger a one-way sync of data for each of your Flagsmith Projects within the Flagsmith Dashboard. You can
migrate your Project over to our Edge API by going to the Project Settings page and hitting the "Start Migration"
button. This will start a job that can take between 1 minute and 1 hour, depending on how much data you have. Once the
job is complete, all the Identities that were present in your Core API will be present in the Edge API.

The Core API will continue to work normally during and following the migration.

:::caution

As of Dec 1st, 2023, we will no longer be replicating Identities from the Core API to our Edge API. Please ensure your
applications are fully migrated before this point in time.

:::

If you have a product like a mobile app, where you cannot immediately force your users to upgrade (as opposed to a web
app, for example), you will likely generate Identity writes to the old Core API.

Following and during the migration, if we receive a request to an `Identity` endpoint that results in a write to the
core API, we will persist the data in the Core API _and replay the request into the Edge API_. You can then update your
API endpoints/SDKs in your own time to gradually move over the Edge API. This will give you time to migrate your users
over to the new version of your application.

Note that writes to the Core API will still work into the future, but the data will not be synchronised across the two
platforms (Core and Edge).

### Step 3 - Deploy your applications

Once your data has been copied onto the Edge API datastore, you can now deploy your applications that point to the new
endpoint `edge.api.flagsmith.com` and benefit from global low latency!

## Things you should know

### Some of the secure Identity endpoints have changed

If you are using our REST API to manipulate/update/list your Identities, some of these endpoints have changed. Please
get in touch if you need any help related to this.

### New Identity Overrides will only apply to the Edge API

After the migration, any new Identity Overrides you apply to flag values for specific Identities will only be applied to
the Edge API.

### Increment and Decrement endpoints are deprecated

You probably didn't know these existed though, right?

### Bulk Trait endpoint is deprecated

But you can still achieve the same functionality using our POST /identities endpoints.

### The API responses have been slimmed down

Our core API responses are quite verbose, and the SDKs ignore a lot of the fields they receive. We've taken the
opportunity to remove these additional, unused fields. This wont affect the SDKs but if you are using these values via
the REST API, things have changed. The list of removed fields is as follows:

```txt
trait.id
flag.feature.created_data
flag.feature.description
flag.feature.initial_value
flag.feature.default_enabled
flag.environment
flag.identity
flag.feature_segment
```

## Architecture

You can see our SaaS architecture [here](/system-administration/architecture.md#saas).

## How It Works

### Lambda@Edge

Our core [Rules Engine](https://github.com/Flagsmith/flagsmith-engine) has been factored out of our REST API. This
allows us to use it as a dependency within both the Flagsmith API, but also within a set of Lambda functions that
service SDK API calls. You can point your SDK clients to our global CDN `edge.api.flagsmith.com` which will serve your
request using a Lambda function running in an AWS data-centre near your client. This is how we reduce latency!

### DynamoDB Global Tables

We store state within our API - both related to the Environments for your Projects, but also for the Identities within
those Environments. Our Edge design sees us write this data through to DynamoDB global tables, which are replicated
globally. Our Lambda functions then connect to the nearest DynamoDB table to retrieve both Environment and Identity
data.
