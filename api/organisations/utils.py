def dict_to_class(dictionary):
    if isinstance(dictionary, dict):
        obj = type("Object", (object,), {})
        for key, value in dictionary.items():
            if isinstance(value, dict):
                setattr(obj, key, dict_to_class(value))
            elif isinstance(value, list):
                setattr(
                    obj,
                    key,
                    [
                        dict_to_class(item) if isinstance(item, dict) else item
                        for item in value
                    ],
                )
            else:
                setattr(obj, key, value)
        return obj
    else:
        return dictionary
