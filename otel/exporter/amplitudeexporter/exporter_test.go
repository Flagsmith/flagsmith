package amplitudeexporter

import (
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"go.opentelemetry.io/collector/pdata/plog"
	"go.uber.org/zap"
)

func newTestExporter(cfg *Config) *amplitudeExporter {
	exp := newAmplitudeExporter(cfg, zap.NewNop())
	exp.client = &http.Client{}
	return exp
}

func newLogRecord(eventName string, attrs map[string]string) plog.Logs {
	ld := plog.NewLogs()
	rl := ld.ResourceLogs().AppendEmpty()
	sl := rl.ScopeLogs().AppendEmpty()
	lr := sl.LogRecords().AppendEmpty()
	lr.SetEventName(eventName)
	lr.Body().SetStr(eventName)
	for k, v := range attrs {
		lr.Attributes().PutStr(k, v)
	}
	return ld
}

func TestMapLogs_AllowlistEmpty_AllEventsIncluded(t *testing.T) {
	// Given
	cfg := &Config{Events: nil}
	exp := newTestExporter(cfg)

	ld := newLogRecord("code_references.scan.created", nil)

	// When
	events := exp.mapLogs(ld)

	// Then
	if len(events) != 1 {
		t.Fatalf("expected 1 event, got %d", len(events))
	}
	if events[0].EventType != "code_references.scan.created" {
		t.Errorf("expected event_type 'code_references.scan.created', got %q", events[0].EventType)
	}
}

func TestMapLogs_AllowlistMatch_EventIncluded(t *testing.T) {
	// Given
	cfg := &Config{
		Events: []string{"code_references.*"},
	}
	exp := newTestExporter(cfg)

	ld := newLogRecord("code_references.scan.created", nil)

	// When
	events := exp.mapLogs(ld)

	// Then
	if len(events) != 1 {
		t.Fatalf("expected 1 event, got %d", len(events))
	}
}

func TestMapLogs_AllowlistNoMatch_EventExcluded(t *testing.T) {
	// Given
	cfg := &Config{
		Events: []string{"feature_lifecycle.*"},
	}
	exp := newTestExporter(cfg)

	ld := newLogRecord("code_references.scan.created", nil)

	// When
	events := exp.mapLogs(ld)

	// Then
	if len(events) != 0 {
		t.Fatalf("expected 0 events, got %d", len(events))
	}
}

func TestMapLogs_AllowlistMultiplePatterns_MatchesAny(t *testing.T) {
	// Given
	cfg := &Config{
		Events: []string{"feature_lifecycle.*", "code_references.*"},
	}
	exp := newTestExporter(cfg)

	ld := newLogRecord("code_references.cleanup_issues.created", nil)

	// When
	events := exp.mapLogs(ld)

	// Then
	if len(events) != 1 {
		t.Fatalf("expected 1 event, got %d", len(events))
	}
}

func TestMapLogRecord_ExtractsBaggageFields(t *testing.T) {
	// Given
	cfg := &Config{
		UserIDAttribute: "organisation.id",
		UserIDPrefix:    "org:",
	}
	exp := newTestExporter(cfg)

	ld := newLogRecord("code_references.scan.created", map[string]string{
		"organisation.id":      "42",
		"amplitude.device_id":  "device-abc",
		"amplitude.session_id": "1710864000000",
		"feature.count":        "3",
	})

	// When
	events := exp.mapLogs(ld)

	// Then
	if len(events) != 1 {
		t.Fatalf("expected 1 event, got %d", len(events))
	}
	ev := events[0]
	if ev.UserID != "org:42" {
		t.Errorf("expected user_id 'org:42', got %q", ev.UserID)
	}
	if ev.DeviceID != "device-abc" {
		t.Errorf("expected device_id 'device-abc', got %q", ev.DeviceID)
	}
	if ev.SessionID != 1710864000000 {
		t.Errorf("expected session_id 1710864000000, got %d", ev.SessionID)
	}
	if ev.EventProperties["feature.count"] != "3" {
		t.Errorf("expected feature.count '3', got %v", ev.EventProperties["feature.count"])
	}
	// Baggage and user ID fields should not leak into event_properties.
	for _, key := range []string{"organisation.id", "amplitude.device_id", "amplitude.session_id"} {
		if _, ok := ev.EventProperties[key]; ok {
			t.Errorf("expected %q to be excluded from event_properties", key)
		}
	}
}

func TestConsumeLogs_SendsToAmplitudeAPI(t *testing.T) {
	// Given
	var received amplitudePayload
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		json.Unmarshal(body, &received)
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	cfg := &Config{
		APIKey:          "test-key",
		Endpoint:        server.URL,
		UserIDAttribute: "organisation.id",
		UserIDPrefix:    "org:",
		Events:  []string{"code_references.*"},
	}
	exp := newTestExporter(cfg)

	ld := newLogRecord("code_references.scan.created", map[string]string{
		"organisation.id": "1",
		"feature.count":   "2",
	})

	// When
	err := exp.consumeLogs(t.Context(), ld)

	// Then
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if received.APIKey != "test-key" {
		t.Errorf("expected api_key 'test-key', got %q", received.APIKey)
	}
	if len(received.Events) != 1 {
		t.Fatalf("expected 1 event, got %d", len(received.Events))
	}
	if received.Events[0].EventType != "code_references.scan.created" {
		t.Errorf("expected event_type, got %q", received.Events[0].EventType)
	}
}

func TestConsumeLogs_AllowlistFilters_NothingSent(t *testing.T) {
	// Given
	called := false
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		called = true
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	cfg := &Config{
		APIKey:         "test-key",
		Endpoint:       server.URL,
		Events: []string{"feature_lifecycle.*"},
	}
	exp := newTestExporter(cfg)

	ld := newLogRecord("code_references.scan.created", nil)

	// When
	err := exp.consumeLogs(t.Context(), ld)

	// Then
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if called {
		t.Error("expected no HTTP call when all events are filtered")
	}
}

func TestConfigValidate_InvalidPattern_ReturnsError(t *testing.T) {
	// Given
	cfg := &Config{
		APIKey:         "key",
		Endpoint:       "https://example.com",
		Events: []string{"[invalid"},
	}

	// When
	err := cfg.Validate()

	// Then
	if err == nil {
		t.Error("expected validation error for invalid pattern")
	}
}
