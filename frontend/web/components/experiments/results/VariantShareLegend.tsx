import { FC } from 'react'
import ColorSwatch from 'components/ColorSwatch'
import { VariantTotal } from './derive'

type VariantShareLegendProps = {
  totals: VariantTotal[]
  excludedIdentities: number
}

const VariantShareLegend: FC<VariantShareLegendProps> = ({
  excludedIdentities,
  totals,
}) => (
  <div>
    {totals.map((t) => (
      <div key={t.key}>
        <div className='experiment-results__legend-row'>
          <span className='experiment-results__legend-name'>
            <ColorSwatch color={t.colour} shape='circle' size='sm' />
            {t.name}
          </span>
          <span className='text-muted'>
            {t.total.toLocaleString()} · {Math.round(t.share * 100)}%
          </span>
        </div>
        <div className='experiment-results__bar'>
          <div
            className='experiment-results__bar-fill'
            style={{
              background: t.colour,
              width: `${Math.round(t.share * 100)}%`,
            }}
          />
        </div>
      </div>
    ))}
    <div className='text-muted fs-caption'>
      Excluded (multi-variant): {excludedIdentities.toLocaleString()}
    </div>
  </div>
)

export default VariantShareLegend
