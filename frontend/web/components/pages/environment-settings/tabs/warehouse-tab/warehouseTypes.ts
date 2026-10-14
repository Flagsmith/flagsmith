import { WarehouseType } from 'common/types/responses'

export type WarehouseTypeOption = WarehouseType | 'bigquery'

type ConfigurableWarehouseTypesOptions = {
  clickhouseEnabled: boolean
  databricksEnabled: boolean
  isSaas: boolean
}

// The managed Flagsmith warehouse only exists on SaaS.
export const getConfigurableWarehouseTypes = ({
  clickhouseEnabled,
  databricksEnabled,
  isSaas,
}: ConfigurableWarehouseTypesOptions): WarehouseTypeOption[] => [
  ...(isSaas ? (['flagsmith'] as const) : []),
  ...(clickhouseEnabled ? (['clickhouse'] as const) : []),
  ...(databricksEnabled ? (['databricks'] as const) : []),
]
