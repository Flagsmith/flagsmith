CREATE OR REPLACE FUNCTION get_recurringtasks_to_process(num_tasks integer)
RETURNS SETOF task_processor_recurringtask AS $$
DECLARE
    row_to_return task_processor_recurringtask;
BEGIN
    -- Select the tasks that needs to be processed
    FOR row_to_return IN
        SELECT *
        FROM task_processor_recurringtask
        WHERE is_locked = FALSE
        ORDER BY id
        LIMIT num_tasks
        FOR UPDATE SKIP LOCKED
    LOOP
        -- Lock(by updating `is_locked` to true) every selected task  selected task
        UPDATE task_processor_recurringtask
        SET is_locked = TRUE
        WHERE id = row_to_return.id;
        -- Update `is_locked` to true before returning the row
        row_to_return.is_locked := TRUE;
        RETURN NEXT row_to_return;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql

