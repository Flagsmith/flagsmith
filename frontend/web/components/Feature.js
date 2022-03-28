// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import TheInput from 'material-ui-chip-input';
import ValueEditor from "./ValueEditor";
import Constants from "../../common/constants";
import VariationOptions from "./mv/VariationOptions";
import AddVariationButton from "./mv/AddVariationButton";

export default class Feature extends PureComponent {
    static displayName = 'Feature';

    removeVariation = (i) => {
        const idToRemove = this.props.multivariate_options[i].id;

        if (idToRemove) {
            openConfirm('Please confirm', 'This will remove the variation on your feature for all environments, if you wish to turn it off just for this environment you can set the % value to 0.', () => {
                this.props.removeVariation(i)
            });
        } else {
            this.props.removeVariation(i)
        }
    }
    render() {
        const {
            identity,
            hide_from_client,
            checked,
            onCheckedChange,
            isEdit,
            environmentFlag,
            readOnly,
            projectFlag,
            multivariate_options,
            value,
            environmentVariations,
            onValueChange
        } = this.props

        const enabledString = isEdit ? 'Enabled' : 'Enabled by default';
        const disabled =hide_from_client
        const controlValue = Utils.calculateControl(multivariate_options, environmentVariations);
        const valueString = identity ? 'User override' : !!multivariate_options && multivariate_options.length ? `Control Value - ${controlValue}%` : `Value (optional)${' - these can be set per environment'}`;

        const showValue = !(!!identity && (multivariate_options && !!multivariate_options.length))
        return (
            <div>
                <FormGroup className="mb-4 mr-3 ml-3">
                    <div>
                        <label>{enabledString || "Enabled"}</label>
                    </div>
                    <Switch
                        data-test="toggle-feature-button"
                        defaultChecked={checked}
                        disabled={disabled || readOnly}
                        checked={!disabled && checked}
                        onChange={onCheckedChange}
                    />
                </FormGroup>

                {showValue && (
                    <FormGroup className="mx-3 mb-4 mr-3">
                        <InputGroup
                            component={(
                                <ValueEditor
                                    data-test="featureValue"
                                    name="featureValue" className="full-width"
                                    value={`${typeof value === 'undefined' || value === null ? '' : value}`}
                                    onChange={onValueChange}
                                    disabled={hide_from_client}
                                    placeholder="e.g. 'big' "
                                />
                            )}
                            tooltip={Constants.strings.REMOTE_CONFIG_DESCRIPTION}
                            title={`${valueString}`}
                        />
                    </FormGroup>
                ) }

                {!!identity && (
                    <div>
                        <FormGroup className="mb-4 mx-3">
                            <VariationOptions
                                disabled
                                select
                                controlValue={environmentFlag.feature_state_value}
                                variationOverrides={this.props.identityVariations}
                                setVariations={this.props.onChangeIdentityVariations}
                                updateVariation={() => {}}
                                weightTitle="Override Weight %"
                                projectFlag={projectFlag}
                                multivariateOptions={projectFlag.multivariate_options}
                                removeVariation={() => {}}
                            />
                        </FormGroup>
                    </div>
                )}
                {!identity && (
                    <div>
                        <FormGroup className="ml-3 mb-4 mr-3">
                            {(!!environmentVariations || !isEdit) && (
                                <VariationOptions
                                    disabled={!!identity}
                                    controlValue={controlValue}
                                    variationOverrides={environmentVariations}
                                    updateVariation={this.props.updateVariation}
                                    weightTitle={isEdit ? 'Environment Weight %' : 'Default Weight %'}
                                    multivariateOptions={multivariate_options}
                                    removeVariation={this.removeVariation}
                                />
                            )}
                        </FormGroup>
                        {!this.props.hideAddVariation && (
                            <AddVariationButton onClick={this.props.addVariation}/>
                        )}
                    </div>

                )}
            </div>
        )
    }
}
