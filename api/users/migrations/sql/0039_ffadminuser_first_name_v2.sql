ALTER TABLE {ffadminuser_table_name}
ADD COLUMN first_name_v2 varchar(150) NULL;
UPDATE {ffadminuser_table_name}
SET first_name_v2 = {ffadminuser_table_name}.first_name;
ALTER TABLE {ffadminuser_table_name}
ALTER COLUMN first_name_v2 SET NOT NULL;
ALTER TABLE {ffadminuser_table_name}
DROP COLUMN first_name;