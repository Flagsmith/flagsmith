---
title: SAML
---

:::tip

Organisations within Flagsmith can be locked to a single authentication method if required, meaning that accounts can
neither be created or logged into with anything other than the method specified.

This can be configured at an Organisation level by a Super-Administrator. Please get in touch if you need help with
this.

:::

## Prerequisites

### SaaS Customers & Private Cloud

To configure the SAML integration with Flagsmith, you must have created a valid organisation at app.flagsmith.com or
your private cloud URL. The organisation must be on our Enterprise plan. You should contact the Flagsmith support team
(support@flagsmith.com) to create a SAML organisation and we will provide you with your organisation name.

### Enterprise Self Hosted

To configure the SAML integration with Flagsmith self hosted, you must be using an Enterprise licence to self host the
Flagsmith application. You should then complete the steps listed
[here](https://docs.flagsmith.com/deployment/authentication#saml---enterprise-on-premise) up to and including the line
which states ‘_Once you've completed these fields, hit the Save button to create the SAML configuration._’

## Procedure

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
