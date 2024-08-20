---
title: SAML single sign-on (SSO)
---

:::tip

SAML authentication requires an [Enterprise subscription](https://flagsmith.com/pricing).

:::

## Setup

To enable SAML authentication for your Flagsmith organisation, you have to go to your organisations settings, and in the
SAML tab, you'll be able to configure it.

In the UI, you will be able to configure the following fields.

**Name:** (**Required**) A short name for the organisation, used as the input when clicking "Single Sign-On" at login.
This name must be unique across all Flagsmith organisations and forms part of the URL that your identity provider will
post SAML messages to during authentication.

**Frontend URL**: (**Required**) This should be the base URL of the Flagsmith dashboard. Users will be redirected here
after authenticating successfully.

**Allow IdP-initiated**: If enabled, users will be able to log in directly from your identity provider without needing
to visit the Flagsmith login page.

**IdP metadata XML**: The metadata from your identity provider.

Once you have configured your identity provider, you can download the service provider metadata XML document with the
button "Download Service Provider Metadata".

### Assertion consumer service URL

The assertion consumer service (ACS) URL, also known as single sign-on URL, for this SAML configuration will be at the
following path, replacing `flagsmith.example.com` with your Flagsmith API's domain:

```
https://flagsmith.example.com/api/v1/auth/saml/YOUR_SAML_CONFIGURATION_NAME/response/
```

### Canonicalization methods

Some identity providers require the service provider to support canonicalization methods that are not allowed by
default. You can see the methods that are enabled by default
[here](https://github.com/IdentityPython/pysaml2/blob/88feeba03c2f891a31a86cbb24b210070aab1fdc/src/saml2/xmldsig/__init__.py#L67-L70).

You can enable additional canonicalization methods by setting the `EXTRA_ALLOWED_CANONICALIZATIONS` environment variable
to a comma-separated list of canonicalization method URIs. For example:

```sh
EXTRA_ALLOWED_CANONICALIZATIONS=http://www.w3.org/TR/2001/REC-xml-c14n-20010315#,http://www.w3.org/TR/2001/REC-xml-c14n-20010315#WithComments
```

### Force SSL after authentication

You can configure Flagsmith to ignore the `X-Forwarded-Proto` HTTP header and always use HTTPS for the ACS URL by
setting the `SAML_FORCE_SSL` environment variable to `True`.

## Attribute mapping

Flagsmith will look for the following SAML attributes, in order, to uniquely identify a SAML user:

- `subject-id`
- `uid`
- `NameID`

Flagsmith also maps user attributes from the following claims in the SAML assertion:

| Flagsmith attribute | IdP claims                                           |
| ------------------- | ---------------------------------------------------- |
| Email               | `mail`, `email` or `emailAddress`                    |
| First name          | `gn`, `givenName` or the first part of `displayName` |
| Last name           | `sn`, `surname` or the second part of `displayName`  |

To add custom attribute mappings, edit your SAML configuration and open the Attribute Mappings tab.

## Permissions for SAML users

By default, users logging in via SAML will have no permissions to view or modify anything in the Flagsmith dashboard.
You can customise this by creating a [group](/system-administration/rbac) with the "Add new users by default" option
enabled, and assigning your desired default permissions to that group.

### Using groups from your SAML IdP

Flagsmith can add or remove a user from groups based on your identity provider's SAML response when logging in.

When a user logs in, Flagsmith will assign groups to a user based on the `groups` claim values from your identity
provider's SAML assertion. Each value of the `groups` claim should correspond to the "External ID" of a Flagsmith group,
which can be set during group creation:

<div style={{textAlign: 'center'}}><img width="75%" src="/img/saml-group-sync-external-id.png"/></div>

For example, a SAML assertion with the following `groups` claim would assign the user to the Flagsmith groups with
external IDs of `my_group` and `my_other_group`:

```xml
<saml2:Attribute Name="groups">
    <saml2:AttributeValue
        xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xs:anyType">my_group
    </saml2:AttributeValue>
    <saml2:AttributeValue
        xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="xs:anyType">my_other_group
    </saml2:AttributeValue>
</saml2:Attribute>
```

Note that the claim must be named exactly `groups`. Some identity providers like Azure Active Directory or Microsoft
Entra ID add a namespace to their claims such as `http://schemas.microsoft.com/ws/2008/06/identity/claims/groups`, which
must be mapped to the `groups` claim that Flagsmith expects. If this is the case, please notify Flagsmith support to add
the correct mapping for you. Or, if you are self-hosting, add a claim mapping like this one to your SAML configuration
from the Django admin console:

![Mapping Entra ID groups to Flagsmith groups](/img/saml-group-mapping.png)
