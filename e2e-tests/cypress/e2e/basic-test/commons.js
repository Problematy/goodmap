export const expectedPlaceZwierzyniecka = {
    title: 'Zwierzyniecka',
    subtitle: 'small bridge',
    categories: [
        ['type_of_place', 'small bridge'],
        ['accessible_by', 'bikes, pedestrians'],
    ],
};

// This is workaround for a problem with getting specific marker.
// TODO Find a way of getting specific marker or marker in specific position
export function getRightmostMarker(markers) {
    let rightmostMarker;
    let maxX = -Infinity;

    Cypress.$(markers).each((index, marker) => {
        const rect = marker.getBoundingClientRect();
        if (rect.x > maxX) {
            maxX = rect.x;
            rightmostMarker = marker;
        }
    });
    return rightmostMarker;
}

export function verifyPopupContent(expectedContent) {
    cy.get('.point-title').should('have.text', expectedContent.title);

    cy.get('.point-subtitle').should('have.text', expectedContent.subtitle);

    expectedContent.categories.forEach(([category, value]) => {
        cy.contains(category).should('exist');
        cy.contains(value).should('exist');
    });

    if (expectedContent.CTA) {
        cy.contains(expectedContent.CTA.displayValue).should('exist');
        cy.contains('button', expectedContent.CTA.displayValue).click();
        cy.get('@openStub').should('have.been.calledOnceWith', expectedContent.CTA.value, '_blank');
    }
}

export function verifyProblemForm() {
    cy.contains('report a problem').should('exist').click();
    cy.intercept('POST', '/api/report-location').as('reportLocation');

    cy.get('form')
        .should('exist')
        .within(() => {
            cy.get('select')
                .should('exist')
                .within(() => {
                    cy.get('option').then(options => {
                        const optionValues = [...options].map(option => option.textContent.trim());
                        expect(optionValues).to.include.members([
                            '--Please choose an option--',
                            'this point is not here',
                            "it's overloaded",
                            "it's broken",
                            'other',
                        ]);
                    });
                });

            cy.get('select').select('other');
            cy.get('input[name="problem"]').should('exist');
            cy.get('input[name="problem"]').type('Custom issue description');
            cy.get('input[type="submit"]').should('exist').click();
        });

    cy.wait('@reportLocation').then(interception => {
        expect(interception.request.body).to.have.property('id');
        expect(interception.request.body).to.have.property('description');
        expect(interception.request.body.description).to.equal('Custom issue description');
        expect(interception.response.statusCode).to.equal(200);
        expect(interception.response.body.message).to.equal('Location reported');
    });

    cy.contains('p', 'Location reported').should('exist');
    cy.get('form').should('not.exist');
}
