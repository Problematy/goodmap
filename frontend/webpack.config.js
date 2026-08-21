const path = require('node:path');
const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');
const { ModuleFederationPlugin } = require('webpack').container;
const deps = require('./package.json').dependencies;

module.exports = (env, argv) => {
    const IS_PROD = argv.mode === 'production';
    const runOnAllInterfaces = env?.serve === 'network';

    return {
        plugins: [
            new ModuleFederationPlugin({
                name: 'goodmap',
                remotes: {},
                shared: {
                    react: { singleton: true, eager: true, requiredVersion: deps.react },
                    'react-dom': { singleton: true, eager: true, requiredVersion: deps['react-dom'] },
                },
            }),
        ],
        cache: {
            type: 'filesystem',
            // webpack-dev-server (serve:local/serve:prod/serve:network, all pass
            // --env serve=...) injects HMR machinery into its build even under
            // --mode production - sharing a cache namespace with the plain `build`
            // script (same mode, no --env) corrupts it: a later plain build can hit
            // dev-server-only constructs (e.g. HarmonyAcceptDependency) it doesn't
            // know how to handle, crashing with "Invalid value used as weak map
            // key". Keying the cache name off env.serve keeps the two fully apart.
            name: env?.serve ? 'dev-server' : 'build',
            cacheDirectory: path.resolve(__dirname, '.webpack-cache'),
            buildDependencies: {
                config: [__filename],
            },
        },
        devtool: 'source-map',
        entry: './src/index.js',
        output: {
            path: process.env.OUTPUT_DIR
                ? path.resolve(__dirname, process.env.OUTPUT_DIR)
                : `${__dirname}/dist`,
            filename: IS_PROD ? 'index.min.js' : 'index.js',
        },
        resolve: {
            extensions: ['.js', '.jsx', '.css'],
        },
        optimization: {
            minimize: IS_PROD,
            minimizer: [new TerserPlugin({ parallel: true })],
        },
        module: {
            rules: [
                {
                    test: /\.(js|jsx)$/,
                    loader: 'babel-loader',
                    exclude: /node_modules/,
                },
                {
                    test: /\.css$/,
                    use: ['style-loader', 'css-loader'],
                },
                {
                    test: /\.(jpe?g|png|gif|woff|woff2|eot|ttf|svg)$/i,
                    loader: 'url-loader',
                    options: {
                        limit: 8192,
                        name: '[path][name].[ext]',
                    },
                },
            ],
        },
        devServer: {
            host: runOnAllInterfaces ? '0.0.0.0' : 'localhost',
            port: 8080,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
                'Access-Control-Allow-Headers': 'X-Requested-With, content-type, Authorization',
            },
            allowedHosts: runOnAllInterfaces ? 'all' : 'localhost',
        },
    };
};
