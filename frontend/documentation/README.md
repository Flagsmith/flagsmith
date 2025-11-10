# Component Documentation

This directory contains Storybook stories and documentation for our components.

## Structure

```
documentation/
└── components/           # Component stories organized by component
    └── multi-select/
        └── MultiSelect.stories.tsx
```

## Adding New Component Stories

To add stories for a new component:

1. Create a new directory under `components/` with the component name
2. Add a `.stories.tsx` file (e.g., `ComponentName.stories.tsx`)
3. The stories will automatically be picked up by Storybook

## Running Storybook

```bash
npm run storybook
```

This will start the Storybook dev server at `http://localhost:6006/`

## Building Storybook

```bash
npm run build-storybook
```

This will create a static build of the Storybook in the `storybook-static` directory.
