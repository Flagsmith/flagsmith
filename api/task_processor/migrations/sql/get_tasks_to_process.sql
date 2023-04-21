CREATE OR REPLACE FUNCTION get_tasks_to_process(num_tasks integer)
RETURNS SETOF task_processor_task AS $$
DECLARE
    row_to_return task_processor_task;
BEGIN
    -- Select the tasks that needs to be processed
    FOR row_to_return IN
        SELECT *
        FROM task_processor_task
        WHERE num_failures < 3 AND scheduled_for < NOW() AND completed = FALSE AND is_locked = FALSE
        ORDER BY scheduled_for ASC, created_at ASC
        LIMIT num_tasks
        FOR UPDATE SKIP LOCKED
    LOOP
        -- Lock(by updating `is_locked` to true) every selected task selected task
        UPDATE task_processor_task
        SET is_locked = TRUE
        WHERE id = row_to_return.id;
        -- Update `is_locked` to true before returning the row
        row_to_return.is_locked := TRUE;
        RETURN NEXT row_to_return;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql

