"""Create or resume the First Minute experiment on a local Flagsmith instance."""

import argparse
import getpass
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000/api/v1/"


class RateLimited(SystemExit):
    def __init__(self, retry_after):
        self.seconds = (
            max(1, int(retry_after)) if retry_after and retry_after.isdigit() else 300
        )
        super().__init__(
            f"Flagsmith rate limit reached. Retry after {self.seconds} seconds."
        )


def request(path, data=None, *, method=None):
    url = urljoin(BASE, path)
    if urlsplit(url).netloc != urlsplit(BASE).netloc:
        raise ValueError("Unexpected pagination host")
    headers = {"Content-Type": "application/json"}
    if path != "auth/login/":
        headers["Authorization"] = "Token " + os.environ["FLAGSMITH_MANAGEMENT_TOKEN"]
    req = Request(
        url,
        headers=headers,
        data=None if data is None else json.dumps(data).encode(),
        method=method,
    )
    try:
        with urlopen(req, timeout=20) as response:
            return json.loads(response.read() or b"null")
    except HTTPError as error:
        if error.code == 429:
            raise RateLimited(error.headers.get("Retry-After")) from error
        if path == "auth/login/":
            raise SystemExit(
                f"Local Flagsmith sign-in returned HTTP {error.code}. Check the account in the local dashboard."
            ) from error
        raise SystemExit(
            f"Flagsmith returned HTTP {error.code} for {req.get_method()} {urlsplit(path).path.rsplit('/', 2)[-2]}. Check management permissions and experiment configuration."
        ) from error
    except (URLError, TimeoutError) as error:
        raise SystemExit(
            "Could not reach local Flagsmith at http://127.0.0.1:8000/. Check that Docker Compose is running."
        ) from error


def records(path):
    while path:
        page = request(path)
        if isinstance(page, list):
            yield from page
            return
        yield from page["results"]
        path = page.get("next")


def local_organisation(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "organisation_id", type=int, nargs="?", help="local Flagsmith organisation ID"
    )
    org_id = parser.parse_args().organisation_id
    if not os.environ.get("FLAGSMITH_MANAGEMENT_TOKEN"):
        if not sys.stdin.isatty():
            parser.error(
                "Set FLAGSMITH_MANAGEMENT_TOKEN or run in a terminal to sign in to local Flagsmith."
            )
        print("Local Flagsmith email: ", file=sys.stderr, end="", flush=True)
        email = input().strip()
        password = getpass.getpass("Local Flagsmith password: ")
        response = request("auth/login/", {"email": email, "password": password})
        if not isinstance(response, dict) or not response.get("key"):
            parser.error(
                "Sign in to local Flagsmith and supply your user token in FLAGSMITH_MANAGEMENT_TOKEN."
            )
        os.environ["FLAGSMITH_MANAGEMENT_TOKEN"] = response["key"]
    if org_id is not None:
        return org_id
    organisations = list(records("organisations/"))
    if len(organisations) == 1:
        return organisations[0]["id"]
    if not organisations:
        parser.error("Create an organisation in the local Flagsmith dashboard first.")
    choices = ", ".join(f"{org['id']} ({org['name']})" for org in organisations)
    parser.error(
        f"Pass the organisation ID to use. Available organisations: {choices}."
    )


def ensure(path, body, match):
    found = [item for item in records(path) if match(item)]
    if len(found) > 1:
        raise SystemExit("Multiple matching resources found. Check the dashboard.")
    return found[0] if found else request(path, body)


def check_rollout(experiment, guided_id):
    rollout = experiment.get("experiment_rollout") or {}
    weights = {
        item["multivariate_feature_option"]: item["percentage_allocation"]
        for item in rollout.get("multivariate_feature_state_values", [])
        if item["percentage_allocation"]
    }
    if weights != {guided_id: 50} or rollout.get("feature_state_value") != {
        "type": "string",
        "value": "control",
    }:
        raise SystemExit(
            "The existing experiment must allocate 50% to guided and 50% to control. Check its rollout before continuing."
        )


def check_enrolment(experiment):
    rollout = experiment.get("experiment_rollout") or {}
    if (
        not rollout.get("enabled")
        or rollout.get("rollout_percentage") != 100
        or (rollout.get("audience") or {}).get("segments")
    ):
        raise SystemExit(
            "The drill needs an enabled rollout for 100% of identities with no audience restriction. Check enrolment in Flagsmith."
        )


