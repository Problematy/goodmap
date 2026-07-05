const path = require('node:path');
const { ModuleFederationPlugin } = require('webpack').container;

// A goodmap frontend plugin is a Module Federation *remote*. This config mirrors the host
// (goodmap's own webpack.config.js): one container, React shared as a singleton, and one
// exposed module per capability the plugin provides.
module.exports = {
    entry: './src/index.js',
    mode: 'production',
    output: {
        // Build into the Python package's `static/` dir. goodmap serves it at
        // /plugins/silly_gif/static/remoteEntry.js and points the manifest there.
        path: path.resolve(__dirname, '..', 'silly_gif', 'static'),
        publicPath: 'auto',
        clean: true,
    },
    resolve: { extensions: ['.js', '.jsx'] },
    module: {
        rules: [{ test: /\.jsx?$/, exclude: /node_modules/, use: 'babel-loader' }],
    },
    plugins: [
        new ModuleFederationPlugin({
            // MUST equal the plugin's entry-point name — it is the global container the
            // goodmap host looks up as window['silly_gif'].
            name: 'silly_gif',
            filename: 'remoteEntry.js',
            // One expose per capability, keyed by the module goodmap derives from the
            // capability base name (MapOverlayPluginBase -> "./MapOverlay", etc.).
            exposes: {
                './MapOverlay': './src/MapOverlay',
                './MarkerField': './src/MarkerField',
            },
            // Borrow the host's single React instance so hooks work across the boundary.
            shared: {
                react: { singleton: true, requiredVersion: false },
                'react-dom': { singleton: true, requiredVersion: false },
            },
        }),
    ],
};
