---
title: Okta
---

Flagsmith can integrate with your Okta single sign-on (SSO) by using [SAML](/system-administration/authentication/SAML).

## Prerequisites (SaaS)

Get in touch with Flagsmith support to obtain the single sign-on URL and audience URI to use when creating your Okta
SAML application.

## Prerequisites (self-hosted)

Create a SAML configuration by following the
[instructions to set up SAML](/system-administration/authentication/01-SAML/index.md#setup-self-hosted). Leave the
identity provider metadata blank for now.

## Setup

[Create an Okta SAML application](https://help.okta.com/oag/en-us/content/topics/access-gateway/add-app-saml-pass-thru-add-okta.htm)
from the Okta management to represent your Flagsmith organisation with the following settings:

- **Single sign-on URL**: Obtain this URL from Flagsmith support, or from your
  [SAML configuration if self-hosting](/system-administration/authentication/SAML/#assertion-consumer-service-url)
- **Audience URI (SP Entity ID)**: Obtain this from Flagsmith support, or use your
  [SAML configuration name](/system-administration/authentication/SAML/#setup-self-hosted) if self-hosting

Once your Okta application is created, you can
[download its corresponding identity provider metadata](https://support.okta.com/help/s/article/Location-to-download-Okta-IDP-XML-metadata-for-a-SAML-app-in-the-new-Admin-User-Interface?language=en_US)
and send it to Flagsmith support, or add it to your SAML configuration if self-hosting.
