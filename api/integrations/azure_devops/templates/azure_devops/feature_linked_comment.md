{% autoescape off %}🔗 Linked to Flagsmith feature flag `{{ feature_name }}`

| Environment | Enabled | Value |
| :--- | :----- | :------ |
{% for env in environment_states %}| [{{ env.name }}]({{ env.url }}) | {% if env.enabled %}✅ Enabled{% else %}❌ Disabled{% endif %} | {% if env.value is not None %}`{{ env.value }}`{% endif %} |
{% endfor %}
Segment and identity overrides may apply — check each environment above for details.{% endautoescape %}
