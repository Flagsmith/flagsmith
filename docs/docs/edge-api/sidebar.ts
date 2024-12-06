import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebar: SidebarsConfig = {
    apisidebar: [
        {
            type: 'doc',
            id: 'edge-api/edge-api',
        },
        {
            type: 'category',
            label: 'Edge API',
            items: [
                {
                    type: 'doc',
                    id: 'edge-api/get-flags',
                    label: 'Get flags',
                    className: 'api-method get',
                },
                {
                    type: 'doc',
                    id: 'edge-api/get-identity-flags-and-traits',
                    label: 'Get identity flags and traits',
                    className: 'api-method get',
                },
                {
                    type: 'doc',
                    id: 'edge-api/identify-user',
                    label: 'Identify user',
                    className: 'api-method post',
                },
                {
                    type: 'doc',
                    id: 'edge-api/bulk-insert-identities-overwrite',
                    label: 'Bulk insert identities (overwrite)',
                    className: 'api-method post',
                },
                {
                    type: 'doc',
                    id: 'edge-api/bulk-insert-identities-update',
                    label: 'Bulk insert identities (update)',
                    className: 'api-method put',
                },
            ],
        },
    ],
};

export default sidebar.apisidebar;