def prepare_experiment(org_id, environment_name, *, resume_paused=False):
    project_name = "First Minute"
    project = ensure(
        "projects/",
        {"name": project_name, "organisation": org_id},
        lambda p: p["name"] == project_name and p["organisation"] == org_id,
    )
    pid = project["id"]
    env = ensure(
        f"environments/?project={pid}",
        {"name": environment_name, "project": pid},
        lambda e: e["name"] == environment_name and e["project"] == pid,
    )
    root = f"environments/{env['api_key']}/"
    warehouse_path = root + "warehouse-connections/"
    warehouse = next(iter(records(warehouse_path)), None)
    if not warehouse:
        warehouse = request(
            warehouse_path,
            {"warehouse_type": "postgres", "config": {"source": "flagsmith_database"}},
        )
    if warehouse["status"] != "connected":
        raise SystemExit(
            "Connect the experiment warehouse in Flagsmith before continuing."
        )

    flag_path = f"projects/{pid}/features/"
    flag = ensure(
        flag_path,
        {
            "name": "triage_guide",
            "type": "MULTIVARIATE",
            "project": pid,
            "default_enabled": True,
            "initial_value": "control",
        },
        lambda f: f["name"] == "triage_guide",
    )
    if flag["type"] != "MULTIVARIATE":
        raise SystemExit(
            "The existing triage_guide feature must be a multivariate flag."
        )
    variants = flag_path + str(flag["id"]) + "/mv-options/"
    variant = ensure(
        variants,
        {
            "feature": flag["id"],
            "type": "unicode",
            "string_value": "guided",
            "key": "guided",
            "default_percentage_allocation": 0,
        },
        lambda v: v["key"] == "guided",
    )
    if variant["string_value"] != "guided":
        raise SystemExit(
            "The existing guided variation must serve the string 'guided'."
        )
    name = "First attempt resolved within 60 seconds"
    metric = ensure(
        root + "experiment-metrics/",
        {
            "name": name,
            "direction": "up",
            "aggregation": "occurrence",
            "definition": {"version": 1, "event": "drill_resolved"},
        },
        lambda m: m["name"] == name,
    )
    if (
        metric["aggregation"] != "occurrence"
        or metric["direction"] != "up"
        or metric["definition"].get("event") != "drill_resolved"
    ):
        raise SystemExit(
            "The existing first-attempt metric must count occurrences of drill_resolved with upward direction."
        )
    name = "Can a runbook help on-call responders?"
    path = root + "experiments/"
    experiment = ensure(
        path,
        {
            "name": name,
            "feature": flag["id"],
            "hypothesis": "A three-step runbook increases first-attempt correct diagnoses within 60 seconds.",
            "metrics": [{"metric": metric["id"], "expected_direction": "increase"}],
            "experiment_rollout": {
                "enabled": True,
                "rollout_percentage": 100,
                "feature_state_value": {"type": "string", "value": "control"},
                "multivariate_feature_state_values": [
                    {
                        "multivariate_feature_option": variant["id"],
                        "percentage_allocation": 50,
                    }
                ],
            },
        },
        lambda e: e["name"] == name,
    )
    detail = path + str(experiment["id"]) + "/"
    experiment = request(detail)
    if experiment["feature"]["id"] != flag["id"] or not any(
        m["metric"] == metric["id"] for m in experiment["metrics"]
    ):
        raise SystemExit(
            "The existing experiment uses a different flag or metric. Check the experiment in Flagsmith."
        )
    check_rollout(experiment, variant["id"])
    should_start = experiment["status"] == "created" or (
        resume_paused and experiment["status"] == "paused"
    )
    if should_start or experiment["status"] == "running":
        check_enrolment(experiment)
    if should_start:
        request(detail + "start/", {})
    return env, metric, variant, detail


def setup(org_id):
    env, _, _, detail = prepare_experiment(
        org_id, "Participant drill", resume_paused=True
    )
    experiment = request(detail)
    if experiment["status"] != "running":
        raise SystemExit(
            "The experiment is not running. Check its status in the dashboard."
        )
    check_enrolment(experiment)
    print("Participant experiment is running.", file=sys.stderr)
    # Only the client-side environment key belongs in a browser configuration.
    print("VITE_FLAGSMITH_ENVIRONMENT_ID=" + env["api_key"])
    print(
        "VITE_FLAGSMITH_DASHBOARD_URL=http://localhost:8000/project/{}/environment/{}/experiments/{}".format(
            env["project"], env["api_key"], experiment["id"]
        )
    )


if __name__ == "__main__":
    setup(local_organisation(__doc__))
