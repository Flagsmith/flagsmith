import React, { FunctionComponent } from 'react';
import ValueEditor from '../ValueEditor'; // we need this to make JSX compile


const VariationValue = ({
    value,
    onChange,
    weightTitle,
    onRemove,
}) => (
    <div className="panel panel--flat panel-without-heading mb-2">
        <div className="panel-content">
            <Row>
                <div className="flex flex-1">
                    <InputGroup
                      component={(
                          <ValueEditor
                            data-test="featureValue"
                            name="featureValue" className="full-width"
                            value={Utils.getTypedValue(Utils.featureStateToValue(value)) + ""}
                            onChange={(e) => {
                                onChange({
                                    ...value,
                                    ...Utils.valueToFeatureState(Utils.safeParseEventValue(e)),
                                });
                            }}
                            placeholder="e.g. 'big' "
                          />
)}
                      tooltip={Constants.strings.REMOTE_CONFIG_DESCRIPTION}
                      title="Value"
                    />
                </div>
                <div className="ml-2" style={{ width: 200 }}>
                    <InputGroup
                      type="text"
                      onChange={(e) => {
                          onChange({
                              ...value,
                              default_percentage_allocation: Utils.safeParseEventValue(e) ? parseInt(Utils.safeParseEventValue(e)) : null,
                          });
                      }}
                      value={value.default_percentage_allocation}
                      inputProps={{ style: { marginTop: 2 }, maxLength: 3 }}
                      title={weightTitle}
                    />
                </div>
                {!!onRemove && (
                <div className="ml-2" style={{ width: 30, marginTop: 22 }}>
                    <button
                      onClick={onRemove}
                      id="delete-multivariate"
                      type="button"
                      className="btn btn--with-icon ml-auto btn--remove"
                    >
                        <RemoveIcon/>
                    </button>
                </div>
                )}

            </Row>
        </div>
    </div>
);

export default VariationValue;
