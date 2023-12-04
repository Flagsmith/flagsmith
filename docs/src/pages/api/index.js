import { RedocStandalone } from 'redoc';
import React from 'react';
import Layout from '@theme/Layout';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';

export default function Redoc() {
    const { siteConfig } = useDocusaurusContext();
    return (
        <Layout title="Relay proxy endpoints documentation">
            <div>
                <RedocStandalone
                    specUrl={siteConfig.customFields.swaggerURL}
                    options={{
                        hideHostname: true,
                        disableSearch: true,
                        nativeScrollbars: false,
                        pathInMiddlePanel: true,
                        jsonSampleExpandLevel: 5,
                    }}
                />
            </div>
        </Layout>
    );
}
