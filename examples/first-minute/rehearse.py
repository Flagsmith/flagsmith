"""Run a seeded SDK rehearsal locally and export aggregate evidence to stdout."""

import json
import math
import os
import subprocess
import time
from pathlib import Path

from setup_experiment import (
    RateLimited,
    local_organisation,
    prepare_experiment,
    request,
)

ENVIRONMENT = "Synthetic rollout rehearsal"
PARTICIPANTS = 240
RATES = {"control": 0.45, "guided": 0.72}
POST_ROLLOUT_CHECKS = 16


def sdk(action, **config):
    process = subprocess.run(
        ["node", str(Path(__file__).with_name("rehearsal-traffic.js"))],
        input=json.dumps({"action": action, **config}),
        text=True,
        stdout=subprocess.PIPE,
        check=True,
        env={k: v for k, v in os.environ.items() if k != "FLAGSMITH_MANAGEMENT_TOKEN"},
    )
    return json.loads(process.stdout)


def metric_result(result, metric_id):
    payload = result.get("payload") or {}
    return next(
        (m for m in payload.get("metrics", []) if m["metric_id"] == metric_id), {}
    )


def counts(metric):
    return {
        key: {"exposed": row["n"], "converted": row["sum"]}
        for key, row in metric.get("variants", {}).items()
    }


def measured_results(detail, metric_id, expected):
    path = detail + "results/"
    # Flagsmith permits one refresh every five minutes and the worker computes it asynchronously.
    deadline = time.monotonic() + 420
    next_refresh = 0
    while time.monotonic() < deadline:
        result = request(path)["results"] or {}
        if counts(metric_result(result, metric_id)) == expected:
            return result
        if time.monotonic() >= next_refresh:
            try:
                request(path + "refresh/", {})
                delay = 300
            except RateLimited as limited:
                delay = limited.seconds
            next_refresh = time.monotonic() + delay
        time.sleep(3)
    raise SystemExit(
        "Warehouse counts have not caught up with the SDK. Retry after the refresh interval."
    )


def split_check(metric, reported):
    if reported is not None:
        return {"method": "Flagsmith SRM", "p_value": reported}
    # Segment rollouts can lack a server SRM value. With two equal groups,
    # use the exact two-sided binomial test against the configured 50/50 split.
    groups = metric["variants"]
    total = groups["control"]["n"] + groups["guided"]["n"]
    minority = min(groups["control"]["n"], groups["guided"]["n"])
    tail = sum(math.comb(total, k) for k in range(minority + 1)) / 2**total
    return {
        "method": "Exact binomial test against 50/50",
        "p_value": min(1.0, 2 * tail),
    }


def qualified_winner(metric, split_p_value):
    per_desk = counts(metric)
    if (
        set(per_desk) != set(RATES)
        or sum(g["exposed"] for g in per_desk.values()) != PARTICIPANTS
    ):
        raise SystemExit("The rehearsal environment contains unexpected traffic.")
    if any(g["exposed"] < 50 or g["converted"] < 5 for g in per_desk.values()):
        raise SystemExit("The experiment needs more observations.")
    if split_p_value is None or split_p_value < 0.001:
        raise SystemExit("Check the sample ratio before making a rollout decision.")
    inference = metric["inference"]["guided"]
    if inference and inference["chance_to_win"] >= 0.95 and inference["ci_low"] > 0:
        return "guided"
    if inference and inference["chance_to_win"] <= 0.05 and inference["ci_high"] < 0:
        return "control"
    raise SystemExit(
        "The rehearsal result is inconclusive. Its flag remains at the original split."
    )


def rehearse(org_id):
    env, metric, variant, detail = prepare_experiment(org_id, ENVIRONMENT)
    experiment = request(detail)
    connection = {"environment": env["api_key"], "experiment": experiment["id"]}
    status = experiment["status"]
    if status == "running":
        rollout = experiment["experiment_rollout"]
        if (
            not rollout["enabled"]
            or rollout["rollout_percentage"] != 100
            or (rollout.get("audience") or {}).get("segments")
        ):
            raise SystemExit(
                "The rehearsal must enrol all synthetic identities before it can send sample traffic."
            )
        expected = sdk("sample", **connection, total=PARTICIPANTS, rates=RATES)
        result = measured_results(detail, metric["id"], expected)
    else:
        result = request(detail + "results/")["results"]

    measurement = metric_result(result or {}, metric["id"])
    if set(measurement.get("variants", {})) != set(RATES):
        raise SystemExit("Flagsmith has not returned both rehearsal variants.")
    split = split_check(measurement, result["payload"]["srm_p_value"])
    winner = qualified_winner(measurement, split["p_value"])
    if status == "running":
        request(detail + "pause/", {})
        status = "paused"
    if status == "paused":
        # Retire the experiment's audience before changing the environment default.
        # Keep the recorded variation split when setting enrolment to zero.
        original = experiment["experiment_rollout"]
        request(
            detail + "rollout/",
            {
                "rollout_percentage": 0,
                "enabled": False,
                "feature_state_value": original["feature_state_value"],
                "multivariate_feature_state_values": original[
                    "multivariate_feature_state_values"
                ],
            },
            method="PATCH",
        )
        request(detail + "complete/", {})
    if request(detail)["status"] != "completed":
        raise SystemExit("The synthetic experiment has not completed.")

    path = (
        f"/api/__future__/environments/{env['api_key']}/features/{variant['feature']}/"
    )
    desired_weight = 100 if winner == "guided" else 0
    flag = request(path)["environment_default"]
    current_weight = next(
        (v["weight"] for v in flag["variants"] if v["id"] == variant["id"]), 0
    )
    if current_weight != desired_weight or not flag["enabled"]:
        request(
            path,
            {
                "environment_default": {
                    "enabled": True,
                    "variants": [
                        {"id": variant["id"], "weight": desired_weight},
                    ],
                }
            },
            method="PATCH",
        )
    checked = sdk("verify", **connection, total=POST_ROLLOUT_CHECKS, winner=winner)
    return {
        "traffic": "synthetic",
        "as_of": result["as_of"],
        "experiment_id": experiment["id"],
        "flag": "triage_guide",
        "metric": "drill_resolved",
        "configured_split": {"control": 50, "guided": 50},
        "simulated_success_rates": RATES,
        "variants": counts(measurement),
        "guided_inference": measurement["inference"]["guided"],
        "allocation_check": split,
        "rollout": {
            "desk": winner,
            "percentage": 100,
            "new_identities_verified": checked["verified"],
        },
    }


if __name__ == "__main__":
    print(json.dumps(rehearse(local_organisation(__doc__)), indent=2, allow_nan=False))
