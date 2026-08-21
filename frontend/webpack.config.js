const path = require('node:path');
const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');
const { ModuleFederationPlugin } = require('webpack').container;
const deps = require('./package.json').dependencies;

module.exports = (env, argv) => {
    const IS_PROD = argv.mode === 'production';
    const runOnAllInterfaces = env && env.serve === 'network';

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
                    exclude: /@phosphor-icons\/core/,
                    loader: 'url-loader',
                    options: {
                        limit: 8192,
                        name: '[path][name].[ext]',
                    },
                },
                {
                    // @phosphor-icons/core's full icon set is pulled in via
                    // require.context (see resolvePhosphorIconUrl.js) so any icon
                    // can be referenced by name from deployment config, without a
                    // frontend code change - never inline these (limit: 0), or that
                    // whole set would bloat the main JS bundle instead of staying as
                    // separate files fetched only for icons actually rendered.
                    test: /@phosphor-icons\/core.*\.svg$/i,
                    loader: 'url-loader',
                    options: {
                        limit: 0,
                        name: 'phosphor-icons/[name].[ext]',
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
