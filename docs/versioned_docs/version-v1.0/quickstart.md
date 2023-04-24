---
sidebar_position: 2
sidebar_label: Quick Start
---

# Flagsmith Quick Start Guide

Let's get up and running in 5 minutes. We're going to run through the following steps:

1. Create an account on [Flagsmith.com](https://flagsmith.com/) and add your first Flag.
2. Import our Javascript SDK into your web page.
3. Connect to the Flagsmith API and get your flags.
4. Update your application based on the flag value.

## 1. Create an account with Flagsmith

:::tip

To get up and running quickly, we're going to use the hosted service at flagsmith.com, but you can easily run the
[platform locally via Docker](deployment/docker.md).

:::

Head over to [Flagsmith](https://app.flagsmith.com/signup) and create an account. We're going to create an Organisation
and a Project.

<div style={{textAlign: 'center'}}><img width="75%" src="/img/quickstart/demo_create_1.png"/></div>

Flagsmith manages Flags with Projects, so let's create one now:

<div style={{textAlign: 'center'}}><img width="75%" src="/img/quickstart/demo_create_2.png"/></div>

Flagsmith organises Projects into separate Environments. When you create a Project, Flagsmith automatically creates
`Development` and `Production` Environments. We will come to these Environments later. Let's go ahead and create our
first Flag. This flag is simply going to control whether a button shows on our super simple web page.

<div style={{textAlign: 'center'}}><img width="75%" src="/img/quickstart/demo_create_3.png"/></div>

Flags can either a `Boolean` value, a `String` value, or a combination of both. For now, we're just going to use the
`Boolean` value of the flag to control whether the button shows. Let's go ahead and create a flag called
`show_demo_button`. We're going to leave it as Disabled by default:

<div style={{textAlign: 'center'}}><img width="75%" src="/img/quickstart/demo_create_4.png"/></div>

## 2. Import the Javascript SDK

OK so we've set up our flag; now let's bring it into our application. We have a (very!) simple web page:

```html
<!DOCTYPE html>
<html lang="en">
 <head>
  <meta charset="utf-8" />
  <title>Flagsmith Quickstart Guide</title>
 </head>
 <body>
  <h1>Here's our button!</h1>
  <div id="submit_button">
   <input type="submit" value="Flagsmith Quickstart Button!" />
  </div>
 </body>
</html>
```

It's pretty simple, and looks like this:

<div style={{textAlign: 'center'}}><img width="75%" src="/img/quickstart/demo_create_8.png"/></div>

As per our [Javascript Docs](clients/client-side/javascript.md), we will import the SDK inline into our web page:

```html
<script src="https://cdn.jsdelivr.net/npm/flagsmith/index.js"></script>
```

## 3. Connect to the Flagsmith API

We can now connect to the Flagsmith API and get our Flags. When you initialise the Flagsmith SDK, you have to provide an
Environment ID. This way, the SDK knows which Project and Environment to grab flags for. Head to the Environment
Settings page within Flagsmith, and copy the API key:

<div style={{textAlign: 'center'}}><img width="75%" src="/img/quickstart/demo_create_6.png"/></div>

Then paste your API key into the code below:

```html
<script>
 flagsmith.init({
  environmentID: '<add your API key here!>',
  onChange: (oldFlags, params) => {},
 });
</script>
```

Now when the browser opens the web page, it will download the Javascript SDK and make a call to `api.flagsmith.com` to
get the flags for our Environment. You can see this in the browser network tab:

<div style={{textAlign: 'center'}}><img width="75%" src="/img/quickstart/demo_create_7.png"/></div>

You can see here that the flag is being returned by the Flagsmith API and it has `"enabled": false` as the value.

## 4. Hook up our Application

Let's hook this value up to our button, so that the value of the flag controls whether the button is hidden or shown.

```html
<script>
 flagsmith.init({
  environmentID: '<add your API key here!>',
  onChange: (oldFlags, params) => {
   if (flagsmith.hasFeature('show_demo_button')) {
    var submit_button = document.getElementById('submit_button');
    submit_button.style.display = 'block';
   }
  },
 });
</script>
```

This code sets up a callback, which is triggered when we get a response back from the Flagsmith API. We simply check for
the state of the flag and set the display visibility based on the result.

Our entire webpage now reads like this:

```html
<!DOCTYPE html>
<html lang="en">
 <head>
  <meta charset="utf-8" />
  <title>Flagsmith Quickstart Guide</title>
  <script src="https://cdn.jsdelivr.net/npm/flagsmith/index.js"></script>
  <script>
   flagsmith.init({
    environmentID: 'ZfmJTbLQZrhZVHkVhXbsNi',
    onChange: (oldFlags, params) => {
     if (flagsmith.hasFeature('show_demo_button')) {
      var submit_button = document.getElementById('submit_button');
      submit_button.style.display = 'block';
     }
    },
   });
  </script>
 </head>
 <body>
  <h1>Here's our button!</h1>
  <div id="submit_button" style="display:none">
   <input type="submit" value="Flagsmith Quickstart Button!" />
  </div>
 </body>
</html>
```

If we go back and refresh our browser, you will see that the button has now disappeared.

<div style={{textAlign: 'center'}}><img width="75%" src="/img/quickstart/demo_create_9.png"/></div>

We've not put the control of the button visibility behind our Flagsmith Flag! You can now go back to the Flagsmith
dashboard and enable the flag:

<div style={{textAlign: 'center'}}><img width="75%" src="/img/quickstart/demo_create_10.png"/></div>

Return to your browser, refresh the page, and the button will re-appear.

## Finishing Up

This was a pretty simple demo, but it covers the core concepts involved in integrating Flagsmith into your application.
From here, some areas of the documentation you might want to check out are:

- A deeper overview of the application - [Features](basic-features/managing-features.md),
  [Identities](basic-features/managing-identities.md) and [Segments](basic-features/managing-segments.md).
- More details about our [API and SDKs](clients/rest.md).
- How you can [run Flagsmith yourself](deployment/overview.md) or use our [Hosted API](https://flagsmith.com/).
