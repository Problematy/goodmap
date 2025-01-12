export function fakeLocation(latitude, longitude) {
    return {
        onBeforeLoad(win) {
            cy.stub(win.navigator.geolocation, 'getCurrentPosition', (cb, err) => {
                if (latitude && longitude) {
                    return cb({ coords: { latitude, longitude } });
                }
                throw err({ code: 1 });
            });
        },
    };
}
