[![Feature Flag, Remote Config and A/B Testing platform, Flagsmith](static-files/flagsmith-cover.png)](https://www.flagsmith.com/)

[![Stars](https://img.shields.io/github/stars/flagsmith/flagsmith)](https://github.com/Flagsmith/flagsmith/stargazers)
[![Docker Pulls](https://img.shields.io/docker/pulls/flagsmith/flagsmith)](https://hub.docker.com/u/flagsmith)
[![Docker Image Size](https://img.shields.io/docker/image-size/flagsmith/flagsmith)](https://hub.docker.com/r/flagsmith/flagsmith)
[![Join the Discord chat](https://img.shields.io/discord/517647859495993347)](https://discord.gg/hFhxNtXzgm)
[![Coverage](https://codecov.io/gh/Flagsmith/flagsmith/branch/main/graph/badge.svg?token=IyGii7VSdc)](https://codecov.io/gh/Flagsmith/flagsmith)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
<a href="https://depot.dev?utm_source=Flagsmith"><img src="https://depot.dev/badges/built-with-depot.svg" alt="Built with Depot" height="20"></a>

# Flagsmith: The most flexible and complete open-source feature flag management solution

## What is Flagsmith?

Flagsmith is an open-source feature management platform that offers remote configuration and experimentation solutions, as well as four different deployment options: Open source, on-premises/self-hosted, cloud, and private cloud.

As an open-source solution, Flagsmith provides flexibility and greater control over your choices. Thanks to our partnership with [OpenFeature](https://openfeature.dev/), you are never locked into one vendor.

With Flagsmith, you can evolve how your team releases software. Roll out, segment, experiment, and optimise with granular control. Stay secure by self-hosting, or choosing our private cloud deployment option.

* Feature flags: Release features behind the safety of a feature flag
* Make changes remotely: Easily toggle individual features on and off, and make changes without deploying new code
* A/B testing: Use segments to run A/B and multivariate tests on new features
* Segments: Release features to beta testers, collect feedback, and iterate
* Organisation management: Stay organised with orgs, projects, and roles for team members
* SDKs and frameworks: Choose from 15+ popular languages like TypeScript, .NET, Java, and more. Integrate with any framework, including React, Next.js, and more
* Integrations and MCP server: Use your favourite tools with Flagsmith

Flagsmith makes it easy to create and manage feature flags across web, mobile, and server-side applications. Just wrap a section of code with a flag, and then use Flagsmith to toggle that feature on or off for different environments, users, or user segments.

## See Flagsmith in action

If you want a step-by-step demonstration of how to get started with Flagsmith, why not [try our interactive demo](https://www.flagsmith.com/demo).

<p align="center">
  <a href="https://www.flagsmith.com/demo">
  <img width="75%" height="75%" src="static-files/ReadMe_Demo.gif" alt="Try our interactive demo">
</p>

## Get up and running with Flagsmith in less than a minute:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/Flagsmith/flagsmith/main/docker-compose.yml
docker-compose -f docker-compose.yml up
```

The application will bootstrap an admin user, organisation, and project for you. You'll find a link to set your password in your Compose logs:

```txt
Superuser "admin@example.com" created successfully.
Please go to the following page and choose a password: http://localhost:8000/password-reset/confirm/.../...
```

## Check a feature flag in your code

Once Flagsmith is running, checking a flag takes one function call. Here's how it looks in JavaScript:

```javascript
import flagsmith from 'flagsmith';

flagsmith.init({
  environmentID: '<your environment key>',
  onChange: () => {
    if (flagsmith.hasFeature('show_demo_button')) {
      // show the new feature
    }
  },
});
```

Follow the [quick start guide](https://docs.flagsmith.com/getting-started/quick-start) for the full walkthrough, or pick your language from our [SDK docs](https://docs.flagsmith.com/integrating-with-flagsmith/sdks/) to see the same thing in Python, Java, Go, .NET, and more.

![Flagsmith Screenshot](static-files/screenshot.png)

## Contribute to Flagsmith Open Source

We love contributions from the community and are always looking to improve our [open-source feature management platform](https://www.flagsmith.com/)! Here are our [contribution guidelines](https://docs.flagsmith.com/platform/contributing).

## Flagsmith hosted SaaS

You can try our hosted version for free at [app.flagsmith.com/signup](https://app.flagsmith.com/signup).

## Community Resources

* [Visit our docs](https://docs.flagsmith.com/)
* [Chat with other developers on Discord](https://discord.com/invite/hFhxNtXzgm)
* If you need help getting up and running, [get in touch](https://www.flagsmith.com/contact-us)

## Available SDKs

### Client side ([docs](https://docs.flagsmith.com/integrating-with-flagsmith/sdks/client-side-sdks/))

* [JavaScript](https://docs.flagsmith.com/integrating-with-flagsmith/sdks/client-side-sdks/javascript)
* [React](https://docs.flagsmith.com/integrating-with-flagsmith/sdks/client-side-sdks/react)
* [Next.js and SSR](https://docs.flagsmith.com/integrating-with-flagsmith/sdks/client-side-sdks/nextjs-and-ssr)
* [Android](https://docs.flagsmith.com/integrating-with-flagsmith/sdks/client-side-sdks/android)
* [iOS](https://docs.flagsmith.com/integrating-with-flagsmith/sdks/client-side-sdks/ios)
* [Flutter](https://docs.flagsmith.com/integrating-with-flagsmith/sdks/client-side-sdks/flutter)

### Server side ([docs](https://docs.flagsmith.com/integrating-with-flagsmith/sdks/server-side))

* [Python](https://github.com/Flagsmith/flagsmith-python-client)
* [Java](https://github.com/Flagsmith/flagsmith-java-client)
* [.NET](https://github.com/Flagsmith/flagsmith-dotnet-client)
* [Node.js](https://github.com/Flagsmith/flagsmith-nodejs-client)
* [Ruby](https://github.com/Flagsmith/flagsmith-ruby-client)
* [PHP](https://github.com/Flagsmith/flagsmith-php-client)
* [Go](https://github.com/Flagsmith/flagsmith-go-client)
* [Rust](https://github.com/Flagsmith/flagsmith-rust-client)
* [Elixir](https://github.com/Flagsmith/flagsmith-elixir-client)

### Using OpenFeature
 
Prefer the vendor-neutral route? You can use Flagsmith through [OpenFeature](https://openfeature.dev/) with providers for the following languages:
 
* [Go](https://github.com/open-feature/go-sdk-contrib/tree/main/providers/flagsmith)
* [Java](https://github.com/open-feature/java-sdk-contrib/tree/main/providers/flagsmith)
* [JavaScript (client-side)](https://github.com/open-feature/js-sdk-contrib/tree/main/libs/providers/flagsmith-client)
* [JavaScript (server-side)](https://github.com/open-feature/js-sdk-contrib/tree/main/libs/providers/flagsmith)
* [Kotlin](https://github.com/Flagsmith/flagsmith-openfeature-provider-kotlin)
* [.NET](https://github.com/open-feature/dotnet-sdk-contrib/tree/main/src/OpenFeature.Contrib.Providers.Flagsmith)
* [Python](https://github.com/Flagsmith/flagsmith-openfeature-provider-python)
* [Ruby](https://github.com/open-feature/ruby-sdk-contrib/tree/main/providers/openfeature-flagsmith-provider)
* [Rust](https://github.com/open-feature/rust-sdk-contrib/tree/main/crates/flagsmith)

Check out the [OpenFeature docs](https://docs.flagsmith.com/integrating-with-flagsmith/openfeature) for setup.

## Open Source Philosophy

The majority of our platform is open source under the [BSD-3-Clause license](https://github.com/Flagsmith/flagsmith?tab=BSD-3-Clause-1-ov-file#readme). A small number of repositories are under the MIT license.

We built Flagsmith as the open-source feature flag tool we needed but couldn't find on GitHub. Our core functionality stays open, always. Read our [open letter to developers](https://www.flagsmith.com/about-us).

## Open Source vs Paid

As our core functionality is open, you can use our open-source feature flag and remote config management platform no matter what. Enterprise-level governance and management features are available with a valid Flagsmith Enterprise license.

To learn more, [contact us](https://www.flagsmith.com/contact-us) or see our [version comparison](https://docs.flagsmith.com/version-comparison).

## Contributors

Thank you to the open source community for your contributions and for building this with us!

<a href="https://github.com/flagsmith/flagsmith/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=flagsmith/flagsmith" />
</a>

Made with [contrib.rocks](https://contrib.rocks).
