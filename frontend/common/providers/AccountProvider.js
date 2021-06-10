import React, { Component } from 'react';
import AccountStore from '../stores/account-store';
import AppLoader from '../../web/components/AppLoader';

const AccountProvider = class extends Component {
    static displayName = 'AccountProvider'

    constructor(props, context) {
        super(props, context);
        this.state = {
            isLoading: AccountStore.isLoading,
            organisation: AccountStore.getOrganisation(),
            organisations: AccountStore.getOrganisations(),
            user: AccountStore.getUser(),
        };
    }

    componentDidMount() {
        ES6Component(this);
        this.listenTo(AccountStore, 'change', () => {
            this.setState({
                isLoading: AccountStore.isLoading,
                isSaving: AccountStore.isSaving,
                organisation: AccountStore.getOrganisation(),
                organisations: AccountStore.getOrganisations(),
                user: AccountStore.getUser(),
                error: AccountStore.error,
            });
        });

        this.listenTo(AccountStore, 'loaded', () => {
            this.props.onLogin && this.props.onLogin();
        });

        this.listenTo(AccountStore, 'saved', () => {
            this.props.onSave && this.props.onSave(AccountStore.savedId);
        });

        this.listenTo(AccountStore, 'logout', () => {
            this.setState({
                isLoading: false,
                isSaving: false,
                organisation: AccountStore.getOrganisation(),
                user: AccountStore.getUser(),
            });
            this.props.onLogout && this.props.onLogout();
        });
        this.listenTo(AccountStore, 'no-user', () => {
            this.setState({
                isSaving: false,
                isLoading: false,
                organisation: AccountStore.getOrganisation(),
                user: AccountStore.getUser(),
            });
            this.props.onNoUser && this.props.onNoUser();
        });
        this.listenTo(AccountStore, 'problem', () => {
            this.setState({
                isLoading: AccountStore.isLoading,
                isSaving: AccountStore.isSaving,
                error: AccountStore.error,
            });
        });
        this.listenTo(AccountStore, 'removed', () => {
            this.props.onRemove && this.props.onRemove();
            if (this.props.onLogin) {
                this.setState({
                    isLoading: false,
                    isSaving: false,
                    organisation: AccountStore.getOrganisation(),
                    user: AccountStore.getUser(),
                });
            }
        });
    }


    login = (details) => {
        AppActions.login(details);
    };

    loginDemo = () => {
        AppActions.login(Project.demoAccount);
    };

    register = (details, isInvite) => {
        AppActions.register(details, isInvite);
    };

    render() {
        const { isLoading, isSaving, user, organisation, organisations, error } = this.state;
        if (isLoading) {
            return (
               <AppLoader/>
            );
        }
        return (
            this.props.children({
                isLoading,
                isSaving,
                user,
                organisation,
                organisations,
                error,
            }, {
                loginDemo: this.loginDemo,
                login: this.login,
                register: this.register,
                enableTwoFactor: AppActions.enableTwoFactor,
                confirmTwoFactor: AppActions.confirmTwoFactor,
                twoFactorLogin: AppActions.twoFactorLogin,
                disableTwoFactor: AppActions.disableTwoFactor,
                selectOrganisation: AppActions.selectOrganisation,
                createOrganisation: AppActions.createOrganisation,
                editOrganisation: AppActions.editOrganisation,
                acceptInvite: AppActions.acceptInvite,
                deleteOrganisation: AppActions.deleteOrganisation,
            })
        );
    }
};

AccountProvider.propTypes = {};

module.exports = AccountProvider;
