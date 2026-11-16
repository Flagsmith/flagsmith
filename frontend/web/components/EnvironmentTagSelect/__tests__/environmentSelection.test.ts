import { getNextEnvironmentSelection } from 'components/EnvironmentTagSelect/environmentSelection'

describe('getNextEnvironmentSelection', () => {
  it.each`
    name                                   | value              | clicked   | multiple | allowEmpty | expected
    ${'adds to a multiple selection'}      | ${['prod']}        | ${'dev'}  | ${true}  | ${false}   | ${['prod', 'dev']}
    ${'removes from a multiple selection'} | ${['prod', 'dev']} | ${'dev'}  | ${true}  | ${false}   | ${['prod']}
    ${'can empty a multiple selection'}    | ${['prod']}        | ${'prod'} | ${true}  | ${false}   | ${[]}
    ${'starts a multiple selection'}       | ${undefined}       | ${'prod'} | ${true}  | ${false}   | ${['prod']}
    ${'picks one in single mode'}          | ${undefined}       | ${'prod'} | ${false} | ${false}   | ${'prod'}
    ${'switches in single mode'}           | ${'prod'}          | ${'dev'}  | ${false} | ${false}   | ${'dev'}
    ${'clears with allowEmpty'}            | ${'prod'}          | ${'prod'} | ${false} | ${true}    | ${undefined}
    ${'keeps it without allowEmpty'}       | ${'prod'}          | ${'prod'} | ${false} | ${false}   | ${'prod'}
  `('$name', ({ allowEmpty, clicked, expected, multiple, value }) => {
    expect(
      getNextEnvironmentSelection(value, clicked, { allowEmpty, multiple }),
    ).toEqual(expected)
  })
})
