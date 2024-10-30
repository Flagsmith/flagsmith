---
title: Okta
---

Flagsmith can integrate with your Okta single sign-on (SSO) by using [SAML](/system-administration/authentication/SAML).
We provide a [first-party Okta integration](https://www.okta.com/integrations/flagsmith/) to simplify the setup.

## Prerequisites (SaaS)

Get in touch with Flagsmith support to obtain the single sign-on URL and audience URI to use when configuring your Okta
application.

## Prerequisites (self-hosted)

Create a SAML configuration by following the [instructions to set up SAML](/system-administration/authentication/SAML).
Leave the identity provider metadata blank for now.

## Procedure

Add the [first-party Flagsmith integration](https://www.okta.com/integrations/flagsmith/) to your Okta account. Then,
open it in the Okta dashboard and:

- Select the "Sign On" tab and click "Edit"
- Scroll down to "Advanced Sign-on Settings", fill out the two fields and then click Save:
  - **API Base URL** should be `https://api.flagsmith.com` on SaaS, or your API root URL otherwise
  - **SAML Organisation** will be provided by Flagsmith support on SaaS. Otherwise, this refers to the "Organisation
    name" field [when creating a SAML Configuration](/system-administration/authentication/SAML)
- Staying on the "Sign On" tab, find the "Metadata URL" in the "Sign on methods" section. Save this metadata to a file
  and send it to [Flagsmith support](mailto:support@flagsmith.com), or add it to the "IdP Metadata XML" field of your
  Flagsmith SAML Configuration if self-hosting

Once Flagsmith support have confirmed that the metadata has been uploaded, your users will be able to sign in via the
Okta applications dashboard and the Flagsmith dashboard by entering the organisation name given to you by Flagsmith
support, or the SAML configuration name if self-hosting.

## User attributes

By default, Flagsmith's Okta integration will map your users' email address, given name and surname so that they are
visible within Flagsmith. If you need to map different attributes, please
[contact support](mailto:support@flagsmith.com) or refer to the
[documentation on SAML attribute mappings](/system-administration/authentication/SAML/#attribute-mapping).

## Troubleshooting

If your users are unable to sign in to the Flagsmith application via Okta, it’s important to check if they already have
a user account in Flagsmith with their Okta email address. If they do, make sure that they are not a member of any other
organisations than the one set up in the Okta integration.
