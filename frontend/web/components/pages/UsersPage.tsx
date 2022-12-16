import React, {Component, useEffect, FC, useState} from 'react';
import {RouterChildContext} from "react-router";
import {Link} from "react-router-dom";

const Permission = require("common/providers/Permission")
const AccountStore = require("common/stores/account-store")
import {PermissionCallback} from "common/types";
import Constants from 'common/constants';
import {useDeleteIdentityMutation, useGetIdentitiesQuery} from "common/services/useIdentity";
import useSearchThrottle from "common/useSearchThrottle";
import {Req} from "common/types/requests";
import {Identity} from "common/types/responses";

import CreateUserModal from '../modals/CreateUser';
import RemoveIcon from '../RemoveIcon';
const PanelSearch = require('../PanelSearch');
import Button, {ButtonLink} from "../base/forms/Button"; // we need this to make JSX compile

type UsersPageType = {
    router: RouterChildContext['router']
    match: {
        params: {
            environmentId: string
            projectId: string
        }
    }
}

const Utils = require("common/utils/utils")
const UsersPage: FC<UsersPageType> = (props) => {
    const [page, setPage] = useState<{
        number:number,
        pages:Req['getIdentities']['pages']
    }>({number:1, pages:undefined});

    const {searchInput, search, setSearchInput} = useSearchThrottle(Utils.fromParam().search, () => {
        setPage({
            number: 1,
            pages: undefined
        });
    });
    const [deleteIdentity] = useDeleteIdentityMutation({})
    const isEdge = Utils.getIsEdge();

    const { data:identities, isLoading } = useGetIdentitiesQuery({
        pages: page.pages,
        page: page.number,
        page_size: 10,
        environmentId:props.match.params.environmentId,
        isEdge
    })

    const { projectId, environmentId } = props.match.params;
    const preventAddTrait = !AccountStore.getOrganisation().persist_trait_data;

    const onSave = () => {
        toast('Environment Saved');
    };

    const removeIdentity = (id:string, identifier:string) => {
        openConfirm(
            <h3>Delete User</h3>,
            <p>
                {'Are you sure you want to delete '}
                <strong>{identifier}</strong>
                {'?'}
            </p>,
            () => deleteIdentity({environmentId, isEdge:Utils.getIsEdge(), id}),
        );
    }

    const newUser = () => {
        openModal('New Users', <CreateUserModal
            environmentId={environmentId}
        />, null, { className: 'alert fade expand' });
    }

    return (
        <div className="app-container container">
            <Permission level="environment" permission={Utils.getManageFeaturePermission(false)} id={environmentId}>
                {({ permission }:PermissionCallback) => (
                    <div>
                        <div>
                            <Row>
                                <Flex>
                                    <div>
                                        <h3>Users</h3>
                                        <p>
                                            View and manage features states for individual users. This will override individual default
                                            feature settings for your selected environment.
                                            {' '}
                                            <ButtonLink target="_blank" href="https://docs.flagsmith.com/basic-features/managing-identities">Learn more.</ButtonLink>
                                        </p>
                                    </div>
                                </Flex>
                                {permission ? (
                                    <FormGroup className="float-right">
                                        <Button
                                            className="float-right" data-test="show-create-feature-btn" id="show-create-feature-btn"
                                            onClick={newUser}
                                        >
                                            Create Users
                                        </Button>
                                    </FormGroup>
                                ) : (
                                    <Tooltip
                                        html
                                        title={(
                                            <Button
                                                disabled data-test="show-create-feature-btn" id="show-create-feature-btn"
                                                onClick={newUser}
                                            >
                                                Create Users
                                            </Button>
                                        )}
                                        place="right"
                                    >
                                        {Constants.environmentPermissions('Admin')}
                                    </Tooltip>
                                )}
                            </Row>
                        </div>
                        <FormGroup>
                                    <div>
                                        <FormGroup>
                                            <PanelSearch
                                                renderSearchWithNoResults
                                                id="users-list"
                                                title="Users"
                                                className="no-pad"
                                                isLoading={isLoading}
                                                filterLabel={Utils.getIsEdge() ? 'Starts with' : 'Contains'}
                                                icon="ion-md-person"
                                                items={identities?.results}
                                                paging={identities}
                                                showExactFilter
                                                nextPage={() => {
                                                    setPage({
                                                        number:page.number-1,
                                                        pages: identities?.last_evaluated_key? (page.pages||[]).concat([identities?.last_evaluated_key]) : undefined
                                                    })
                                                }}
                                                prevPage={() => {
                                                    setPage({
                                                        number:page.number-1,
                                                        pages: page.pages? Utils.removeElementFromArray(page.pages, page.pages.length-1) : undefined
                                                    })
                                                }}
                                                goToPage={(newPage:number) => {
                                                    setPage({
                                                        number:newPage,
                                                        pages: page.pages? Utils.removeElementFromArray(page.pages, page.pages.length-1) : undefined
                                                    })
                                                }}
                                                renderRow={({ id, identifier }:Identity, index:number) => (permission ? (
                                                    <Row
                                                        space className="list-item clickable" key={id}
                                                        data-test={`user-item-${index}`}
                                                    >
                                                        <Flex>
                                                            <Link
                                                                to={`/project/${props.match.params.projectId}/environment/${props.match.params.environmentId}/users/${encodeURIComponent(identifier)}/${id}`}
                                                            >
                                                                <ButtonLink>
                                                                    {identifier}
                                                                    <span className="ion-ios-arrow-forward ml-3"/>
                                                                </ButtonLink>
                                                            </Link>
                                                        </Flex>
                                                        <Column>
                                                            <button
                                                                id="remove-feature"
                                                                className="btn btn--with-icon"
                                                                type="button"
                                                                onClick={() => removeIdentity(id, identifier)}
                                                            >
                                                                <RemoveIcon/>
                                                            </button>
                                                        </Column>
                                                    </Row>
                                                ) : (
                                                    <Row
                                                        space className="list-item" key={id}
                                                        data-test={`user-item-${index}`}
                                                    >
                                                        {identifier}
                                                    </Row>
                                                ))}
                                                renderNoResults={(
                                                    <div>
                                                        You have no users in your project{search ? <span> for <strong>"{search}"</strong></span> : ''}.
                                                    </div>
                                                )}
                                                filterRow={() => true}
                                                search={searchInput}
                                                onChange={(e:InputEvent) => {
                                                    setSearchInput(Utils.safeParseEventValue(e))
                                                }}
                                            />
                                        </FormGroup>
                                        <FormGroup>
                                            <p className="faint mt-4">
                                                Users are created for your environment automatically when calling
                                                identify/get flags
                                                from any of the SDKs.
                                                <br/>
                                                We've created
                                                {' '}
                                                <strong>user_123456</strong>
                                                {' '}
                                                for you so you always have an example user to
                                                test with on your environments.
                                            </p>
                                            <div className="row">
                                                <div className="col-md-12">
                                                    <CodeHelp
                                                        showInitially
                                                        title="Creating users and getting their feature settings"
                                                        snippets={Constants.codeHelp.CREATE_USER(props.match.params.environmentId, identities && identities[0] && identities[0].identifier)}
                                                    />
                                                </div>
                                            </div>

                                        </FormGroup>
                                    </div>
                        </FormGroup>
                    </div>
                )}
            </Permission>
        </div>
    )
}

export default ConfigProvider(UsersPage)
