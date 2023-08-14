do $$
declare 
	/* manually define the project id here */
	_project_id int := /* PROJECT ID */;

	/* these variables need to be defined here but are populated later */
	_segment_ids_to_delete int[];
	_parent_rule_ids_to_delete int[];
	_child_rule_ids_to_delete int[];
	_feature_segment_ids_to_delete int[];
	_feature_state_ids_to_delete int[];
begin
	_segment_ids_to_delete := array(
		select s.id 
		from segments_segment s 
		where s.project_id = _project_id
	);
	_parent_rule_ids_to_delete := array(
		select sr1.id
		from segments_segmentrule sr1
		where sr1.segment_id = any(_segment_ids_to_delete)
	);
	_child_rule_ids_to_delete := array(
		select sr1.id
		from segments_segmentrule sr1
		where sr1.rule_id = any(_parent_rule_ids_to_delete)
	);
	_feature_segment_ids_to_delete := array(
		select "fseg".id 
   		from features_featuresegment "fseg"
    	where "fseg".segment_id = any(_segment_ids_to_delete)
	);
	_feature_state_ids_to_delete := array(
		select "fs".id
		from features_featurestate "fs"
		where "fs".feature_segment_id = any(_feature_segment_ids_to_delete)
	);
	
	delete from features_featurestatevalue where feature_state_id = any(_feature_state_ids_to_delete);
	delete from features_featuresegment where segment_id = any(_segment_ids_to_delete);
	delete from features_featurestate where id = any(_feature_state_ids_to_delete);
	delete from segments_condition where rule_id = any(_child_rule_ids_to_delete);
	delete from segments_segmentrule where id = any(_child_rule_ids_to_delete) or id = any(_parent_rule_ids_to_delete);
	delete from segments_segment where id = any(_segment_ids_to_delete);
end $$;
