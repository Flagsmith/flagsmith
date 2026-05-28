from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("feature_external_resources", "0003_add_gitlab_resource_types"),
    ]

    operations = [
        migrations.AlterField(
            model_name="featureexternalresource",
            name="type",
            field=models.CharField(
                choices=[
                    ("GITHUB_ISSUE", "GitHub Issue"),
                    ("GITHUB_PR", "GitHub PR"),
                    ("GITLAB_ISSUE", "GitLab Issue"),
                    ("GITLAB_MR", "GitLab MR"),
                    ("AZURE_DEVOPS_PULL_REQUEST", "Azure DevOps Pull Request"),
                    ("AZURE_DEVOPS_WORK_ITEM", "Azure DevOps Work Item"),
                ],
                max_length=30,
            ),
        ),
    ]
