# Authentication Methods

:::tip

Organisations within Flagsmith can be locked to a single authentication method if required, meaning that accounts can
neither be created or logged into with anything other than the method specified.

This can be configured at an Organisation level by a Super-Administrator. Please get in touch if you need help with
this.

:::

As well as Email/Password and OAuth2 via Google or Github, we also provide the following methods of authentication.

## SAML

The Flagsmith platform can be configured for a given organisation to use SAML authentication. To configure SAML login
for your organisation please get in touch with us directly to help set it up.

Note that users authenticated via SAML can only belong to one organisation, the one that the SAML configuration is tied
to.

To set up SAML authentication, we will provide you with a unique name for your SAML organisation that you must then
enter when prompted by the 'Single Sign on' dialog. We will also provide you with our Service Provider metadata and
expect your IdP metadata in return.

### Mapping information

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

## LDAP

LDAP Authentication is available in our [Enterprise Edition](../enterprise-edition.md). Please contact us if this is of
interest. We also support sync-ing of LDAP groups into [Flagsmith RBAC groups](permissions.md#groups).

## AD FS

Active Directory Federation Services Authentication is available in our [Enterprise Edition](../enterprise-edition.md).

## Okta

Okta Integration is available in our [Enterprise Edition](../enterprise-edition.md).
