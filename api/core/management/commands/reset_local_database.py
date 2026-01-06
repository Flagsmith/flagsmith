import json
from typing import Any

from django.core.management import BaseCommand, call_command
from django.urls import reverse
from rest_framework.test import APIClient


class Command(BaseCommand):
    help = "Resets and seeds the database with test data for local development"

    def handle(self, *args: Any, **kwargs: Any) -> None:
        self.stdout.write("Flushing database...")
        call_command("flush", "--noinput", verbosity=0)

        self.stdout.write("Running migrations...")
        call_command("migrate", verbosity=0)

        self.stdout.write("Creating cache table...")
        call_command("createcachetable", verbosity=0)

        self.stdout.write("Seeding database with test data...")
        self._seed_database()

    def _seed_database(self) -> None:
        email = "local@flagsmith.com"
        password = "testpass1"

        client = APIClient()

        # Create user via signup API
        signup_url = reverse("api-v1:custom_auth:ffadminuser-list")
        signup_response = client.post(
            signup_url,
            data={
                "email": email,
                "password": password,
                "re_password": password,
                "first_name": "Local",
                "last_name": "Developer",
            },
        )
        auth_token = signup_response.json()["key"]
        client.credentials(HTTP_AUTHORIZATION=f"Token {auth_token}")

        # Create organisation via API (user becomes admin automatically)
        org_name = "Acme, Inc."
        org_url = reverse("api-v1:organisations:organisation-list")
        org_response = client.post(org_url, data={"name": org_name})
        organisation_id = org_response.json()["id"]

        # Create project via API
        project_name = "AI Booster"
        project_url = reverse("api-v1:projects:project-list")
        project_response = client.post(
            project_url,
            data={"name": project_name, "organisation": organisation_id},
        )
        project_id = project_response.json()["id"]

        # Create environments via API
        env_url = reverse("api-v1:environments:environment-list")
        dev_env_response = client.post(
            env_url,
            data={"name": "Development", "project": project_id},
        )
        dev_environment = dev_env_response.json()
        dev_env_id = dev_environment["id"]
        dev_env_api_key = dev_environment["api_key"]

        client.post(
            env_url,
            data={"name": "Staging", "project": project_id},
        )

        client.post(
            env_url,
            data={"name": "Production", "project": project_id},
        )

        # Create features via API
        feature_url = reverse(
            "api-v1:projects:project-features-list", args=[project_id]
        )

        dark_mode_response = client.post(
            feature_url,
            data={
                "name": "dark_mode",
                "description": "Enable dark mode theme for the application",
                "default_enabled": True,
                "type": "FLAG",
            },
        )
        dark_mode_id = dark_mode_response.json()["id"]

        client.post(
            feature_url,
            data={
                "name": "ai_assistant",
                "description": "Enable AI-powered assistant features",
                "default_enabled": False,
                "type": "FLAG",
            },
        )

        api_rate_limit_response = client.post(
            feature_url,
            data={
                "name": "api_rate_limit",
                "description": "Maximum API requests per minute",
                "default_enabled": True,
                "type": "CONFIG",
                "initial_value": "100",
            },
        )
        api_rate_limit_id = api_rate_limit_response.json()["id"]

        welcome_message_response = client.post(
            feature_url,
            data={
                "name": "welcome_message",
                "description": "Welcome message displayed to users",
                "default_enabled": True,
                "type": "CONFIG",
                "initial_value": "Welcome to AI Booster!",
            },
        )
        welcome_message_id = welcome_message_response.json()["id"]

        client.post(
            feature_url,
            data={
                "name": "feature_config",
                "description": "JSON configuration for feature behavior",
                "default_enabled": True,
                "type": "CONFIG",
                "initial_value": '{"theme": "modern", "animations": true}',
            },
        )

        beta_features_response = client.post(
            feature_url,
            data={
                "name": "beta_features",
                "description": "Enable access to beta features",
                "default_enabled": True,
                "type": "FLAG",
            },
        )
        beta_features_id = beta_features_response.json()["id"]

        # Create segments via API
        segment_url = reverse(
            "api-v1:projects:project-segments-list", args=[project_id]
        )

        premium_segment_response = client.post(
            segment_url,
            data=json.dumps(
                {
                    "name": "Premium Users",
                    "description": "Users with premium subscription and active status",
                    "project": project_id,
                    "rules": [
                        {
                            "type": "ALL",
                            "rules": [
                                {
                                    "type": "ANY",
                                    "rules": [],
                                    "conditions": [
                                        {
                                            "property": "subscription_tier",
                                            "operator": "EQUAL",
                                            "value": "premium",
                                        },
                                        {
                                            "property": "account_age",
                                            "operator": "GREATER_THAN_INCLUSIVE",
                                            "value": "30",
                                        },
                                    ],
                                }
                            ],
                            "conditions": [],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        premium_segment_id = premium_segment_response.json()["id"]

        beta_segment_response = client.post(
            segment_url,
            data=json.dumps(
                {
                    "name": "Beta Testers",
                    "description": "Users enrolled in beta testing program",
                    "project": project_id,
                    "rules": [
                        {
                            "type": "ALL",
                            "rules": [],
                            "conditions": [
                                {
                                    "property": "beta_tester",
                                    "operator": "EQUAL",
                                    "value": "true",
                                },
                            ],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )
        beta_segment_id = beta_segment_response.json()["id"]

        client.post(
            segment_url,
            data=json.dumps(
                {
                    "name": "50% Rollout",
                    "description": "50% of users for gradual feature rollout",
                    "project": project_id,
                    "rules": [
                        {
                            "type": "ALL",
                            "rules": [],
                            "conditions": [
                                {
                                    "property": "id",
                                    "operator": "PERCENTAGE_SPLIT",
                                    "value": "50",
                                },
                            ],
                        }
                    ],
                }
            ),
            content_type="application/json",
        )

        # Create feature segments via API
        feature_segment_url = reverse("api-v1:features:feature-segment-list")

        client.post(
            feature_segment_url,
            data=json.dumps(
                {
                    "feature": dark_mode_id,
                    "segment": premium_segment_id,
                    "environment": dev_env_id,
                    "enabled": True,
                }
            ),
            content_type="application/json",
        )

        client.post(
            feature_segment_url,
            data=json.dumps(
                {
                    "feature": beta_features_id,
                    "segment": beta_segment_id,
                    "environment": dev_env_id,
                    "enabled": True,
                }
            ),
            content_type="application/json",
        )

        # Create segment overrides with custom values
        client.post(
            feature_segment_url,
            data=json.dumps(
                {
                    "feature": api_rate_limit_id,
                    "segment": premium_segment_id,
                    "environment": dev_env_id,
                    "enabled": True,
                    "value": "500",
                }
            ),
            content_type="application/json",
        )

        client.post(
            feature_segment_url,
            data=json.dumps(
                {
                    "feature": welcome_message_id,
                    "segment": beta_segment_id,
                    "environment": dev_env_id,
                    "enabled": True,
                    "value": "Welcome, Beta Tester!",
                }
            ),
            content_type="application/json",
        )

        # Create identities via API
        identity_url = reverse(
            "api-v1:environments:environment-identities-list", args=[dev_env_api_key]
        )

        alice_response = client.post(
            identity_url, data={"identifier": "alice@example.com"}
        )
        alice_id = alice_response.json()["id"]

        bob_response = client.post(identity_url, data={"identifier": "bob@example.com"})
        bob_id = bob_response.json()["id"]

        # Create identity overrides via API
        identity_featurestates_url = reverse(
            "api-v1:environments:identity-featurestates-list",
            args=[dev_env_api_key, alice_id],
        )

        # Override dark_mode to false for alice
        client.post(
            identity_featurestates_url,
            data=json.dumps(
                {
                    "feature": dark_mode_id,
                    "enabled": False,
                }
            ),
            content_type="application/json",
        )

        # Override welcome_message for bob
        bob_featurestates_url = reverse(
            "api-v1:environments:identity-featurestates-list",
            args=[dev_env_api_key, bob_id],
        )

        client.post(
            bob_featurestates_url,
            data=json.dumps(
                {
                    "feature": dark_mode_id,
                    "enabled": True,
                }
            ),
            content_type="application/json",
        )

        # Print summary
        self.stdout.write(self.style.SUCCESS("\nDatabase seeded successfully\n"))

        self.stdout.write("Created entities:\n")
        self.stdout.write(f"  Organisation: {org_name}\n")
        self.stdout.write(f"    Project: {project_name}\n")
        self.stdout.write("      Environments (3):\n")
        self.stdout.write("        Development\n")
        self.stdout.write("        Staging\n")
        self.stdout.write("        Production\n")
        self.stdout.write("      Features (6):\n")
        self.stdout.write("        dark_mode (FLAG, enabled)\n")
        self.stdout.write("        ai_assistant (FLAG, disabled)\n")
        self.stdout.write("        api_rate_limit (CONFIG)\n")
        self.stdout.write("        welcome_message (CONFIG)\n")
        self.stdout.write("        feature_config (CONFIG)\n")
        self.stdout.write("        beta_features (FLAG, enabled)\n")
        self.stdout.write("      Segments (3):\n")
        self.stdout.write("        Premium Users (with overrides)\n")
        self.stdout.write("        Beta Testers (with overrides)\n")
        self.stdout.write("        50% Rollout\n")
        self.stdout.write("      Identities (2):\n")
        self.stdout.write("        alice@example.com (with overrides)\n")
        self.stdout.write("        bob@example.com (with overrides)\n")

        self.stdout.write("\nLogin credentials:\n")
        self.stdout.write(f"  Email: {email}\n")
        self.stdout.write(f"  Password: {password}\n")
