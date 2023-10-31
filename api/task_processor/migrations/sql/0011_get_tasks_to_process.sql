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
        ORDER BY priority ASC, scheduled_for ASC, created_at ASC
        LIMIT num_tasks
        -- Select for update to ensure that no other workers can select these tasks while in this transaction block
        FOR UPDATE SKIP LOCKED
    LOOP
        -- Lock every selected task(by updating `is_locked` to true)
        UPDATE task_processor_task
        -- Lock this row by setting is_locked True, so that no other workers can select these tasks after this
        -- transaction is complete (but the tasks are still being executed by the current worker)
        SET is_locked = TRUE
        WHERE id = row_to_return.id;
        -- If we don't explicitly update the `is_locked` column here, the client will receive the row that is actually locked but has the `is_locked` value set to `False`.
        row_to_return.is_locked := TRUE;
        RETURN NEXT row_to_return;
    END LOOP;

    RETURN;
END;
$$ LANGUAGE plpgsql

