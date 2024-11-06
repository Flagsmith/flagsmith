ALTER TABLE {ffadminuser_table_name}
ADD COLUMN first_name varchar(30) NULL;
UPDATE {ffadminuser_table_name}
SET first_name = left({ffadminuser_table_name}.first_name_v2, 30);
ALTER TABLE {ffadminuser_table_name}
ALTER COLUMN first_name SET NOT NULL;
ALTER TABLE {ffadminuser_table_name}
DROP COLUMN first_name_v2;
