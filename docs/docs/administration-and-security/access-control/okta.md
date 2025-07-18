---
title: Okta
sidebar_label: Okta
sidebar_position: 30
---

Flagsmith can integrate with Okta single sign-on (SSO) by using SAML. We provide a first-party Okta integration to
simplify the setup.

## Setup

1. Create a [Flagsmith SAML configuration](/administration-and-security/access-control/saml#setup). You can leave the
   identity provider metadata blank for now.
2. Add the [Flagsmith Okta integration](https://www.okta.com/integrations/flagsmith/) to your Okta account, and open 
   it in the Okta dashboard.
3. Select the "Sign On" tab, and click "Edit".
4. Under "Advanced Sign-on Settings", fill out these fields and then click Save:
   - **API Base URL** should be `https://api.flagsmith.com` on SaaS, or your API root URL otherwise.
   - **SAML Organisation** should be the name of the SAML configuration you previously created.
5. Staying on the "Sign On" tab, find the "Metadata URL" in the "Sign on methods" section. Save this metadata to a file
  and upload it to the "IdP Metadata XML" of your Flagsmith SAML configuration.

Once your Flagsmith SAML configuration has your Okta IdP metadata set, your users can log in to Flagsmith with Okta by
clicking "Single Sign-On" at the login page, and typing the name of the SAML configuration you created.

## User attributes

By default, the Flagsmith Okta integration will map your users' Okta email address, given name and surname so that they
are visible within Flagsmith. If you need to map different attributes, you can
[customise the attribute mappings](/administration-and-security/access-control/saml#attribute-mapping) on your SAML
configuration.
