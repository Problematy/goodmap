import {
    verifyPopupContent,
    verifyProblemForm,
    expectedPlaceZwierzyniecka,
    getRightmostMarker,
} from './commons.js';

describe('Popup Tests on Mobile', () => {
    const viewports = ['iphone-x', 'iphone-6', 'ipad-2', 'samsung-s10'];

    viewports.forEach(viewport => {
        it(`displays title and subtitle in the popup on ${viewport}`, () => {
            cy.on('window:before:load', win => {
                Object.defineProperty(win.navigator, 'userAgent', {
                    value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
                });
            });
            cy.viewport(viewport);
            cy.visit('/');

            cy.window().then(win => {
                cy.stub(win, 'open').as('openStub');
            });

            cy.get('.leaflet-marker-icon').click();
            cy.get('.leaflet-marker-icon').should('have.length', 2);

            cy.get('.leaflet-marker-icon').then(markers => {
                const rightmostMarker = getRightmostMarker(markers);
                cy.wrap(rightmostMarker).click();
            });

            // TODO: Remove .MuiDialogContent-root selector after goodmap-frontend unifies popup behavior
            cy.get('.MuiDialogContent-root, .leaflet-popup-content')
                .should('exist')
                .within(() => {
                    verifyPopupContent(expectedPlaceZwierzyniecka);
                    verifyProblemForm();
                });
            // TODO: Remove .MuiIconButton-root selector after goodmap-frontend unifies popup behavior
            cy.get('.MuiIconButton-root, .leaflet-popup-close-button').should('exist').click();
        });
    });
});
