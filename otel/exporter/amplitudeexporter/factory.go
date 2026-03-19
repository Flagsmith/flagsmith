package amplitudeexporter

import (
	"context"

	"go.opentelemetry.io/collector/component"
	"go.opentelemetry.io/collector/config/configretry"
	"go.opentelemetry.io/collector/exporter"
	"go.opentelemetry.io/collector/exporter/exporterhelper"
)

const typeStr = "amplitude"

// NewFactory creates an exporter.Factory for Amplitude.
func NewFactory() exporter.Factory {
	return exporter.NewFactory(
		component.MustNewType(typeStr),
		createDefaultConfig,
		exporter.WithLogs(createLogsExporter, component.StabilityLevelAlpha),
	)
}

func createDefaultConfig() component.Config {
	return &Config{
		Endpoint:        "https://api2.amplitude.com/2/httpapi",
		UserIDAttribute: "organisation.id",
		UserIDPrefix:    "org:",
		TimeoutConfig:   exporterhelper.NewDefaultTimeoutConfig(),
		BackOffConfig:   configretry.NewDefaultBackOffConfig(),
	}
}

func createLogsExporter(
	ctx context.Context,
	set exporter.Settings,
	cfg component.Config,
) (exporter.Logs, error) {
	c := cfg.(*Config)
	exp := newAmplitudeExporter(c, set.TelemetrySettings.Logger)
	return exporterhelper.NewLogs(ctx, set, cfg,
		exp.consumeLogs,
		exporterhelper.WithStart(exp.start),
		exporterhelper.WithShutdown(exp.shutdown),
		exporterhelper.WithTimeout(c.TimeoutConfig),
		exporterhelper.WithRetry(c.BackOffConfig),
	)
}
