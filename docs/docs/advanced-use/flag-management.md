# Flag Management

Managing larger numbers of flags is easy using some of the tools built into Flagsmith.

![Image](/img/flag-settings.png)

## Tagging

You can create tags within Flagsmith and tag Flags in order to organise them. Tags can also be used to filter the list
of Flags in the event that you have a large number.

![Image](/img/flag-tags.png)

## Flag Archiving

You can also archive Flags within Flagsmith. Archived flags will continue to be sent to your SDKs when you get the flags
for your Environment, but by default they are hidden from the main list of flags.

You can set a Flag as Archived from the Flag settings tab.

Archived flags are often used when you have customers running older versions of your mobile app. You may well have
finished with a flag, but you can't remove it as there are still some older versions of your app out there that depend
on that flag. Archiving the flag helps to keep your main list of flags under control.

## Case Sensitive Flags

By default, Flagsmith stores flags with lower case characters in order to minimise human error. If you want to store
flags in a case-sensitive manner you can do this as a Project-wide setting from the Project Settings page.

## Feature Name Regular Expressions

You can enforce feature name String formatting by way of a regular expression in the Project Settings area. If you want
flags to always be lower case, or camel case, or whatever your preference, you can set it here.

## Flag Owners

You can specify members of your team as owners of individual Flags. This helps in larger teams when you need to identify
who is responsible for a particular flag.

<img width="75%" src="/img/flag-owners.png"/>

## Flag Defaults

By default, when you create a feature with a value and enabled state it acts as a default for your other Environments.
In the Project Settings page, you have the option of enabling this setting. It forces the user to create a Feature
before setting its values per Environment.

## Comparing Flags

You can compare Flags both across Environments and for individual Flags.

### Environment Comparison

Use the "Compare" menu item to get an overview of how flag values differ between any two Environments:

![Image](/img/flag-compare-environment.png)

### Flag Comparison

You can also view a the values of a single Flag against all the Environments within the Project:

![Image](/img/flag-compare-flag.png)
