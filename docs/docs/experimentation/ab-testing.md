---
title: A/B Testing
sidebar_label: A/B Testing
sidebar_position: 10
---

A/B testing enables you to experiment with design and functionality variants of your application. The data generated will allow you to make modifications to your app, safe in the knowledge that it will have a net positive effect.

You can use Flagsmith to perform A/B Tests. Using a combination of [Multivariate Flags](/basic-features/managing-features.md#multi-variate-flags) and a 3rd party analytics tool like [Amplitude](https://amplitude.com/) or [Mixpanel](https://mixpanel.com/), you can easily perform complex A/B tests that will help improve your product.

Running AB tests require two main components: a bucketing engine and an analytics platform. The bucketing engine is used to put users into a particular AB testing bucket. These buckets will control the specific user experience that is being tested. The analytics platform will receive a stream of event data derived from the behaviour of the user. Combining these two concepts allows you to deliver seamless AB test.

We have [integrations](/integrations) with a number of analytics platforms. If we don't integrate with the platform you are using, you can still manually send the test data to the downstream platform manually.

By the end of this tutorial, you will be able to:

-   Set up a Multivariate Flag in Flagsmith for A/B testing.
-   Implement logic in your application to bucket users and display variants.
-   Send A/B test data to an analytics platform.
-   Understand how to use anonymous identities for A/B testing on unknown users.

## Before you begin

To follow this tutorial, you will need:

- A basic understanding of [Multivariate Flags](/basic-features/managing-features.md#multi-variate-flags) in Flagsmith.
- Access to a third-party analytics platform (e.g., Amplitude, Mixpanel) where you can send custom events. You can explore Flagsmith [integrations](/integrations) for this purpose.
- A development environment for your application where you can implement changes and integrate the Flagsmith SDK.

## Scenario - Testing a new Paypal button

For this example, lets assume we have an app that currently accepts Credit Card payments only. We have a hunch that we are losing out on potential customers that would like to pay with Paypal. We're going to test whether adding Paypal to the payment options increases our checkout rate.

We have a lot of users on our platform, so we don't want to run this test against our entire user-base. We want 90% of our users to be excluded from the test. Then for our test, 5% of our users will see the new Paypal button, and the remaining 5% will not see it. So we will have 3 buckets:

1. Excluded (Control) Users
2. Paypal Test Button Users
3. Test users that don't see the Paypal Button

Because Flagsmith Flags can contain both boolean states as well as multivariate flag values, we can make use of both. We will use the boolean flag state to control whether to run the test. Then, if the flag is `enabled`, check the Multivariate value. In this example, we will only show the Paypal button if the value is set to `show`.

## Steps

1. Create a new [Multivariate Flag](/basic-features/managing-features.md#multi-variate-flags) that will control which of the 3 buckets the user is put into. We'll call this flag `paypal_button_test`. We will provide 3 variate options:

   1. Control - 90% of users
   2. Paypal Button - 5% of users
   3. Test users that don't see the Paypal Button - 5% of users

2. In our app, we want to [identify](/basic-features/managing-identities.md) each user before they start the checkout process. All Flagsmith Multivariate flags need us to identify the user, so we can bucket them in a reproducible manner.
3. When we get to the checkout page, check the `value` of the `paypal_button_test` flag for that user. If it evaluates to `show`, show the Paypal payment button. Otherwise, don't show the button.
4. Send an event message to the analytics platform, adding the name/value pair of `paypal_button_test` and the value of the flag; in this case it would be one of either `control`, `show` or `hide`.
5. Deploy our app, enable the flag and watch the data come in to your analytics platform.

Here is what creating the Flag would look like.

![Image](/img/ab-test-paypal-example.png)

Once the test is set up, and the flag has been enabled, data will start streaming into the analytics platform. We can now evaluate the results of the tests based on the behavioral changes that the new button has created.

## Handling Anonymous/Unknown Identities

To do A/B testing you need to use Identities. Without an Identity to key from, it's impossible for the platform to serve a consistent experience to your users.

What if you want to run an A/B test in an area of your application where you don't know who your users are? For example on the homepage of your website? In this instance, you need to generate _Anonymous Identities_ values for your users. In this case we will generate a _GUID_ for each user.

A _GUID_ value is just a random string that has an extremely high likelihood of being unique. There's more info about generating GUID values [on Stack Overflow](https://stackoverflow.com/a/2117523).

The general flow would be:

1. A new browser visits your website homepage for the first time.
2. You see that this is an anonymous user, so you generate a random _GUID_ for that user and assign it to them.
3. You send that GUID along with an Identify call to Flagsmith. This will then segment that visitor.
4. You add a cookie to the browser and store the GUID. That way, if the user returns to your page, they will still be in the same segment.

These techniques will be slightly different depending on what platform you are developing for, but the general concept will remain the same.

## Next steps

- Explore [Flagsmith's Integrations](/integrations) with analytics platforms.
- Learn more about [managing Identities](/basic-features/managing-identities.md) in Flagsmith.
