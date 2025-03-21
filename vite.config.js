import { defineConfig, loadEnv } from 'vite';
import { resolve, join } from 'path';
import { rmSync } from 'fs';
import postcssImportExtGlob from 'postcss-import-ext-glob';
import postcssImport from 'postcss-import';
import postcssAdvancedVariables from 'postcss-advanced-variables';
import autoprefixer from 'autoprefixer';
import postcssSassyMixins from 'postcss-sassy-mixins';
import postcssNested from 'postcss-nested';
import postcssPxToRem from 'postcss-pxtorem';

const assetsDir = 'csgomatches/frontend';

const postcssConfig = {
	plugins: [
		postcssImportExtGlob,
		postcssImport,
		postcssNested,
		postcssSassyMixins,
		postcssAdvancedVariables,
		postcssPxToRem({
			unitPrecision: 3,
			selectorBlackList: ['body'],
		}),
		autoprefixer,
	],
};

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
		css: {
			postcss: postcssConfig,
		},
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
