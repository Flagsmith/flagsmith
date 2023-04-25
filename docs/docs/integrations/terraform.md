---
title: Terraform Provider
sidebar_label: Terraform
hide_title: true
---

![Terraform](/img/integrations/terraform/terraform-logo.svg)

You can integrate Flagsmith with Terraform. Use our
[Terraform provider](https://registry.terraform.io/providers/Flagsmith/flagsmith) to drive flag management as part of
your Infrastructure as Code tooling.

:::tip

You can find the latest Hashicorp docs for using the Flagsmith provider
[here](https://registry.terraform.io/providers/Flagsmith/flagsmith/latest/docs).

:::

:::tip

Some API actions require object UUIDs/IDs to be referenced. You can enable the [JSON View](../clients/rest.md#json-view)
from your account settings page which will help you access these variables.

:::

## Prerequisite

### [Terraform API Key](../advanced-use/system-administration.md#terraform-api-keys-for-organisations):

In order to configure the Flagsmith Terraform provider we are going to need an API key. To generate that head over to
the Organisation Settings page, and click on `Create Terraform API Key`.

:::info

Organisation Administrator permission is required to generate Terraform API Key.

:::

## Using the Flagsmith Terraform Provider

Once you have the Terraform Provider key you can go ahead and create a Terraform config file, which will look something
like this:

```hcl
terraform {
  required_providers {
    flagsmith = {
      source = "Flagsmith/flagsmith"
      version = "0.3.0" # or whatever the latest version is
    }
  }
}

provider "flagsmith" {
  # or omit this for master_api_key to be read from environment variable
  master_api_key = "<Your Terraform API Key>"
}

# the feature that you want to manage
resource "flagsmith_feature" "new_standard_feature" {
  feature_name = "new_standard_feature"
  project_uuid = "10421b1f-5f29-4da9-abe2-30f88c07c9e8"
  description  = "This is a new standard feature"
  type         = "STANDARD"
}

```

Now, to create the feature all you have to do is run `terraform apply`.

```bash
Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # flagsmith_feature.new_standard_feature will be created
  + resource "flagsmith_feature" "new_standard_feature" {
      + default_enabled = (known after apply)
      + description     = "This is a new standard feature"
      + feature_name    = "new_standard_feature"
      + id              = (known after apply)
      + initial_value   = (known after apply)
      + is_archived     = (known after apply)
      + project_id      = (known after apply)
      + project_uuid    = "10421b1f-5f29-4da9-abe2-30f88c07c9e8"
      + type            = "STANDARD"
      + uuid            = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

flagsmith_feature.new_standard_feature: Creating...
flagsmith_feature.new_standard_feature: Creation complete after 2s

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

Next, let's say you want to update the description of the feature:

```hcl
# the feature that you want to manage
resource "flagsmith_feature" "new_standard_feature" {
  feature_name = "new_standard_feature"
  project_uuid = "10421b1f-5f29-4da9-abe2-30f88c07c9e8"
  description  = "New description"
  type         = "STANDARD"
}
```

Now, to apply the changes just run `terraform apply`:

```bash
Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  ~ update in-place

Terraform will perform the following actions:

  # flagsmith_feature.new_standard_feature will be updated in-place
  ~ resource "flagsmith_feature" "new_standard_feature" {
      ~ description     = "This is a new standard feature" -> "New description"
        id              = 574
        # (7 unchanged attributes hidden)
    }

Plan: 0 to add, 1 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

flagsmith_feature.new_standard_feature: Modifying...
flagsmith_feature.new_standard_feature: Modifications complete after 1s

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
```

To bring an existing Flagsmith feature into Terraform (and start tracking it's state) you can go ahead and
[import](https://registry.terraform.io/providers/Flagsmith/flagsmith/latest/docs/resources/feature#import) it.
