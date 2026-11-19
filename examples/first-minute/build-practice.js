import { build } from 'vite';
import { mkdir, writeFile } from 'node:fs/promises';

// Package the practice desk for judges who want to open it directly from a file.
const bundle = await build({ mode: 'practice', build: { write: false } });
const html = bundle.output.find((file) => file.fileName === 'index.html').source;
const script = bundle.output.find((file) => file.type === 'chunk' && file.isEntry).code;
const css = bundle.output.find((file) => file.fileName.endsWith('.css')).source;
const document = html
    .replace(
        /<script type="module"[^>]*src="[^"]+"[^>]*><\/script>/,
        () => '<script type="module">' + script.replace(/<\/script/gi, '<\\/script') + '</script>',
    )
    .replace(/<link rel="stylesheet"[^>]*>/, () => '<style>' + css + '</style>');
await mkdir('dist', { recursive: true });
await writeFile('dist/first-minute.html', document);
