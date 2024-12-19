describe('Tests the behavior of go-to-my-location button', () => {
    it('go-to-my-location takes user to their location', () => {
        cy.visit('/', {
            onBeforeLoad (win) {
                // e.g., force Barcelona geolocation
                const latitude = 41.38879;
                const longitude = 2.15899;
                cy.stub(win.navigator.geolocation, 'getCurrentPosition').callsFake((cb) => {
                    return cb({ coords: { latitude, longitude } });
                });
            },
        });

        cy.get('.leaflet-marker-icon').click();


//        cy.get(['button[aria-label="centerButtonAriaLabel"]']).should('exist').click();
//        cy.get('button[data-testid=MyLocationIcon]').should('exist').click();
        cy.get('[data-testid=MyLocationIcon]').should('exist').click();
        cy.wait(4000);
    });
});
