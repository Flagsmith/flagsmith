package amplitudeexporter

import (
	"errors"

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

	BackOffConfig configretry.BackOffConfig  `mapstructure:"retry_on_failure"`
	TimeoutConfig exporterhelper.TimeoutConfig `mapstructure:",squash"`
}

func (c *Config) Validate() error {
	if c.APIKey == "" {
		return errors.New("api_key is required")
	}
	if c.Endpoint == "" {
		return errors.New("endpoint is required")
	}
	return nil
}
