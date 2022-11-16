import React from 'react';
import EnvironmentStore from '../stores/environment-store';

const EnvironmentProvider = class extends React.Component {
    static displayName = 'EnvironmentProvider'

    constructor(props, context) {
        super(props, context);
        this.state = {
            isLoading: !EnvironmentStore.model,
            env: EnvironmentStore.model,
            name: EnvironmentStore.model && EnvironmentStore.model.name,
            flags: EnvironmentStore.getFlagsForEditing(),
        };
        ES6Component(this);
        this.listenTo(EnvironmentStore, 'change', () => {
            this.setState({
                isSaving: EnvironmentStore.isSaving,
                isLoading: EnvironmentStore.isLoading,
                env: EnvironmentStore.model,
                name: this.state.name || (EnvironmentStore.model && EnvironmentStore.model.name),
                flags: this.state.flags || (EnvironmentStore.getFlagsForEditing()),
            });
        });

        this.listenTo(EnvironmentStore, 'saved', () => {
            this.setState({
                name: EnvironmentStore.model && EnvironmentStore.model.name,
                flags: EnvironmentStore.getFlagsForEditing(),
            });
            this.props.onSave && this.props.onSave();
        });
    }

    reset = () => {
        this.setState({
            flags: EnvironmentStore.getFlagsForEditing(),
            name: EnvironmentStore.model && EnvironmentStore.model.name,
        });
    };

    toggleFlag = (i) => {
        const { flags } = this.state;
        flags[i].enabled = !flags[i].enabled;
        this.setState({ flags });
    };


    remove = () => {
        AppActions.removeEnvironment(Object.assign({}, EnvironmentStore.model, {
            featurestates: this.state.flags,
            name: this.state.name,
        }));
    };

    save = () => {
        AppActions.saveEnvironment(Object.assign({}, EnvironmentStore.model, {
            featurestates: this.state.flags,
            name: this.state.name,
        }));
    };

    render() {
        return (
            this.props.children(
                {
                    ...this.state,
                    toggleFlag: this.toggleFlag,
                    setName: this.setName,
                    saveEnv: this.save,
                    reset: this.reset,
                },
            )
        );
    }
};

EnvironmentProvider.propTypes = {
    onSave: OptionalFunc,
    children: OptionalNode,
};

module.exports = EnvironmentProvider;
