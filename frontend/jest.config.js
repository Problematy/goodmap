const config = {
    verbose: true,
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
    collectCoverageFrom: ['src/components/**/*.jsx'],
transformIgnorePatterns: [
    'node_modules/(?!(react-leaflet|@react-leaflet/core|react-leaflet-custom-control)/)',
],
    moduleNameMapper: {
        '\\.(css|less)$': '<rootDir>/__mocks__/styleMock.js',
        '\\.(png|jpg|jpeg|gif|svg)$': '<rootDir>/__mocks__/fileMock.js',
    },
};

module.exports = config;
