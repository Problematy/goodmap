module.exports = {
    setupFiles: ['<rootDir>/src/i18n'],
    verbose: true,
    testEnvironment: 'jsdom',
    coverageProvider: 'v8',
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
    collectCoverageFrom: ['src/components/**/*.jsx'],
    coverageThreshold: {
        global: {
            statements: 85,
            branches: 70,
            functions: 60,
            lines: 85,
        },
    },
    transform: {
        '^.+\\.(js|jsx)$': 'babel-jest',
    },
    transformIgnorePatterns: [
        'node_modules/(?!(react-leaflet|@react-leaflet/core|react-leaflet-custom-control|react-leaflet-cluster|uuid)/)',
    ],
    moduleNameMapper: {
        '\\.(css|less)$': '<rootDir>/__mocks__/styleMock.js',
        '\\.(png|jpg|jpeg|gif|svg)$': '<rootDir>/__mocks__/fileMock.js',
        'resolvePhosphorIconUrl$': '<rootDir>/__mocks__/resolvePhosphorIconUrlMock.js',
    },
};
