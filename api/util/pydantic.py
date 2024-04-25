from pydantic import BaseModel, create_model


def exclude_model_fields(
    model_cls: type[BaseModel],
    *exclude_fields: str,
) -> type[BaseModel]:
    """
    Create a copy of a model class without the fields
    specified in `exclude_fields`.
    """
    fields = {
        field_name: (field.annotation, field)
        for field_name, field in model_cls.model_fields.items()
        if field_name not in exclude_fields
    }
    return create_model(
        model_cls.__name__,
        __config__=model_cls.model_config,
        **fields,
    )
