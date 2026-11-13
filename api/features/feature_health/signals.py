from django.dispatch import Signal

# Sent when a feature's health changes in an environment.
# Arguments:
#   - `feature`: the `Feature` whose health changed.
#   - `environment`: the `Environment` the change applies to, or `None`
#     if the health event was not tied to an environment.
feature_health_updated = Signal()
