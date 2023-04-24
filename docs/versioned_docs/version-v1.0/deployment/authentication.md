---
title: Authentication
sidebar_label: Authentication
sidebar_position: 78
---

## SAML

To allow an Organisation on the Flagsmith platform to login using SAML authentication, you'll need to access the admin
interface. Instructions on how to access the admin interface can be found
[here](https://docs.flagsmith.com/deployment/configuration/django-admin).

Once you've logged into the django admin interface, you'll need to click on the 'Saml Configurations' option in the menu
on the left. From here, you should see a list of existing SAML configuration entities. To create a new one, click on the
'ADD SAML CONFIGURATION' button in the top right corner of the screen.

You should see a screen similar to the following.

![SAML Auth Setup](/img/saml-auth-setup.png)

From the drop down next to **Organisation**, select the organisation in the Flagsmith platform that you want to
configure for SAML authentication.

Next to **Organisation name**, add a name without any spaces that identifies the organisation uniquely for the
installation of Flagsmith you're working on. This is what users will provide when authenticating with SAML so that the
platform knows where to redirect them.

Next to **Frontend url**, add in the URL at which your Frontend application is running. This is where users will be
redirected to on a successful SAML authentication.

For now, we'll leave **Idp metadata xml** empty.

Once you've completed these fields, hit the **Save** button to create the SAML configuration.

Now, we need to grab the Flagsmith service provider metadata to configure the integration on your IDP. To do this, open
a new browser tab and head to [https://api.flagsmith.com/api/v1/auth/saml/\<organisation
name\>/metadata/](https://api.flagsmith.com/api/v1/auth/saml/\<organisation name\>/metadata/) where _\<organisation
name\>_ is the name you provided above. From here, copy and paste what you see in the web page into a new text file and
save that file as `flagsmith-sp-metadata.xml` or similar.

Note: do not use 'save page as' from your browser as this will likely result in the metadata being incorrect and the
integration will not work.

Now you can use this XML metadata to create the integration on your IDP. Once created on the IDP, you can add the IDP
metadata into the **Idp metadata xml** field that we left blank earlier.
