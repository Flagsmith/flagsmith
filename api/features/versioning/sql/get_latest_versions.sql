SELECT
    fv."uuid",
    fv."published_at",
    fv."live_from"
FROM feature_versioning_environmentfeatureversion fv
JOIN (
    SELECT fv.feature_id, fv.environment_id, MAX(fv.live_from) AS latest_release
    FROM feature_versioning_environmentfeatureversion fv
    WHERE fv.deleted_at is null
    AND fv.published_at is not null
    GROUP BY fv.feature_id, fv.environment_id
) latest_release_dates ON fv.feature_id = latest_release_dates.feature_id
    AND fv.environment_id = latest_release_dates.environment_id
    AND fv.live_from = latest_release_dates.latest_release
WHERE fv.environment_id = %(environment_id)s;