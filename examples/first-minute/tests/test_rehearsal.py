import pytest
import rehearse
import setup_experiment
from setup_experiment import RateLimited


def test_measured_results__refresh_is_rate_limited__waits_for_warehouse_counts(
    monkeypatch,
):
    # Given a cooldown followed by an asynchronous warehouse refresh
    expected = {"guided": {"exposed": 2, "converted": 1}}
    result = {
        "payload": {
            "metrics": [{"metric_id": 1, "variants": {"guided": {"n": 2, "sum": 1}}}]
        }
    }
    now = 100
    refreshes = []

    def request(path, data=None):
        if path.endswith("refresh/"):
            refreshes.append(now)
            if len(refreshes) == 1:
                raise RateLimited("6")
            return None
        return {"results": result if now >= 109 else None}

    def sleep(seconds):
        nonlocal now
        now += seconds

    monkeypatch.setattr(rehearse, "request", request)
    monkeypatch.setattr(rehearse.time, "monotonic", lambda: now)
    monkeypatch.setattr(rehearse.time, "sleep", sleep)

    # When the rehearsal requests the measured results
    measured = rehearse.measured_results("experiment/", 1, expected)

    # Then it retries at the server's deadline and returns the worker's result
    assert measured == result
    assert refreshes == [100, 106]


@pytest.mark.parametrize("guided_weight", [0, 30, 100])
def test_check_rollout__reused_experiment_has_wrong_split__refuses_sampling(
    guided_weight,
):
    # Given a reused experiment with different weights
    experiment = {
        "experiment_rollout": {
            "feature_state_value": {"type": "string", "value": "control"},
            "multivariate_feature_state_values": [
                {
                    "multivariate_feature_option": 7,
                    "percentage_allocation": guided_weight,
                }
            ],
        }
    }
    # When / Then the validation fails before any identities are sampled
    with pytest.raises(SystemExit, match="50% to guided and 50% to control"):
        setup_experiment.check_rollout(experiment, 7)


def test_prepare_experiment__paused_experiment__resumes_only_when_requested(
    monkeypatch,
):
    # Given an existing experiment with an equal split between control and guided
    rollout = {
        "enabled": True,
        "rollout_percentage": 100,
        "feature_state_value": {"type": "string", "value": "control"},
        "multivariate_feature_state_values": [
            {"multivariate_feature_option": 7, "percentage_allocation": 50}
        ],
    }
    detail = {
        "status": "paused",
        "feature": {"id": 1},
        "metrics": [{"metric": 3}],
        "experiment_rollout": rollout,
    }
    starts = []

    def ensure(path, body, match):
        return {
            **body,
            "id": 7
            if path.endswith("mv-options/")
            else 3
            if path.endswith("experiment-metrics/")
            else 1,
            "api_key": "test",
        }

    def request(path, body=None):
        if path.endswith("start/"):
            starts.append(path)
        return detail

    monkeypatch.setattr(setup_experiment, "ensure", ensure)
    monkeypatch.setattr(
        setup_experiment, "records", lambda path: [{"status": "connected"}]
    )
    monkeypatch.setattr(setup_experiment, "request", request)
    # When rehearsal cleanup and participant setup reuse their paused experiment
    setup_experiment.prepare_experiment(1, "Rehearsal")
    assert starts == []
    setup_experiment.prepare_experiment(1, "Participant", resume_paused=True)
    # Then participant setup resumes precisely once
    assert starts == ["environments/test/experiments/1/start/"]

    # A paused rehearsal can finish cleanup with enrolment already closed.
    rollout["rollout_percentage"] = 0
    setup_experiment.prepare_experiment(1, "Rehearsal")
    with pytest.raises(SystemExit, match="100% of identities"):
        setup_experiment.prepare_experiment(1, "Participant", resume_paused=True)
    assert len(starts) == 1


@pytest.mark.parametrize(
    "changed",
    [
        {"enabled": False},
        {"rollout_percentage": 0},
        {"rollout_percentage": 20},
        {"audience": {"segments": [{"id": 1}]}},
    ],
)
def test_check_enrolment__rollout_excludes_players__refuses_setup(changed):
    # Given a reused participant experiment that cannot enrol every player
    rollout = {"enabled": True, "rollout_percentage": 100, **changed}
    # When / Then the participant experiment cannot be advertised as ready
    with pytest.raises(SystemExit, match="100% of identities"):
        setup_experiment.check_enrolment({"experiment_rollout": rollout})


@pytest.mark.parametrize("response", [None, [], {}])
def test_local_organisation__cookie_only_login__explains_token_requirement(
    monkeypatch, capsys, response
):
    # Given an interactive login with no user-token payload
    monkeypatch.delenv("FLAGSMITH_MANAGEMENT_TOKEN", raising=False)
    monkeypatch.setattr(setup_experiment.sys, "argv", ["setup_experiment.py"])
    monkeypatch.setattr(setup_experiment.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda: "local@example.invalid")
    monkeypatch.setattr(setup_experiment.getpass, "getpass", lambda prompt: "test")
    monkeypatch.setattr(setup_experiment, "request", lambda *args: response)
    # When / Then the CLI prints an actionable diagnostic
    with pytest.raises(SystemExit):
        setup_experiment.local_organisation("setup")
    assert "FLAGSMITH_MANAGEMENT_TOKEN" in capsys.readouterr().err
