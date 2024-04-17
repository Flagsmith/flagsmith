---
title: LDAP
---

import Tabs from '@theme/Tabs'; import TabItem from '@theme/TabItem';

:::tip

LDAP authentication requires a self-hosted [Enterprise subscription](https://flagsmith.com/pricing).

:::

Flagsmith can be configured to use LDAP for authentication with [environment variables](#backend-environment-variables).
When enabled, it works by authenticating the user with username and password using the ldap server, fetching the user
details from the LDAP server (if the authentication was successful) and creating the user in the Django database.

## Using Microsoft Active Directory

By default, Flagsmith supports logging in via OpenLDAP. To connect to a Microsoft Active Directory, you need to modify
the following environment variables.

For simple usernames (e.g. "username"):

```txt
LDAP_AUTH_FORMAT_USERNAME="django_python3_ldap.utils.format_username_active_directory"
```

For down-level login name formats (e.g. "DOMAIN\username"):

```txt
LDAP_AUTH_FORMAT_USERNAME="django_python3_ldap.utils.format_username_active_directory"
LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN="DOMAIN"
```

For user-principal-name formats (e.g. "user@domain.com"):

```txt
LDAP_AUTH_FORMAT_USERNAME="django_python3_ldap.utils.format_username_active_directory_principal"
LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN="domain.com"
```

Depending on how your Active Directory server is configured, the following additional settings may match your server
better than the defaults used by django-python3-ldap:

```txt
LDAP_AUTH_USER_FIELDS=username=sAMAccountName,email=mail,first_name=givenName,last_name=sn
LDAP_AUTH_OBJECT_CLASS="user"
```

## Sync LDAP groups

You can synchronise Flagsmith users and groups with your LDAP (Directory) users and groups by running the following
command:

```bash
python manage.py sync_ldap_users_and_groups
```

Running this command will:

- Remove users from Flagsmith if they have been removed from Directory
- Remove groups from Flagsmith if they have been removed from Directory
- Remove users from group if they no longer belong to that group in Directory
- Add users to group if they belong to a new group in Directory

:::note Before running this command, please make sure to set the following environment variables:

- LDAP_SYNC_USER_USERNAME
- LDAP_SYNC_USER_PASSWORD
- LDAP_SYNCED_GROUPS
- LDAP_AUTH_SYNC_USER_RELATIONS
- LDAP_DEFAULT_FLAGSMITH_ORGANISATION_ID

:::

## Backend environment variables

Note that some environment variables may be different depending on the image that you are using
(`flagsmith/flagsmith-api-ee` or `flagsmith/flagsmith-private-cloud`). Please select the correct tab below to ensure you
are using the correct environment variables.

<Tabs groupId="ImageType">
<TabItem value="ee" label="flagsmith-api-ee">

| Variable                                   | Example Value                                                                                            | Description                                                                                                                                                                                                                                                                                                                                          | Default Value                                              |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| **LDAP_AUTH_URL**                          | ldap://localhost:389                                                                                     | The URL of the LDAP server                                                                                                                                                                                                                                                                                                                           | None                                                       |
| **LDAP_AUTH_USE_TLS**                      | False                                                                                                    | Setting this to true will initiate TLS on connection                                                                                                                                                                                                                                                                                                 | False                                                      |
| **LDAP_AUTH_SEARCH_BASE**                  | ou=people,dc=example,dc=com                                                                              | The LDAP search base for looking up users                                                                                                                                                                                                                                                                                                            | ou=people,dc=example,dc=com                                |
| **LDAP_AUTH_OBJECT_CLASS**                 | inetOrgPerson                                                                                            | The LDAP class that represents a user                                                                                                                                                                                                                                                                                                                | inetOrgPerson                                              |
| **LDAP_AUTH_USER_FIELDS**                  | username=uid,email=email                                                                                 | User model fields mapped to the LDAP attributes that represent them.                                                                                                                                                                                                                                                                                 | username=uid,email=email,first_name=givenName,last_name=sn |
| **LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN**      | DOMAIN                                                                                                   | Sets the login domain for Active Directory users.                                                                                                                                                                                                                                                                                                    | None                                                       |
| **LDAP_AUTH_CONNECT_TIMEOUT**              | 60                                                                                                       | Set connection timeouts (in seconds) on the underlying `ldap3` library.                                                                                                                                                                                                                                                                              | None                                                       |
| **LDAP_AUTH_RECEIVE_TIMEOUT**              | 60                                                                                                       | Set receive timeouts (in seconds) on the underlying `ldap3` library.                                                                                                                                                                                                                                                                                 | None                                                       |
| **LDAP_AUTH_FORMAT_USERNAME**              | django_python3_ldap.<br/>utils.format_username_openldap                                                  | Path to a callable used to format the username to bind to the LDAP server                                                                                                                                                                                                                                                                            | django_python3_ldap.utils.format_username_openldap         |
| **LDAP_DEFAULT_FLAGSMITH_ORGANISATION_ID** | 1                                                                                                        | All newly created users will be added to this originisation                                                                                                                                                                                                                                                                                          | None                                                       |
| **LDAP_AUTH_SYNC_USER_RELATIONS**          | custom_auth.ldap.sync_user_groups                                                                        | Path to a callable used to sync user relations. Note: if you are setting this value to `custom_auth.ldap.sync_user_groups` please make sure `LDAP_DEFAULT_FLAGSMITH_ORGANISATION_ID` is set.                                                                                                                                                         | django_python3_ldap.utils.sync_user_relations              |
| **LDAP_AUTH_FORMAT_SEARCH_FILTERS**        | custom_auth.ldap.login_group_search_filter                                                               | Path to a callable used to add search filters to login to restrict login to a certain group                                                                                                                                                                                                                                                          | django_python3_ldap.utils.format_search_filters            |
| **LDAP_SYNCED_GROUPS**                     | CN=Readers,CN=Roles,CN=webapp01,<br/>dc=admin,dc=com:CN=Marvel,CN=Roles,<br/>CN=webapp01,dc=admin,dc=com | colon(:) seperated list of DN's of ldap group that will be copied over to flagmsith (lazily, i.e: On user login we will create the group(s) and add the current user to the group(s) if the user is a part of them). Note: please make sure to set `LDAP_AUTH_SYNC_USER_RELATIONS` to `custom_auth.ldap.sync_user_groups` in order for this to work. | []                                                         |
| **LDAP_LOGIN_GROUP**                       | CN=Readers,CN=Roles,CN=webapp01,<br/>dc=admin,dc=com                                                     | DN of the user allowed login user group. Note: Please make sure to set `LDAP_AUTH_FORMAT_SEARCH_FILTERS` to `custom_auth.ldap.login_group_search_filter` in order for this to work.                                                                                                                                                                  | None                                                       |
| **LDAP_SYNC_USER_USERNAME**                | john                                                                                                     | Username used by [sync_ldap_users_and_groups](#sync-ldap-groups) in order to connect to the server.                                                                                                                                                                                                                                                  | None                                                       |
| **LDAP_SYNC_USER_PASSWORD**                | password                                                                                                 | Password used by [sync_ldap_users_and_groups](#sync-ldap-groups) in order to connect to the server.                                                                                                                                                                                                                                                  | None                                                       |

</TabItem>
<TabItem value="pc" label="flagsmith-private-cloud">

| Variable                                   | Example Value                                                                                            | Description                                                                                                                                                                                                                                                                                                                                        | Default Value                                              |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| **LDAP_AUTH_URL**                          | ldap://localhost:389                                                                                     | The URL of the LDAP server                                                                                                                                                                                                                                                                                                                         | None                                                       |
| **LDAP_AUTH_USE_TLS**                      | False                                                                                                    | Setting this to true will initiate TLS on connection                                                                                                                                                                                                                                                                                               | False                                                      |
| **LDAP_AUTH_SEARCH_BASE**                  | ou=people,dc=example,dc=com                                                                              | The LDAP search base for looking up users                                                                                                                                                                                                                                                                                                          | ou=people,dc=example,dc=com                                |
| **LDAP_AUTH_OBJECT_CLASS**                 | inetOrgPerson                                                                                            | The LDAP class that represents a user                                                                                                                                                                                                                                                                                                              | inetOrgPerson                                              |
| **LDAP_AUTH_USER_FIELDS**                  | username=uid,email=email                                                                                 | User model fields mapped to the LDAP attributes that represent them.                                                                                                                                                                                                                                                                               | username=uid,email=email,first_name=givenName,last_name=sn |
| **LDAP_AUTH_ACTIVE_DIRECTORY_DOMAIN**      | DOMAIN                                                                                                   | Sets the login domain for Active Directory users.                                                                                                                                                                                                                                                                                                  | None                                                       |
| **LDAP_AUTH_CONNECT_TIMEOUT**              | 60                                                                                                       | Set connection timeouts (in seconds) on the underlying `ldap3` library.                                                                                                                                                                                                                                                                            | None                                                       |
| **LDAP_AUTH_RECEIVE_TIMEOUT**              | 60                                                                                                       | Set receive timeouts (in seconds) on the underlying `ldap3` library.                                                                                                                                                                                                                                                                               | None                                                       |
| **LDAP_AUTH_FORMAT_USERNAME**              | django_python3_ldap.<br/>utils.format_username_openldap                                                  | Path to a callable used to format the username to bind to the LDAP server                                                                                                                                                                                                                                                                          | django_python3_ldap.utils.format_username_openldap         |
| **LDAP_DEFAULT_FLAGSMITH_ORGANISATION_ID** | 1                                                                                                        | All newly created users will be added to this originisation                                                                                                                                                                                                                                                                                        | None                                                       |
| **LDAP_AUTH_SYNC_USER_RELATIONS**          | flagsmith_ldap.ldap.sync_user_groups                                                                     | Path to a callable used to sync user relations. Note: if you are setting this value to `flagsmith_ldap.ldap.sync_user_groups` please make sure `LDAP_DEFAULT_FLAGSMITH_ORGANISATION_ID` is set.                                                                                                                                                    | django_python3_ldap.utils.sync_user_relations              |
| **LDAP_AUTH_FORMAT_SEARCH_FILTERS**        | flagsmith_ldap.ldap.login_group_search_filter                                                            | Path to a callable used to add search filters to login to restrict login to a certain group                                                                                                                                                                                                                                                        | django_python3_ldap.utils.format_search_filters            |
| **LDAP_SYNCED_GROUPS**                     | CN=Readers,CN=Roles,CN=webapp01,<br/>dc=admin,dc=com:CN=Marvel,CN=Roles,<br/>CN=webapp01,dc=admin,dc=com | colon(:) seperated list of DN's of ldap group that will be copied over to flagmsith (lazily, i.e: On user login we will create the group(s) and add the current user to the group(s) if the user is a part of them). Note: please make sure to set `LDAP_AUTH_SYNC_USER_RELATIONS` to `flagsmith.ldap.sync_user_groups` in order for this to work. | []                                                         |
| **LDAP_LOGIN_GROUP**                       | CN=Readers,CN=Roles,CN=webapp01,<br/>dc=admin,dc=com                                                     | DN of the user allowed login user group. Note: Please make sure to set `LDAP_AUTH_FORMAT_SEARCH_FILTERS` to `flagsmith_ldap.ldap.login_group_search_filter` in order for this to work.                                                                                                                                                             | None                                                       |
| **LDAP_SYNC_USER_USERNAME**                | john                                                                                                     | Username used by [sync_ldap_users_and_groups](#sync-ldap-groups) in order to connect to the server.                                                                                                                                                                                                                                                | None                                                       |
| **LDAP_SYNC_USER_PASSWORD**                | password                                                                                                 | Password used by [sync_ldap_users_and_groups](#sync-ldap-groups) in order to connect to the server.                                                                                                                                                                                                                                                | None                                                       |

</TabItem>
</Tabs>
