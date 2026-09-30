CREATE VIEW experimentation_delivery_connections AS
SELECT
    environment.api_key AS client_api_key,
    connection.id AS connection_id,
    connection.warehouse_type,
    connection.config,
    connection.credentials
FROM experimentation_warehouseconnection AS connection
JOIN environments_environment AS environment
    ON environment.id = connection.environment_id
WHERE connection.deleted_at IS NULL
    AND environment.deleted_at IS NULL
    AND connection.warehouse_type <> 'flagsmith';
