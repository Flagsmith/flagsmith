select
	efv1."uuid",
	efv1."published_at",
	efv1."live_from"
from
	feature_versioning_environmentfeatureversion efv1
join (
	select
		efv2."feature_id",
		efv2."environment_id",
		MAX(efv2."live_from") as "latest_release"
	from
		feature_versioning_environmentfeatureversion efv2
	where
		efv2."deleted_at" is null
		and efv2."published_at" is not null
	group by
		efv2."feature_id",
		efv2."environment_id"
) latest_release_dates on
	efv1."feature_id" = latest_release_dates."feature_id"
	and efv1."environment_id" = latest_release_dates."environment_id"
	and efv1."live_from" = latest_release_dates."latest_release"
where
	efv1.environment_id = %(environment_id)s;