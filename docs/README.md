# Website

This website is built using [Docusaurus 2](https://docusaurus.io/), a modern static website generator.

## Installation

```console
npm install
```

## Local Development

```console
npm run start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without
having to restart the server.

When forwarding port 3000 from a remote server or VM, you can run the dev server on 0.0.0.0 to make it listen on the
local IP.

```console
npm run start -- --host 0.0.0.0
```

### Checking your changes with prettier

After you make changes to the documentation, you can check the changes by running the following command:

```console
npx prettier --check docs
```

If you want to apply any fixes discovered, you can run the following command:

```console
npx prettier <YOUR_DOC> --write
```

## OpenAPI generator

We are using the https://github.com/PaloAltoNetworks/docusaurus-openapi-docs plugin to generate the OpenAPI docs. If
`static/api-static/edge-api.yaml` changes you will need to rebuild the static files with:

```bash
npm run docusaurus clean-api-docs all
npm run docusaurus gen-api-docs all
```

and then commit them.

## Build

```console
npm run build
```

This command generates static content into the `build` directory and can be served using any static contents hosting
service.

## Deployment

This site is set to auto deploy to Vercel.
