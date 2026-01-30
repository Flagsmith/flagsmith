import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebar: SidebarsConfig = {
  apisidebar: [
    {
      type: "doc",
      id: "edge-api/flagsmith-api",
    },
    {
      type: "category",
      label: "sdk",
      items: [
        {
          type: "doc",
          id: "edge-api/sdk-v-1-environment-document",
          label: "sdk_v1_environment_document",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "edge-api/sdk-v-1-flags",
          label: "sdk_v1_flags",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "edge-api/sdk-v-1-get-identities",
          label: "sdk_v1_get_identities",
          className: "api-method get",
        },
        {
          type: "doc",
          id: "edge-api/sdk-v-1-post-identities",
          label: "sdk_v1_post_identities",
          className: "api-method post",
        },
      ],
    },
  ],
};

export default sidebar.apisidebar;
