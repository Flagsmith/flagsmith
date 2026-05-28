from django.apps import apps


def test_azure_devops_app__django_registry__contains_config() -> None:
    # Given
    app_label = "azure_devops"

    # When
    config = apps.get_app_config(app_label)

    # Then
    assert config.name == "integrations.azure_devops"
