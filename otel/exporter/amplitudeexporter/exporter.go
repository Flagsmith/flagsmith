package amplitudeexporter

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"

	"go.opentelemetry.io/collector/component"
	"go.opentelemetry.io/collector/pdata/pcommon"
	"go.opentelemetry.io/collector/pdata/plog"
	"go.uber.org/zap"
)

const (
	baggageDeviceID  = "amplitude.device_id"
	baggageSessionID = "amplitude.session_id"
)

// amplitudeEvent mirrors a single event in Amplitude's HTTP V2 API.
type amplitudeEvent struct {
	EventType       string         `json:"event_type"`
	UserID          string         `json:"user_id,omitempty"`
	DeviceID        string         `json:"device_id,omitempty"`
	SessionID       int64          `json:"session_id,omitempty"`
	Time            int64          `json:"time,omitempty"`
	EventProperties map[string]any `json:"event_properties,omitempty"`
	InsertID        string         `json:"insert_id,omitempty"`
}

// amplitudePayload is the top-level request body for Amplitude's HTTP V2 API.
type amplitudePayload struct {
	APIKey string           `json:"api_key"`
	Events []amplitudeEvent `json:"events"`
}

type amplitudeExporter struct {
	cfg    *Config
	logger *zap.Logger
	client *http.Client
}

func newAmplitudeExporter(cfg *Config, logger *zap.Logger) *amplitudeExporter {
	return &amplitudeExporter{cfg: cfg, logger: logger}
}

func (e *amplitudeExporter) start(_ context.Context, _ component.Host) error {
	e.client = &http.Client{}
	return nil
}

func (e *amplitudeExporter) shutdown(_ context.Context) error {
	if e.client != nil {
		e.client.CloseIdleConnections()
	}
	return nil
}

func (e *amplitudeExporter) consumeLogs(ctx context.Context, ld plog.Logs) error {
	events := e.mapLogs(ld)
	if len(events) == 0 {
		return nil
	}

	payload := amplitudePayload{
		APIKey: e.cfg.APIKey,
		Events: events,
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("marshal amplitude payload: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, e.cfg.Endpoint, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("create amplitude request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := e.client.Do(req)
	if err != nil {
		return fmt.Errorf("amplitude request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		e.logger.Debug("amplitude export succeeded", zap.Int("events", len(events)))
		return nil
	}

	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode == http.StatusTooManyRequests {
		return fmt.Errorf("amplitude throttled (429): %s", respBody)
	}
	if resp.StatusCode >= 500 {
		return fmt.Errorf("amplitude server error (%d): %s", resp.StatusCode, respBody)
	}
	// 4xx errors other than 429 are not retryable.
	e.logger.Error("amplitude rejected events",
		zap.Int("status", resp.StatusCode),
		zap.String("body", string(respBody)),
	)
	return nil
}

func (e *amplitudeExporter) mapLogs(ld plog.Logs) []amplitudeEvent {
	var events []amplitudeEvent

	for i := range ld.ResourceLogs().Len() {
		rl := ld.ResourceLogs().At(i)
		for j := range rl.ScopeLogs().Len() {
			sl := rl.ScopeLogs().At(j)
			for k := range sl.LogRecords().Len() {
				lr := sl.LogRecords().At(k)
				event := e.mapLogRecord(lr)
				if event.EventType != "" {
					events = append(events, event)
				}
			}
		}
	}
	return events
}

func (e *amplitudeExporter) mapLogRecord(lr plog.LogRecord) amplitudeEvent {
	eventType := lr.EventName()
	if eventType == "" {
		eventType = lr.Body().AsString()
	}

	props := make(map[string]any)
	var userID string
	var deviceID string
	var sessionID int64

	lr.Attributes().Range(func(k string, v pcommon.Value) bool {
		switch k {
		case e.cfg.UserIDAttribute:
			userID = e.cfg.UserIDPrefix + v.AsString()
		case baggageDeviceID:
			deviceID = v.AsString()
		case baggageSessionID:
			sessionID, _ = strconv.ParseInt(v.AsString(), 10, 64)
		default:
			props[k] = v.AsString()
		}
		return true
	})

	var timeMs int64
	if ts := lr.Timestamp(); ts != 0 {
		timeMs = int64(ts) / 1_000_000 // nanoseconds -> milliseconds
	}

	return amplitudeEvent{
		EventType:       eventType,
		UserID:          userID,
		DeviceID:        deviceID,
		SessionID:       sessionID,
		Time:            timeMs,
		EventProperties: props,
		InsertID:        lr.TraceID().String() + "-" + lr.SpanID().String(),
	}
}
