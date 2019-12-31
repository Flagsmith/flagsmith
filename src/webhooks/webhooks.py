import json

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.serializers.json import DjangoJSONEncoder
from django.template.loader import get_template


def call_webhooks(environment, data):
    for webhook in environment.webhooks.filter(enabled=True):
        try:
            headers = {'content-type': 'application/json'}
            json_data = json.dumps(
                data,
                sort_keys=True,
                cls=DjangoJSONEncoder
            )
            res = requests.post(str(webhook.url), data=json_data, headers=headers)
        except requests.exceptions.ConnectionError:
            send_failure_email(webhook, data)
            continue

        if res.status_code != 200:
            send_failure_email(webhook, data, res.status_code)


def send_failure_email(webhook, data, status_code=None):
    template_data = {
        "project_name": webhook.environment.project.name,
        "environment_name": webhook.environment.name,
        "status_code": status_code,
        "data": json.dumps(
            data,
            sort_keys=True,
            indent=2,
            cls=DjangoJSONEncoder
        ),
        "webhook_url": webhook.url
    }

    text_template = get_template('features/webhook_failure.txt')
    text_content = text_template.render(template_data)
    subject = "Bullet Train Webhook Failure"
    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.EMAIL_CONFIGURATION.get('INVITE_FROM_EMAIL'),
        [webhook.environment.project.organisation.webhook_notification_email]
    )
    msg.content_subtype = "plain"
    msg.send()
