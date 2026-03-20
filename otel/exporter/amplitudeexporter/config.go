package amplitudeexporter

import (
	"errors"
	"path"

	"go.opentelemetry.io/collector/config/configretry"
	"go.opentelemetry.io/collector/exporter/exporterhelper"
)

// Config holds the configuration for the Amplitude exporter.
type Config struct {
	// APIKey is the Amplitude project API key.
	APIKey string `mapstructure:"api_key"`

	// Endpoint is the Amplitude HTTP V2 API URL.
	Endpoint string `mapstructure:"endpoint"`

	// UserIDAttribute is the OTel log attribute used as Amplitude's user_id.
	UserIDAttribute string `mapstructure:"user_id_attribute"`

	// UserIDPrefix is prepended to the attribute value to form the user_id.
	UserIDPrefix string `mapstructure:"user_id_prefix"`

	// Events is a list of glob patterns for event names to export.
	// If empty, all events are exported. Patterns use path.Match syntax
	// (e.g. "code_references.*", "feature_lifecycle.*").
	Events []string `mapstructure:"events"`

	BackOffConfig configretry.BackOffConfig    `mapstructure:"retry_on_failure"`
	TimeoutConfig exporterhelper.TimeoutConfig `mapstructure:",squash"`
}

func (c *Config) Validate() error {
	if c.APIKey == "" {
		return errors.New("api_key is required")
	}
	if c.Endpoint == "" {
		return errors.New("endpoint is required")
	}
	for _, pattern := range c.Events {
		if _, err := path.Match(pattern, ""); err != nil {
			return errors.New("invalid event_allowlist pattern: " + pattern)
		}
	}
	return nil
}

// matchesEvents returns true if the event name matches any pattern
// in the allowlist, or if the allowlist is empty (allow all).
func (c *Config) matchesEvents(eventName string) bool {
	if len(c.Events) == 0 {
		return true
	}
	for _, pattern := range c.Events {
		if matched, _ := path.Match(pattern, eventName); matched {
			return true
		}
	}
	return false
}
