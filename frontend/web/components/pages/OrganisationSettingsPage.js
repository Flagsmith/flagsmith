import React, { Component } from 'react';
import { BarChart, ResponsiveContainer, Bar, XAxis, YAxis, CartesianGrid, Tooltip as _Tooltip, Legend } from 'recharts';
import CreateProjectModal from '../modals/CreateProject';
import InviteUsersModal from '../modals/InviteUsers';
import UserGroupList from '../UserGroupList';
import ConfirmRemoveOrganisation from '../modals/ConfirmRemoveOrganisation';
import PaymentModal from '../modals/Payment';
import CreateGroupModal from '../modals/CreateGroup';
import CancelPaymentPlanModal from '../modals/CancelPaymentPlan';
import withAuditWebhooks from '../../../common/providers/withAuditWebhooks';
import CreateAuditWebhookModal from '../modals/CreateAuditWebhook';
import ConfirmRemoveAuditWebhook from '../modals/ConfirmRemoveAuditWebhook';
import Button from '../base/forms/Button';
import { EditPermissionsModal } from '../EditPermissions';


const OrganisationSettingsPage = class extends Component {
    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    static displayName = 'OrganisationSettingsPage';

    constructor(props, context) {
        super(props, context);
        this.state = {
            role: 'ADMIN',
            manageSubscriptionLoaded: true,
        };
        if (!AccountStore.getOrganisation()) {
            return;
        }
        AppActions.getOrganisation(AccountStore.getOrganisation().id);

        if (Utils.getFlagsmithHasFeature('usage_chart') && !projectOverrides.disableInflux) {
            AppActions.getInfluxData(AccountStore.getOrganisation().id);
        }

        this.props.getWebhooks();
    }

    componentDidMount = () => {
        API.trackPage(Constants.pages.ORGANISATION_SETTINGS);
        $('body').trigger('click');
        if (AccountStore.getUser() && AccountStore.getOrganisationRole() !== 'ADMIN') {
            this.context.router.history.replace('/projects');
        }
    };

    newProject = () => {
        openModal('Create  Project', <CreateProjectModal onSave={(projectId) => {
            this.context.router.history.push(`/project/${projectId}/environment/create`);
        }}
        />);
    };

    onSave = () => {
        toast('Saved organisation');
    }

    confirmRemove = (organisation, cb) => {
        openModal('Remove Organisation', <ConfirmRemoveOrganisation
          organisation={organisation}
          cb={cb}
        />);
    };

    onRemove = () => {
        toast('Your organisation has been removed');
        if (AccountStore.getOrganisation()) {
            this.context.router.history.replace('/projects');
        } else {
            this.context.router.history.replace('/create');
        }
    };

    deleteInvite = (id) => {
        openConfirm(<h3>Delete Invite</h3>, <p>
            Are you sure you want to delete this
            invite?
                                            </p>, () => AppActions.deleteInvite(id));
    }

    deleteUser = (id) => {
        openConfirm(<h3>Delete User</h3>, <p>
            Are you sure you want to delete this user?
                                          </p>, () => AppActions.deleteUser(id));
    }

    save = (e) => {
        e && e.preventDefault();
        const { name, webhook_notification_email, restrict_project_create_to_admin, force_2fa } = this.state;
        if (AccountStore.isSaving) {
            return;
        }

        const org = AccountStore.getOrganisation();
        AppActions.editOrganisation({
            name: name || org.name,
            force_2fa,
            restrict_project_create_to_admin: typeof restrict_project_create_to_admin === 'boolean' ? restrict_project_create_to_admin : undefined,
            webhook_notification_email: webhook_notification_email !== undefined ? webhook_notification_email : org.webhook_notification_email,
        });
    }

    save2FA = (force_2fa) => {
        const { name, webhook_notification_email, restrict_project_create_to_admin } = this.state;
        if (AccountStore.isSaving) {
            return;
        }

        const org = AccountStore.getOrganisation();
        AppActions.editOrganisation({
            name: name || org.name,
            force_2fa,
            restrict_project_create_to_admin: typeof restrict_project_create_to_admin === 'boolean' ? restrict_project_create_to_admin : undefined,
            webhook_notification_email: webhook_notification_email !== undefined ? webhook_notification_email : org.webhook_notification_email,
        });
    }

    setAdminCanCreateProject = (restrict_project_create_to_admin) => {
        this.setState({ restrict_project_create_to_admin }, this.save);
    }

    saveDisabled = () => {
        const { name, webhook_notification_email } = this.state;
        if (AccountStore.isSaving || (!name && webhook_notification_email === undefined)) {
            return true;
        }

        // Must have name
        if (name !== undefined && !name) {
            return true;
        }

        // Must be valid email for webhook notification email
        if (webhook_notification_email && !Utils.isValidEmail(webhook_notification_email)) {
            return true;
        }

        return false;
    }

    cancelPaymentPlan = () => {
        openModal(
            <h2>Are you sure you want to cancel your plan?</h2>,
            <CancelPaymentPlanModal/>,
        );
    }

    roleChanged = (id, { value: role }) => {
        AppActions.updateUserRole(id, role);
    }

    createWebhook = () => {
        openModal('New Webhook', <CreateAuditWebhookModal
          router={this.context.router}
          save={this.props.createWebhook}
        />, null, { className: 'alert fade expand' });
    };


    editWebhook = (webhook) => {
        openModal('Edit Webhook', <CreateAuditWebhookModal
          router={this.context.router}
          webhook={webhook}
          isEdit
          save={this.props.saveWebhook}
        />, null, { className: 'alert fade expand' });
    };

    deleteWebhook = (webhook) => {
        openModal('Remove Webhook', <ConfirmRemoveAuditWebhook
          url={webhook.url}
          cb={() => this.props.deleteWebhook(webhook)}
        />);
    };

    drawChart = (data) => {
        if (data && data.events_list) { // protect against influx setup incorrectly
            let totalFlags = 0;
            let totalTraits = 0;
            let totalIdentities = 0;
            data.events_list.map((v) => {
                totalFlags += v.Flags || 0;
                totalTraits += v.Traits || 0;
                totalIdentities += v.Identities || 0;
            });
            return (
                <div>
                    <div className="flex-row header--icon">
                        <h5>API usage</h5>

                    </div>
                    <div className="col-md-6 row mb-2">

                        <table className="table">
                            <thead>
                                <th style={{ width: 200, borderBottom: '1px solid #ccc' }}>
                                    <td>
                                    Usage type
                                    </td>
                                </th>
                                <th style={{ borderBottom: '1px solid #ccc' }}>
                                    <td>
                                    API calls
                                    </td>
                                </th>
                            </thead>
                            <tbody>
                                <tr style={{ borderBottom: '1px solid #ccc' }}>
                                    <td>
                                    Flags
                                    </td>
                                    <td>
                                        {Utils.numberWithCommas(totalFlags)}
                                    </td>
                                </tr>
                                <tr style={{ borderBottom: '1px solid #ccc' }}>
                                    <td>
                                    Identities
                                    </td>
                                    <td>
                                        {Utils.numberWithCommas(totalIdentities)}
                                    </td>
                                </tr>
                                <tr style={{ borderBottom: '1px solid #ccc' }}>
                                    <td>
                                    Traits
                                    </td>
                                    <td>
                                        {Utils.numberWithCommas(totalTraits)}
                                    </td>
                                </tr>
                                <tr style={{ borderTop: '1px solid #ccc' }}>
                                    <td>
                                        <strong>
                                        Total
                                        </strong>
                                    </td>
                                    <td>
                                        <strong>
                                            {Utils.numberWithCommas(totalFlags + totalIdentities + totalTraits)}
                                        </strong>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <ResponsiveContainer height={400} width="100%">
                        <BarChart data={data.events_list}>
                            <CartesianGrid strokeDasharray="3 5"/>
                            <XAxis allowDataOverflow={false} dataKey="name"/>
                            <YAxis allowDataOverflow={false} />
                            <_Tooltip/>
                            <Legend />
                            <Bar dataKey="Flags" stackId="a" fill="#6633ff" />
                            <Bar dataKey="Identities" stackId="a" fill="#00a696" />
                            <Bar dataKey="Traits" stackId="a" fill="#f18e7f" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

            );
        }
        return null;
    }

    editUserPermissions = (user) => {
        openModal('Edit Organisation Permissions', <EditPermissionsModal
          name={`${user.first_name} ${user.last_name}`}
          id={AccountStore.getOrganisation().id}
          onSave={() => {
              AppActions.getOrganisation(AccountStore.getOrganisation().id);
          }}
          level="organisation"
          user={user}
        />);
    }

    editGroupPermissions = (group) => {
        openModal(`Edit Organisation Permissions`, <EditPermissionsModal
          name={`${group.name}`}
          id={AccountStore.getOrganisation().id}
          isGroup
          onSave={() => {
              AppActions.getOrganisation(AccountStore.getOrganisation().id);
          }}
          level="organisation"
          group={group}
          push={this.context.router.history.push}
        />);
    }

    render() {
        const { name, webhook_notification_email } = this.state;
        const { props: { webhooks, webhooksLoading } } = this;
        const hasRbacPermission = !Utils.getFlagsmithHasFeature('plan_based_access') || Utils.getPlansPermission('RBAC');
        const paymentsEnabled = Utils.getFlagsmithHasFeature('payments_enabled');
        const force2faPermission = Utils.getPlansPermission('FORCE_2FA');

        return (
            <div className="app-container container">

                <AccountProvider onSave={this.onSave} onRemove={this.onRemove}>
                    {({
                        isLoading,
                        isSaving,
                        user,
                        organisation,
                    }, { createOrganisation, selectOrganisation, deleteOrganisation }) => !!organisation && (
                        <OrganisationProvider>
                            {({ isLoading, name, error, projects, usage, users, invites, influx_data, inviteLinks }) => (
                                <div>
                            <FormGroup>
                                <div className="margin-bottom">
                                    <div className="panel--grey" style={{ marginTop: '3em' }}>
                                        <form key={organisation.id} onSubmit={this.save}>
                                            <h5>Organisation Name</h5>
                                            <Row>
                                                <Column className="m-l-0">
                                                    <Input
                                                      ref={e => this.input = e}
                                                      data-test="organisation-name"
                                                      value={this.state.name || organisation.name}
                                                      onChange={e => this.setState({ name: Utils.safeParseEventValue(e) })}
                                                      isValid={name && name.length}
                                                      type="text"
                                                      inputClassName="input--wide"
                                                      placeholder="My Organisation"
                                                    />
                                                </Column>
                                                <Button disabled={this.saveDisabled()} className="float-right">
                                                    {isSaving ? 'Saving' : 'Save'}
                                                </Button>
                                            </Row>
                                        </form>
                                        {paymentsEnabled && (
                                            <div className="plan plan--current flex-row m-t-2">
                                                <div className="plan__prefix">
                                                    <img
                                                      src="/static/images/nav-logo.svg" className="plan__prefix__image"
                                                      alt="BT"
                                                    />
                                                </div>
                                                <div className="plan__details flex flex-1">
                                                    <p className="text-small m-b-0">Your plan</p>
                                                    <h3 className="m-b-0">{Utils.getPlanName(_.get(organisation, 'subscription.plan')) ? Utils.getPlanName(_.get(organisation, 'subscription.plan')) : 'Free'}</h3>
                                                </div>
                                                <div>
                                                    {organisation.subscription && (
                                                        <a className="btn btn-primary mr-2" href="https://flagsmith.chargebeeportal.com/" target="_blank">
                                                            Manage Invoices
                                                        </a>
                                                    )}
                                                    { organisation.subscription ? (
                                                        <button
                                                          disabled={!this.state.manageSubscriptionLoaded}
                                                          type="button" className="btn btn-primary text-center ml-auto mt-2 mb-2"
                                                          onClick={() => {
                                                              if (this.state.chargebeeURL) {
                                                                  window.location = this.state.chargebeeURL;
                                                              } else {
                                                                  openModal('Payment plans', <PaymentModal
                                                                    viewOnly={false}
                                                                  />, null, { large: true });
                                                              }
                                                          }}
                                                        >
                                                            Manage payment plan
                                                        </button>
                                                    ) : (
                                                        <button
                                                          type="button" className="btn btn-primary text-center ml-auto mt-2 mb-2"
                                                          onClick={() => openModal('Payment Plans', <PaymentModal
                                                            viewOnly={false}
                                                          />, null, { large: true })}
                                                        >
                                                            View plans
                                                        </button>
                                                    ) }
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </FormGroup>
                            <FormGroup className="mt-5">
                                <div>
                                            <div>
                                                <Row space className="mt-5">
                                                    <h3 className="m-b-0">Team Members</h3>
                                                    <Button
                                                      style={{ width: 180 }}
                                                      id="btn-invite" onClick={() => openModal('Invite Users',
                                                          <InviteUsersModal/>)}
                                                      type="button"
                                                    >
                                                    Invite members
                                                    </Button>
                                                </Row>
                                                {paymentsEnabled && (
                                                    <p>
                                                        {'You are currently using '}
                                                        <strong className={organisation.num_seats > (_.get(organisation, 'subscription.max_seats') || 1) ? 'text-danger' : ''}>
                                                            {`${organisation.num_seats} of ${_.get(organisation, 'subscription.max_seats') || 1}`}
                                                        </strong>
                                                        {` seat${organisation.num_seats === 1 ? '' : 's'}. `} for your plan.
                                                        {' '}
                                                        {organisation.num_seats > (_.get(organisation, 'subscription.max_seats') || 1)
                                                        && (
                                                            <a
                                                              href="#" onClick={() => openModal('Payment Plans', <PaymentModal
                                                                viewOnly={false}
                                                              />, null, { large: true })}
                                                            >
                                                                Upgrade
                                                            </a>
                                                        )
                                                        }
                                                    </p>
                                                )}
                                                {
                                                     inviteLinks && (
                                                     <form onSubmit={(e) => {
                                                         e.preventDefault();
                                                     }}
                                                     >
                                                         <div className="mt-3">
                                                             <Row>
                                                                 <div className="mr-2" style={{ width: 280 }}>
                                                                     <Select
                                                                       value={{
                                                                           value: this.state.role,
                                                                           label: this.state.role === 'ADMIN' ? 'Organisation Administrator' : 'User',
                                                                       }}
                                                                       onChange={v => this.setState({ role: v.value })}
                                                                       options={[
                                                                           { label: 'Organisation Administrator', value: 'ADMIN' },
                                                                           { label: hasRbacPermission ? 'User' : 'User - Please upgrade for role based access',
                                                                               value: 'USER',
                                                                               isDisabled: !hasRbacPermission,
                                                                           },
                                                                       ]}
                                                                     />
                                                                 </div>
                                                                 {inviteLinks.find(f => f.role === this.state.role) && (
                                                                  <>
                                                                      <Flex className="mr-4">
                                                                          <Input
                                                                            style={{ width: '100%' }}
                                                                            value={`${document.location.origin}/invite/${inviteLinks.find(f => f.role === this.state.role).hash}`}
                                                                            data-test="invite-link"
                                                                            inputClassName="input input--wide"
                                                                            className="full-width"
                                                                            type="text"
                                                                            readonly="readonly"
                                                                            title={<h3>Link</h3>}
                                                                            placeholder="Link"
                                                                          />
                                                                      </Flex>

                                                                      <div>
                                                                          <Button
                                                                            style={{ width: 180 }}
                                                                            onClick={() => {
                                                                                navigator.clipboard.writeText(`${document.location.origin}/invite/${inviteLinks.find(f => f.role === this.state.role).hash}`);
                                                                                toast('Link copied');
                                                                            }}
                                                                          >
                                                                              Copy invite link
                                                                          </Button>
                                                                      </div>
                                                                  </>
                                                                 )}


                                                             </Row>

                                                         </div>
                                                         <p className="mt-3">
                                                              Anyone with link can join as a standard user, once they have joined you can edit their role from the team members panel.
                                                             {' '}
                                                             <ButtonLink target="_blank" href="https://docs.flagsmith.com/advanced-use/permissions">Learn about User Roles.</ButtonLink>
                                                         </p>
                                                         <div className="text-right mt-2">
                                                             {error && <Error error={error}/>}
                                                         </div>
                                                     </form>
                                                     )
                                                }
                                                <div>
                                                    {isLoading && <div className="centered-container"><Loader/></div>}
                                                    {!isLoading && (
                                                    <div>
                                                        <FormGroup>
                                                            <PanelSearch
                                                              id="org-members-list"
                                                              title="Members"
                                                              className="no-pad"
                                                              items={users}
                                                              itemHeight={65}
                                                              renderRow={(user, i) => {
                                                                  const { id, first_name, last_name, email, role } = user;
                                                                  const onEditClick = () => {
                                                                      if (role !== 'ADMIN') {
                                                                          this.editUserPermissions(user);
                                                                      }
                                                                  };
                                                                  return (
                                                                      <Row
                                                                        data-test={`user-${i}`}

                                                                        space className={'list-item clickable'} key={id}
                                                                      >
                                                                          <Flex onClick={onEditClick}>

                                                                              {`${first_name} ${last_name}`}


                                                                              {' '}
                                                                              {id == AccountStore.getUserId() && '(You)'}
                                                                              <div className="list-item-footer faint">
                                                                                  {email}
                                                                              </div>
                                                                          </Flex>
                                                                          <Row>
                                                                              <Column>
                                                                                  {organisation.role === 'ADMIN' && id !== AccountStore.getUserId() ? (
                                                                                      <div style={{ width: 250 }}>
                                                                                          <Select
                                                                                            data-test="select-role"
                                                                                            placeholder="Select a role"
                                                                                            styles={{ menuPortal: base => ({ ...base, zIndex: 9999 }) }}
                                                                                            value={role && { value: role, label: Constants.roles[role] }}
                                                                                            onChange={e => this.roleChanged(id, Utils.safeParseEventValue(e))}
                                                                                            className="pl-2"
                                                                                            options={_.map(Constants.roles, (label, value) => (
                                                                                                {
                                                                                                    value,
                                                                                                    label:
                                                                                                          value !== 'ADMIN' && !hasRbacPermission ? `${label} - Please upgrade for role based access` : label,
                                                                                                    isDisabled: value !== 'ADMIN' && !hasRbacPermission,
                                                                                                }
                                                                                            ))}
                                                                                            menuPortalTarget={document.body}
                                                                                            menuPosition="absolute"
                                                                                            menuPlacement="auto"
                                                                                          />
                                                                                      </div>
                                                                                  ) : (
                                                                                      <div className="pl-3 mr-2">{Constants.roles[role] || ''}</div>
                                                                                  )}
                                                                              </Column>

                                                                              {role !== 'ADMIN' && (
                                                                                  <Column onClick={onEditClick}>
                                                                                      <Button className="btn--link">Edit Permissions</Button>
                                                                                  </Column>
                                                                              )}
                                                                              <Column>
                                                                                  <button
                                                                                    id="delete-invite"
                                                                                    type="button"
                                                                                    onClick={() => this.deleteUser(id)}
                                                                                    className="btn btn--with-icon ml-auto btn--remove"
                                                                                  >
                                                                                      <RemoveIcon/>
                                                                                  </button>
                                                                              </Column>
                                                                          </Row>
                                                                      </Row>
                                                                  );
                                                              }}
                                                              renderNoResults={(
                                                                  <div>
                                                                  You have no users in this organisation.
                                                                  </div>
                                                              )}
                                                              filterRow={(item, search) => {
                                                                  const strToSearch = `${item.first_name} ${item.last_name} ${item.email}`;
                                                                  return strToSearch.toLowerCase().indexOf(search.toLowerCase()) !== -1;
                                                              }}
                                                            />
                                                            <div id="select-portal" />
                                                        </FormGroup>

                                                        {invites && invites.length ? (
                                                            <FormGroup className="margin-top">
                                                                <PanelSearch
                                                                  itemHeight={70}
                                                                  id="org-invites-list"
                                                                  title="Invites Pending"
                                                                  className="no-pad"
                                                                  items={invites}
                                                                  renderRow={({ id, email, date_created, invited_by, link }, i) => (
                                                                      <Row
                                                                        data-test={`pending-invite-${i}`}
                                                                        className="list-item" key={id}
                                                                      >
                                                                          <div className="flex flex-1">
                                                                              {email || link}
                                                                              <div className="list-item-footer faint">
                                                                                    Created
                                                                                  {' '}
                                                                                  {moment(date_created).format('DD/MMM/YYYY')}
                                                                              </div>
                                                                              {invited_by ? (
                                                                                  <div
                                                                                    className="list-item-footer faint"
                                                                                  >
                                                                                        Invited by
                                                                                      {' '}
                                                                                      {invited_by.first_name ? `${invited_by.first_name} ${invited_by.last_name}` : invited_by.email}
                                                                                  </div>
                                                                              ) : null}
                                                                          </div>
                                                                          <Row>
                                                                              <Column>
                                                                                  {link ? ' '
                                                                                      : (
                                                                                          <button
                                                                                            id="resend-invite"
                                                                                            type="button"
                                                                                            onClick={() => AppActions.resendInvite(id)}
                                                                                            className="btn btn--anchor"
                                                                                          >
                                                                                      Resend
                                                                                          </button>
                                                                                      )
                                                                                  }
                                                                              </Column>
                                                                              <Column>
                                                                                  <button
                                                                                    id="delete-invite"
                                                                                    type="button"
                                                                                    onClick={() => this.deleteInvite(id)}
                                                                                    className="btn btn--with-icon ml-auto btn--remove"
                                                                                  >
                                                                                      <RemoveIcon/>
                                                                                  </button>
                                                                              </Column>
                                                                          </Row>
                                                                      </Row>
                                                                  )}
                                                                  filterRow={(item, search) => item.email.toLowerCase().indexOf(search.toLowerCase()) !== -1}
                                                                />
                                                            </FormGroup>
                                                        ) : null}

                                                        <div>
                                                            <Row space className="mt-5">
                                                                <h3 className="m-b-0">User Groups</h3>
                                                                <Button
                                                                  className="mr-2"
                                                                  id="btn-invite" onClick={() => openModal('Create Group',
                                                                      <CreateGroupModal orgId={organisation.id}/>)}
                                                                  type="button"
                                                                >
                                                                  Create Group
                                                                </Button>
                                                            </Row>
                                                            <p>Groups allow you to manage permissions for viewing and editing projects, features and environments.</p>
                                                            <UserGroupList
                                                              onEditPermissions={
                                                                this.editGroupPermissions
                                                            } showRemove orgId={organisation && organisation.id}
                                                            />
                                                        </div>

                                                        {Utils.getFlagsmithHasFeature('force_2fa') && (
                                                            <div>
                                                                <Row space className="mt-5">
                                                                    <h3 className="m-b-0">Enforce 2FA</h3>
                                                                    {!force2faPermission ? (
                                                                        <Tooltip title={<Switch checked={organisation.force_2fa} onChange={this.save2FA}/>}>
                                                                            To access this feature please upgrade your account to scaleup or higher."
                                                                        </Tooltip>
                                                                    ) : (
                                                                        <Switch checked={organisation.force_2fa} onChange={this.save2FA}/>
                                                                    )}
                                                                </Row>
                                                                <p>Enabling this setting forces users within the organisation to setup 2 factor security.</p>
                                                            </div>

                                                        )}
                                                    </div>
                                                    )}
                                                </div>
                                            </div>
                                </div>
                            </FormGroup>
                            <FormGroup className="m-y-3">
                                <Row className="mb-3" space>
                                    <h3 className="m-b-0">Audit Webhooks</h3>
                                    <Button onClick={this.createWebhook}>
                                    Create audit webhook
                                    </Button>
                                </Row>
                                <p>
                                Audit webhooks let you know when audit logs occur, you can configure 1 or more audit webhooks per organisation.
                                    {' '}
                                    <ButtonLink href="https://docs.flagsmith.com/advanced-use/system-administration#audit-log-webhooks/">Learn about Audit Webhooks.</ButtonLink>
                                </p>
                                {webhooksLoading && !webhooks ? (
                                    <Loader/>
                                ) : (
                                    <PanelSearch
                                      id="webhook-list"
                                      title={(
                                          <Tooltip
                                            title={<h6 className="mb-0">Webhooks <span className="icon ion-ios-information-circle"/></h6>}
                                            place="right"
                                          >
                                              {Constants.strings.WEBHOOKS_DESCRIPTION}
                                          </Tooltip>
                                    )}
                                      className="no-pad"
                                      icon="ion-md-cloud"
                                      items={webhooks}
                                      renderRow={webhook => (
                                          <Row
                                            onClick={() => {
                                                this.editWebhook(webhook);
                                            }} space className="list-item clickable cursor-pointer"
                                            key={webhook.id}
                                          >
                                              <div>
                                                  <ButtonLink>
                                                      {webhook.url}
                                                  </ButtonLink>
                                                  <div className="list-item-footer faint">
                                                Created
                                                      {' '}
                                                      {moment(webhook.created_date).format('DD/MMM/YYYY')}
                                                  </div>
                                              </div>
                                              <Row>
                                                  <Switch checked={webhook.enabled}/>
                                                  <button
                                                    id="delete-invite"
                                                    type="button"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        e.preventDefault();
                                                        this.deleteWebhook(webhook);
                                                    }}
                                                    className="btn btn--with-icon ml-auto btn--remove"
                                                  >
                                                      <RemoveIcon/>
                                                  </button>
                                              </Row>
                                          </Row>
                                      )}
                                      renderNoResults={(
                                          <Panel
                                            id="users-list"
                                            icon="ion-md-cloud"
                                            title={(
                                                <Tooltip
                                                  title={<h6 className="mb-0">Webhooks <span className="icon ion-ios-information-circle"/></h6>}
                                                  place="right"
                                                >
                                                    {Constants.strings.AUDIT_WEBHOOKS_DESCRIPTION}
                                                </Tooltip>
                                    )}
                                          >
                                    You currently have no webhooks configured for this organisation.
                                          </Panel>
                                )}
                                      isLoading={this.props.webhookLoading}
                                    />
                                )}
                            </FormGroup>
                            {Utils.getFlagsmithHasFeature('restrict_project_create_to_admin') && (
                                <FormGroup className="mt-5">
                                    <Row>
                                        <Column>
                                            <h3>Admin Settings</h3>
                                            <Row>
                                                Only allow organisation admins to create projects
                                                <Switch
                                                  checked={organisation.restrict_project_create_to_admin} onChange={() => this.setAdminCanCreateProject(!organisation.restrict_project_create_to_admin)}
                                                />
                                            </Row>
                                        </Column>
                                    </Row>

                                </FormGroup>
                            )}
                            {Utils.getFlagsmithHasFeature('usage_chart') && !projectOverrides.disableInflux && (
                                <div className="panel--grey mt-2">
                                    {!isLoading && usage != null ? (
                                        <div>
                                            {Utils.getFlagsmithHasFeature('usage_chart') ? this.drawChart(influx_data) : (
                                                <>
                                                    <div className="flex-row header--icon">
                                                        <h5>API usage</h5>
                                                    </div>
                                                    <span>
                                                        {'You have made '}
                                                        <strong>{`${Utils.numberWithCommas(usage)}`}</strong>
                                                        {' requests over the past 30 days.'}
                                                    </span>
                                                </>
                                            )}
                                        </div>
                                    ) : <div className="text-center"><Loader/></div> }
                                </div>
                            )}
                            <FormGroup className="mt-5">
                                <Row>
                                    <Column>
                                        <h3>Delete Organisation</h3>
                                        <p>
                                        This organisation will be  permanently deleted, along with all projects and features.
                                        </p>
                                    </Column>
                                    <Button
                                      id="delete-org-btn"
                                      onClick={() => this.confirmRemove(organisation, () => {
                                          deleteOrganisation();
                                      })}
                                      className="btn btn--with-icon ml-auto btn--remove"
                                    >
                                        <RemoveIcon/>
                                    </Button>
                                </Row>
                            </FormGroup>
                        </div>
                            )}
                        </OrganisationProvider>
                    )}
                </AccountProvider>
            </div>
        );
    }
};

OrganisationSettingsPage.propTypes = {};

module.exports = ConfigProvider(withAuditWebhooks(OrganisationSettingsPage));
