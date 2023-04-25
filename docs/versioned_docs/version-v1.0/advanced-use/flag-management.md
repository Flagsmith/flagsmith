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
finished with a flag, but you cant remove it as there are still some older versions of your app out there that depend on
that flag. Archiving the flag helps to keep your main list of flags under control.

## Flag Owners

You can specify members of your team as owners of individual Flags. This helps in larger teams when you need to identify
who is responsible for a particular flag.

<img width="75%" src="/img/flag-owners.png"/>
