---
title: "Email Setup"
description: "How to configure Flagsmith to send emails using SMTP or SendGrid."
sidebar_position: 30
---

:::note

You can self-host Flagsmith without setting up an email server/gateway. You can invite additional users to the platform using invitation links, and the platform will run fine without email.

:::

:::tip

Flagsmith makes use of the `django_site` table to provide the domain name for email template links. You will need to configure the record in this table to point to your domain for email links to work.

:::

## Required Environment Variables

- `SENDER_EMAIL`: Email address from which emails are sent
- `EMAIL_BACKEND`: One of:
  - `django.core.mail.backends.smtp.EmailBackend`
  - `sgbackend.SendGridBackend`
  - `django_ses.SESBackend`

## SMTP Configuration

If using `django.core.mail.backends.smtp.EmailBackend`, you will need to configure:

- `EMAIL_HOST` = env("EMAIL_HOST", default='localhost')
- `EMAIL_HOST_USER` = env("EMAIL_HOST_USER", default=None)
- `EMAIL_HOST_PASSWORD` = env("EMAIL_HOST_PASSWORD", default=None)
- `EMAIL_PORT` = env("EMAIL_PORT", default=587)
- `EMAIL_USE_TLS` = env.bool("EMAIL_USE_TLS", default=True)

## SendGrid Configuration

If using `sgbackend.SendGridBackend`, you will need to configure:

- `SENDGRID_API_KEY`: API key for the SendGrid account

## AWS SES Configuration

If using AWS SES, you will need to configure:

- `AWS_SES_REGION_NAME`: If using Amazon SES as the email provider, specify the region (e.g. eu-central-1) that contains your verified sender email address. Defaults to us-east-1
- `AWS_SES_REGION_ENDPOINT`: SES region endpoint, e.g. email.eu-central-1.amazonaws.com. Required when using SES.
- `AWS_ACCESS_KEY_ID`: If using Amazon SES, these form part of your SES credentials.
- `AWS_SECRET_ACCESS_KEY`: If using Amazon SES, these form part of your SES credentials. 