---
title: SAML
---

:::tip

Organisations within Flagsmith can be locked to a single authentication method if required, meaning that accounts can
neither be created or logged into with anything other than the method specified.

This can be configured at an Organisation level by a Super-Administrator. Please get in touch if you need help with
this.

:::

As well as Email/Password and OAuth2 via Google or Github, we also provide the following methods of authentication.

## SaaS

The Flagsmith platform can be configured for a given organisation to use SAML authentication. To configure SAML login
for your organisation please get in touch with us directly to help set it up.

The steps we need to go through are something like:

1. You contact us to enable SAML for your organisation.
2. We create an XML file and provide it to you along with your SAML organisation name.
3. You supply the XML to your SAML IDP and receive some XML in return. You might need to apply some
   [attribute mappings](#attribute-mapping-information).
4. You send us this XML and we add it to Flagsmith.
5. You log in by visiting https://app.flagsmith.com/login clicking on "Single Sign On" and entering your SAML
   organisation name from step 2.

Note that users authenticated via SAML can only belong to one organisation, the one that the SAML configuration is tied
to.

To set up SAML authentication, we will provide you with a unique name for your SAML organisation that you must then
enter when prompted by the 'Single Sign on' dialog. We will also provide you with our Service Provider metadata and
expect your IdP metadata in return.

## Enterprise On-premise

:::tip

SAML authentication is only available as part of our Enterprise Plans. Please
[get in touch](https://flagsmith.com/contact-us/) if this is something you are interested in!

:::

To allow an Organisation on the Flagsmith platform to login using SAML authentication, you'll need to access the admin
interface. Instructions on how to access the admin interface can be found
[here](https://docs.flagsmith.com/deployment/configuration/django-admin).

Once you've logged into the django admin interface, you'll need to click on the 'Saml Configurations' option in the menu
on the left. From here, you should see a list of existing SAML configuration entities. To create a new one, click on the
'ADD SAML CONFIGURATION' button in the top right corner of the screen.

You should see a screen similar to the following.

![SAML Auth Setup](/img/saml-auth-setup.png)

From the drop down next to **Organisation**, select the organisation in the Flagsmith platform that you want to
configure for SAML authentication.

Next to **Organisation name**, add a name without any spaces that identifies the organisation uniquely for the
installation of Flagsmith you're working on. This is what users will provide when authenticating with SAML so that the
platform knows where to redirect them.

Next to **Frontend url**, add in the URL at which your Frontend application is running. This is where users will be
redirected to on a successful SAML authentication.

For now, we'll leave **Idp metadata xml** empty.

If you require the ability to initiate authentication requests from your IdP (IdP initiated), you'll need to check the
box next to **Allow IdP-initiated (unsolicited) login**.

Once you've completed these fields, hit the **Save** button to create the SAML configuration.

Now, we need to grab the Flagsmith service provider metadata to configure the integration on your IDP. To do this, open
a new browser tab and head to `https://<your Flagsmith API>/api/v1/auth/saml/<organisation_name>/metadata/` where
`<organisation_name>` is the name you provided above. From here, copy and paste what you see in the web page into a new
text file and save that file as `flagsmith-sp-metadata.xml` or similar.

Note: do not use 'save page as' from your browser as this will likely result in the metadata being incorrect and the
integration will not work.

Now you can use this XML metadata to create the integration on your IDP. Once created on the IDP, you can add the IDP
metadata into the **Idp metadata xml** field that we left blank earlier.

## Attribute Mapping information

To uniquely identify users, we attempt to retrieve a unique identifier from either the `subject-id` or `uid` claim, or
we use the content of the `NameID` attribute.

We also map the following Flagsmith user attributes to the following claims in the SAML response.

| Flagsmith Attribute | IdP claims                                             |
| ------------------- | ------------------------------------------------------ |
| `email`             | `mail`, `email` or `emailAddress`                      |
| `first_name`        | `gn`, `givenName` or (the first part of) `displayName` |
| `last_name`         | `sn`, `surname` or (the second part of) `displayName`  |

Here's an example configuration from Google's SAML app creation flow.

<div style={{textAlign: 'center'}}><img width="75%" src="/img/saml-mapping-configuration.png"/></div>

## Group Sync

You can configure Flagsmith to add or remove a user from a group (on login) based on your SAML response.

E.g: let's assume you have a group named `team` in your system and whenever a user logs in into Flagsmith you want
either that user to be added (if the group is part of relevant SAML attribute, but the user is not already part of the
group) to the equivalent Flagsmith group or be removed (if the group is not part of the relevant SAML attribute, but the
user is part of the group) from it.

### Configuration

To configure this, you need to create an equivalent group in Flagsmith using the SAML name of the group as the External
ID. e.g: if your SAML attribute looks like the below xml snippet (and you want the `team` group to be synced):

```xml
<saml2:Attribute Name="groups">
    <saml2:AttributeValue
        xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xs:anyType">team
    </saml2:AttributeValue>
    <saml2:AttributeValue
        xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xs:anyType">for_saml_group_test
    </saml2:AttributeValue>
</saml2:Attribute>
```

Then you need to create an equivalent group in the Flagsmith that will look like this:

<div style={{textAlign: 'center'}}><img width="75%" src="/img/saml-group-sync-external-id.png"/></div>
