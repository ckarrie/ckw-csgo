import { defineConfig, loadEnv } from 'vite';
import { resolve, join } from 'path';
import { rmSync } from 'fs';

const assetsDir = 'csgomatches/frontend';

const plugins = [
	{
		name: 'clean-assets-folder',
		buildStart() {
			const assetsPath = resolve(
				__dirname,
				'csgomatches/static',
				assetsDir
			);
			rmSync(assetsPath, { recursive: true, force: true });
		},
	},
];

export default defineConfig(mode => {
	const env = loadEnv(mode, process.cwd(), '');

	const INPUT_DIR = './src';
	const OUTPUT_DIR = './../ckw-csgo/csgomatches/static';

	return {
		plugins,
		resolve: {
			alias: {
				'@': resolve(INPUT_DIR),
			},
		},
		root: resolve(INPUT_DIR),
		base: '/static/',
		css: {},
		server: {
			host: env.DJANGO_VITE_DEV_SERVER_HOST,
			port: env.DJANGO_VITE_DEV_SERVER_PORT,
		},
		build: {
			manifest: 'manifest.json',
			emptyOutDir: false,
			outDir: resolve(OUTPUT_DIR),
			assetsDir,
			rollupOptions: {
				input: {
					css: join(INPUT_DIR, '/entry.js'),
				},
			},
		},
	};
});
