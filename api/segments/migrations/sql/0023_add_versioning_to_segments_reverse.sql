UPDATE segments_segment
SET deleted_at = now()
WHERE version_of_id <> id;
