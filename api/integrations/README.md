# Integrations

## Integration Health Records Cleanup

Integration health records are stored to track the status of external integration calls. These records can grow over time. A management command is provided to clean up old records.

### Running the cleanup command

To delete integration health records older than 30 days (default):

```bash
python manage.py cleanup_integration_health_records
```

To specify a custom retention period:

```bash
python manage.py cleanup_integration_health_records --days=60
```

### Scheduling automatic cleanup

To prevent the `IntegrationHealthRecord` table from growing unbounded, schedule the cleanup command to run periodically using cron or your preferred task scheduler.

Example cron entry (runs daily at 3 AM):

```cron
0 3 * * * cd /path/to/flagsmith && python manage.py cleanup_integration_health_records
```