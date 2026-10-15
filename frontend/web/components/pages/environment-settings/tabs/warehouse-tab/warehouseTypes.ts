import { WarehouseType } from 'common/types/responses'

export type WarehouseTypeOption = WarehouseType | 'bigquery'

// The managed Flagsmith warehouse only exists on SaaS.
export const getConfigurableWarehouseTypes = (
  isSaas: boolean,
): WarehouseTypeOption[] => [
  ...(isSaas ? (['flagsmith'] as const) : []),
  'clickhouse',
  'databricks',
]
