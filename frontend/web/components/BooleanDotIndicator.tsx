const BooleanDotIndicator = ({ enabled }: { enabled: boolean }) => (
  <div
    style={{
      backgroundColor: enabled ? '#6837fc' : '#dbdcdf',
      borderRadius: '50% 50%',
      content: ' ',
      height: 14,
      width: 14,
    }}
  />
)

export default BooleanDotIndicator
