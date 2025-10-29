export function fakeLocation(latitude, longitude) {
    return {
        onBeforeLoad(win) {
            // Stub permissions API to always grant geolocation
            const permissionsQuery = win.navigator.permissions.query;
            cy.stub(win.navigator.permissions, 'query').callsFake((parameters) => {
                if (parameters.name === 'geolocation') {
                    return Promise.resolve({ state: 'granted' });
                }
                return permissionsQuery.call(win.navigator.permissions, parameters);
            });

            // Stub geolocation API
            cy.stub(win.navigator.geolocation, 'getCurrentPosition').callsFake((success, error) => {
                if (latitude && longitude) {
                    return success({ coords: { latitude, longitude, accuracy: 50 } });
                }
                if (error) {
                    return error({ code: 1 });
                }
            });
        },
    };
}
