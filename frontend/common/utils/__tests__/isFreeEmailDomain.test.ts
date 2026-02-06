import isFreeEmailDomain from 'common/utils/isFreeEmailDomain'

describe('isFreeEmailDomain', () => {
  it.each`
    input                      | expected
    ${'user@gmail.com'}        | ${true}
    ${'user@yahoo.com'}        | ${true}
    ${'user@hotmail.com'}      | ${true}
    ${'user@outlook.com'}      | ${true}
    ${'user@company.com'}      | ${false}
    ${'user@flagsmith.com'}    | ${false}
    ${'user@enterprise.co.uk'} | ${false}
    ${null}                    | ${false}
    ${undefined}               | ${false}
    ${''}                      | ${false}
    ${'invalid-email'}         | ${false}
    ${'@gmail.com'}            | ${true}
  `('isFreeEmailDomain($input) returns $expected', ({ expected, input }) => {
    expect(isFreeEmailDomain(input)).toBe(expected)
  })
})
