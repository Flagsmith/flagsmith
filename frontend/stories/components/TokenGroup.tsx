import React from 'react'

type TokenEntry = { cssVar: string; computed: string }
type TokenGroupData = { title: string; tokens: TokenEntry[] }

const TokenSwatch: React.FC<{ token: TokenEntry }> = ({ token }) => (
  <div className='token-swatch'>
    <div
      className='token-swatch__preview'
      style={{ background: `var(${token.cssVar})` }}
    />
    <code className='token-swatch__name'>{token.cssVar}</code>
    <code className='token-swatch__value'>{token.computed}</code>
  </div>
)

const TokenGroup: React.FC<{ group: TokenGroupData }> = ({ group }) => (
  <div className='token-group'>
    <h3 className='token-group__title'>{group.title}</h3>
    <div className='token-group__header'>
      <span />
      {['Token', 'Computed value'].map((h) => (
        <span key={h} className='token-group__header-label'>
          {h}
        </span>
      ))}
    </div>
    {group.tokens.map((token) => (
      <TokenSwatch key={token.cssVar} token={token} />
    ))}
  </div>
)

export default TokenGroup
export type { TokenEntry, TokenGroupData }
