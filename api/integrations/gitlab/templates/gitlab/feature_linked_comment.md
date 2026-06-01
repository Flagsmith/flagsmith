{% autoescape off %}:link: Linked to Flagsmith feature flag `{{ feature_name }}`

| Environment | Enabled | Value |
| :--- | :----- | :------ |
{% for env in environment_states %}| [{{ env.name }}]({{ env.url }}) | {% if env.enabled %}:white_check_mark: Enabled{% else %}:x: Disabled{% endif %} | {% if env.value is not None %}`{{ env.value }}`{% endif %} |
{% endfor %}
Segment and identity overrides may apply -- check each environment above for details.{% endautoescape %}
