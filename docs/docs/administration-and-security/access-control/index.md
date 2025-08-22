---
title: Authentication
description: Customise how your users log in to the Flagsmith dashboard
sidebar_label: Overview
sidebar_position: 1
---

Flagsmith supports a variety of authentication methods for logging into the dashboard:

## Supported in all versions

- Email and password
- GitHub
- Google

## Two-factor authentication (2FA)

Two-factor authentication requires a [Start-Up or Enterprise subscription](https://flagsmith.com/pricing).

## Enterprise single sign-on (SSO)

Using the following authentication methods requires an [Enterprise subscription](https://flagsmith.com/pricing):

- [SAML](/administration-and-security/access-control/saml)
- [Active Directory (LDAP)](/administration-and-security/access-control/ldap)
- [Microsoft ADFS](/administration-and-security/access-control/adfs)

Please get in touch in order to integrate with LDAP or ADFS.

## Enforcing authentication methods per email domain {#domain-auth}

You can force users with specific email domains to always use certain authentication methods when they log in to any
Flagsmith organisation.

If you are using Flagsmith SaaS or private cloud, contact Flagsmith support. Make sure to mention which email domain(s)
and authentication methods you want to allow for your users, and when would be a convenient time to enforce these
restrictions.

If you are self-hosting Flagsmith, you can restrict authentication methods per email domain from
[Django Admin](/deployment/configuration/django-admin):

1. On the Django Admin sidebar, click on "Domain auth methods".
2. Click "Add domain auth methods".
3. Enter the email domain that these restrictions should apply to, such as `example.com`.
4. Select the authentication methods to allow for this email domain.
5. Click "Save".

## Disabling password authentication {#disable-password}

If you are self-hosting Flagsmith, you can disable password authentication by setting the `PREVENT_EMAIL_PASSWORD` 
environment variable on the Flagsmith API. This will also hide the username and password fields from the login screen.
Note that this does not disable password authentication for
[Django Admin](/deployment/configuration/django-admin#email-and-password).

If you have a private cloud Flagsmith instance, contact Flagsmith support to disable password authentication once 
you have successfully set up an alternative authentication method.
