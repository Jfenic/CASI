def merge_settings(defaults, overrides):
    result = defaults.copy()
    result.update(overrides)
    return result
