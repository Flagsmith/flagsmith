---
title: "Enterprise Licence"
description: "How to upload and manage your Enterprise licence in a self-hosted Flagsmith deployment."
sidebar_position: 35
---

Enterprise Edition deployments require a valid licence to activate seat and project limits for your organisation. Your Flagsmith account team will provide you with two files:

- **Licence file** — contains your organisation's licence details (seats, projects, expiry)
- **Signature file** — a cryptographic signature used to verify the licence

## Prerequisites

- A running [Enterprise Edition](/deployment-self-hosting/enterprise-edition) deployment
- Organisation admin access
- Both licence and signature files from your Flagsmith account team

## Uploading via the Dashboard

1. Log in to your Flagsmith dashboard as an organisation admin.
2. Navigate to **Organisation Settings**.
3. Select the **Licensing** tab.
4. Click **Select Licence File** and choose your licence file.
5. Click **Select Signature File** and choose your signature file.
6. Click **Upload Licensing Files**.

A success notification confirms the licence has been applied. Your organisation's seat and project limits will be updated immediately.

## Uploading via the API

You can also upload the licence programmatically using the REST API. This is useful for automated deployments or infrastructure-as-code workflows.

```bash
curl -X PUT \
  https://<your-flagsmith-host>/api/v1/organisations/<organisation_id>/licence \
  -H "Authorization: Token <api_token>" \
  -F "licence=@/path/to/licence-file" \
  -F "licence_signature=@/path/to/signature-file"
```

Replace:

- `<your-flagsmith-host>` with your Flagsmith API domain
- `<organisation_id>` with your organisation ID
- `<api_token>` with a valid API token for an organisation admin
- The file paths with the actual paths to your licence and signature files

## Troubleshooting

| Symptom | Cause | Resolution |
| --- | --- | --- |
| "No licence file provided" | The licence file was not included in the upload | Select a licence file before clicking Upload. |
| "No licence signature file provided" | The signature file was not included in the upload | Select a signature file before clicking Upload. |
| "Signature failed for licence" | The signature does not match the licence file | Ensure you are using the correct pair of files provided by your Flagsmith account team. Contact support if the issue persists. |
| Licensing tab not visible | Deployment is not running the Enterprise Edition image | The licensing tab only appears on Enterprise Edition deployments. See [Enterprise Edition](/deployment-self-hosting/enterprise-edition) for setup instructions. |
| "You do not have permission to view this page" on Organisation Settings | Insufficient access | Only organisation admins can access Organisation Settings and upload licence files. Check your role with an existing admin. |
