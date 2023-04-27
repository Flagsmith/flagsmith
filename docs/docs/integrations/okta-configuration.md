# Okta Configuration Guide

## Prerequisites

### SaaS Customers & Private Cloud

To configure the Okta integration with Flagsmith, you must have created a valid organisation at app.flagsmith.com or
your private cloud URL. The organisation must be on our scale up or enterprise plan. You should contact the Flagsmith
support team (support@flagsmith.com) to create a SAML organisation and we will provide you with your organisation name.

### Enterprise Self Hosted

To configure the Okta integration with Flagsmith self hosted, you must be using an Enterprise licence to self host the
Flagsmith application. You should then complete the steps listed
[here](https://docs.flagsmith.com/deployment/authentication#saml---enterprise-on-premise) up to and including the line
which states ‘_Once you've completed these fields, hit the Save button to create the SAML configuration._’

## Supported Features

- IdP-initiated SSO
- SP-initiated SSO

## Procedure

- In Okta, select the Sign On tab for the Flagsmith app, then click Edit.
  - Scroll down to Advanced Sign-on Settings.
  - Enter Base API Url (if using SaaS this should be [https://api.flagsmith.com](https://api.flagsmith.com), otherwise
    it will be your self hosted / private cloud API URL) and SAML Organisation (this should have been provided by
    Flagsmith support)
  - Click Save.
- In Okta, on the ‘Sign on’ tab, under ‘SAML Signing Certificates’, click ‘Actions’ -> ‘View IdP Metadata’ on the first
  certificate in the list.
  - **For SaaS customers: **Save this metadata to a file and send it to Flagsmith
    ([support@flagsmith.com](mailto:support@flagsmith.com))
  - **For Self-Hosted customers: **Copy this metadata and paste it into the ‘Idp metadata xml’ field in the Flagsmith
    admin dashboard as per the instructions
    [here](https://docs.flagsmith.com/deployment/authentication#saml---enterprise-on-premise).
- Once Flagsmith support have confirmed that the metadata has been uploaded, you should now be able to sign in via the
  Okta applications dashboard and the Flagsmith dashboard (by entering the organisation name given to you by Flagsmith
  support).

## Troubleshooting & Tips

- If your users are unable to sign in to the Flagsmith application via Okta, it’s important to check if they already
  have a user account in Flagsmith with their Okta email address. If they do, make sure that they are not a member of
  any other organisations than the one set up in the Okta integration.
