---
title: Testing Push Notifications
---

## The Problem

Sending out Push Notifications (and Email messages!) accurately and without error is notoriously difficult. Combine the
fact that they can be extremely sensitive/error prone across dev/staging/production environments, along with the
inability to recall them if you've sent them out in error, and you have a subject area that can strike fear into even
the most hardened engineer. Deploying code that sends out messages to potentially millions of users is not a relaxing
experience.

When you send a push notification via [Firebase FCM](https://firebase.google.com/docs/cloud-messaging), you can test
things out by sending messages to a specific device via a device token. The problem is that it’s quite technical to get
set up, and these tokens are not readily surfaced within an app. In addition, if you want to test out a campaign it’s
likely you will want to try sending push notifications to more than 1 device so you can test between QA, product owners,
developers and marketing when validating behavior and fixing bugs.

## The Solution

We want to be able to test out the end-to-end process of sending marketing push notifications, before rolling them out
in production. This often means working across marketing, product and engineering teams in what can become a complex,
error prone process. Testing this process before pushing things live is one of the best ways of making sure that your
procedures are working.

You can utilise Flagsmith in combination with Firebase FCM topics to make this easier. When sending a push notification
to a topic, Firebase will send that notification to all the users that are subscribed to that named topic. We will
eventually use these topics to target marketing messages to our user-base, but we can also use them to test out the
messaging with our team before sending them out to all our users.

We're going to create a flag in Flagsmith called `fcm_marketing_beta`. We want anyone with this flag enabled in
Flagsmith to be subscribed to the `marketing` FCM topic. We will then send messages out via this topic.

We use the following code in our React Native application to do this:

```javascript
const isInMarketingBeta = flagsmith.hasFeature('fcm_marketing_beta');

if (isInMarketingBeta) {
 messaging().subscribeToTopic('marketing');
}
```

### Adding Individual Users

Once our code is deployed, we can start enabling this flag for individual users of our application. Using the
[Identities](/basic-features/managing-identities.md) aspect of Flagsmith, we can enable this flag for our user in the
application, as well as enabling it for some of our close team mates.

![Overriding the Flag for our User](/img/guides/fcm-user-override.png)

Refreshing the application will cause the `messaging().subscribeToTopic('marketing');` code to execute, adding us to the
FCM topic.

![FCM Subscriptions](/img/guides/fcm-subscribed.png)

Our device has now appeared in this topic, and we can use the topic to start sending test marketing messages.

### Adding Teams of Users with Segments

We can now make use of [Flagsmith Segments](/basic-features/managing-segments.md) to add all our team to this beta FCM
group.

Create a Segment, add a rule that will include our team (in our case we match against the domain name of an email
Trait), and override the `fcm_marketing_beta` Flag with this Segment:

![Overriding the Flag for our Segment](/img/guides/fcm-segment.png)

We're now able to test these messages with our entire team, no further code or deployments required!
