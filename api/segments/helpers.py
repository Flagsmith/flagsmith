class SegmentAuditLogHelper:
    def __init__(self) -> None:
        self.skip_audit_log = {}

    def should_skip_audit_log(self, segment_id: int) -> None | bool:
        return self.skip_audit_log.get(segment_id)

    def set_skip_audit_log(self, segment_id: int) -> None:
        self.skip_audit_log[segment_id] = True

    def unset_skip_audit_log(self, segment_id: int) -> None:
        if segment_id in self.skip_audit_log:
            del self.skip_audit_log[segment_id]


segment_audit_log_helper = SegmentAuditLogHelper()
