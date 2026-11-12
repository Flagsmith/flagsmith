---
sidebar_label: Upgrades and Rollbacks
title: Upgrades and Rollbacks
sidebar_position: 2
---

# Rolling Back to a Previous Version of Flagsmith

:::warning

These steps may result in data loss in the scenario where new models or fields have been added to the database. We recommend taking a full backup of the database before completing the rollback.

:::

This page covers the process of rolling back to a previous version of Flagsmith. If you need to roll back to a previous version, you will need to ensure that the database is also rolled back to the correct state. In order to do this, you will need to unapply all the migrations that happened between the version that you want to roll back to and the one that you are rolling back from. The following steps explain how to do that.

## Steps for v2.151.0 and Later

1. Identify the date and time that you deployed the version that you want to roll back to.

:::tip

If you are unsure about when you completed the previous deployment, you can use the `django_migrations` table as a guide. If you query the table using the following query, you should see the migrations that have been applied (in descending order), grouped in batches corresponding to each deployment.

```sql
SELECT *
FROM django_migrations
ORDER BY applied DESC
```

:::

2. Run the rollback command inside a Flagsmith API container running the _current_ version of Flagsmith:

```bash
python manage.py rollbackmigrationsafter "<datetime from step 1>"
```

3. Roll back the Flagsmith API to the desired version.

## Steps for Versions Earlier Than v2.151.0

If you are rolling back from a version earlier than v2.151.0, you will need to replace step 2 above with the following two steps.

### Step 1: Generate Rollback Commands

Replace the datetime in the query below with a datetime after the deployment of the version you want to roll back to, and before any subsequent deployments. Execute the subsequent query against the Flagsmith database.

```sql {14} showLineNumbers
select
    concat('python manage.py migrate ',
    app,
    ' ',
    case
        when substring(name, 1, 4)::integer = 1 then 'zero'
        else lpad((substring(name, 1, 4)::integer - 1)::text, 4, '0')
        end
    ) as "python_commands"
from django_migrations
where id in (
    select min(id)
    from django_migrations
    where applied >= 'yyyy-MM-dd HH:mm:ss'
    group by app
);
```

Example output:

```
                python_commands
-----------------------------------------------
 python manage.py migrate multivariate 0007
 python manage.py migrate segment 0004
 python manage.py migrate environments 0034
 python manage.py migrate features 0064
 python manage.py migrate token_blacklist zero
```

### Step 2: Execute the Rollback Commands

Run the generated commands inside a Flagsmith API container running the _current_ version of Flagsmith.
