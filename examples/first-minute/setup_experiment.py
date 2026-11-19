"""Create or resume the First Minute experiment on a local Flagsmith instance."""
import json
import os
import sys
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000/api/v1/"


def request(path, data=None):
    url = urljoin(BASE, path)
    if urlsplit(url).netloc != urlsplit(BASE).netloc:
        raise ValueError("Unexpected pagination host")
    req = Request(url, headers={
        "Authorization": "Token " + os.environ["FLAGSMITH_MANAGEMENT_TOKEN"],
        "Content-Type": "application/json",
    }, data=None if data is None else json.dumps(data).encode())
    try:
        with urlopen(req, timeout=20) as response:
            return json.loads(response.read() or b"null")
    except HTTPError as error:
        raise SystemExit(f"Flagsmith returned HTTP {error.code} for {req.get_method()} {urlsplit(path).path.rsplit('/', 2)[-2]}. Check management permissions and experiment configuration.") from error


def records(path):
    while path:
        page = request(path)
        if isinstance(page, list):
            yield from page
            return
        yield from page["results"]
        path = page.get("next")


def ensure(path, body, match):
    found = [item for item in records(path) if match(item)]
    if len(found) > 1:
        raise SystemExit("Multiple matching resources found. Check the dashboard.")
    return found[0] if found else request(path, body)


def setup(org_id):
    project_name = "First Minute"
    project = ensure("projects/", {"name": project_name, "organisation": org_id},
                     lambda p: p["name"] == project_name and p["organisation"] == org_id)
    pid = project["id"]
    env = ensure(f"environments/?project={pid}", {"name": "Participant drill", "project": pid},
                 lambda e: e["name"] == "Participant drill" and e["project"] == pid)
    root = f'environments/{env["api_key"]}/'
    warehouse_path = root + "warehouse-connections/"
    warehouse = next(iter(records(warehouse_path)), None)
    if not warehouse:
        warehouse = request(warehouse_path, {"warehouse_type": "postgres", "config": {"source": "flagsmith_database"}})
    if warehouse["status"] != "connected":
        raise SystemExit("Connect the experiment warehouse in Flagsmith before continuing.")

    flag_path = f"projects/{pid}/features/"
    flag = ensure(flag_path, {"name": "triage_guide", "type": "MULTIVARIATE",
                              "project": pid, "default_enabled": True, "initial_value": "control"},
                  lambda f: f["name"] == "triage_guide")
    variants = flag_path + str(flag["id"]) + "/mv-options/"
    variant = ensure(variants, {"feature": flag["id"], "type": "unicode", "string_value": "guided",
                                "key": "guided", "default_percentage_allocation": 0},
                     lambda v: v["key"] == "guided")
    name = "First attempt resolved within 60 seconds"
    metric = ensure(root + "experiment-metrics/", {"name": name, "direction": "up", "aggregation": "occurrence",
                    "definition": {"version": 1, "event": "drill_resolved"}}, lambda m: m["name"] == name)
    name = "Can a runbook help on-call responders?"
    path = root + "experiments/"
    experiment = ensure(path, {
        "name": name, "feature": flag["id"],
        "hypothesis": "A three-step runbook increases first-attempt correct diagnoses within 60 seconds.",
        "metrics": [{"metric": metric["id"], "expected_direction": "increase"}],
        "experiment_rollout": {"enabled": True, "rollout_percentage": 100,
            "feature_state_value": {"type": "string", "value": "control"},
            "multivariate_feature_state_values": [{"multivariate_feature_option": variant["id"], "percentage_allocation": 50}]},
    }, lambda e: e["name"] == name)
    detail = path + str(experiment["id"]) + "/"
    if experiment["status"] == "created":
        request(detail + "start/", {})
    if request(detail)["status"] != "running":
        raise SystemExit("The experiment is not running. Check its status in the dashboard.")
    print("Participant experiment is running.", file=sys.stderr)
    # Only the client-side environment key belongs in a browser configuration.
    print("VITE_FLAGSMITH_ENVIRONMENT_ID=" + env["api_key"])


if __name__ == "__main__":
    if "FLAGSMITH_MANAGEMENT_TOKEN" not in os.environ or len(sys.argv) != 2:
        raise SystemExit("Supply FLAGSMITH_MANAGEMENT_TOKEN in the environment and pass the numeric organisation ID.")
    setup(int(sys.argv[1]))
