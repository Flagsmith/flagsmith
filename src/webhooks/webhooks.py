import requests
import json
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.serializers.json import DjangoJSONEncoder
from django.template.loader import get_template


def call_webhook(environment, data):
    try:
        headers = {'content-type': 'application/json'}
        jsonData = json.dumps(
                data,
                sort_keys=True,
                indent=2,
                cls=DjangoJSONEncoder
            )
        res = requests.post(str(environment.webhook_url), data= jsonData, headers= headers)
    except requests.exceptions.ConnectionError:
        send_failure_email(environment, data, None)
        return

    if res.status_code != 200:
        send_failure_email(environment, data, res.status_code)


def send_failure_email(environment, data, status_code):
        template_data = {
            "project_name": environment.project.name,
            "environment_name": environment.name,
            "status_code": status_code,
            "data": json.dumps(
                data,
                sort_keys=True,
                indent=2,
                cls=DjangoJSONEncoder
            )
        }

        text_template = get_template('features/webhook_failure.txt')
        text_content = text_template.render(template_data)
        subject = "Bullet Train Webhook Failure"
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.EMAIL_CONFIGURATION.get('INVITE_FROM_EMAIL'),
            [environment.project.organisation.webhook_notification_email]
        )
        msg.content_subtype = "plain"
        msg.send()
