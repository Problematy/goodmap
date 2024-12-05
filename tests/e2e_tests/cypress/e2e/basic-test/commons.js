const expectedPlace1 = {
  title: "Grunwaldzki",
  subtitle: "big bridge",
  categories: [
    ["type_of_place", "big bridge"],
    ["accessible_by", "pedestrians, cars"]
  ],
  CTA: {
    "type": "CTA",
    "value": "https://www.example.com",
    "displayValue": "Visit example.org!"
  }
};
const expectedPlace2 = {
  title: "Zwierzyniecka",
  subtitle: "small bridge",
  categories: [
    ["type_of_place", "small bridge"],
    ["accessible_by", "bikes, pedestrians"]
  ]
};

export const expectedPlaces = [expectedPlace1, expectedPlace2];

// TODO - Find a way to search for a specific point, not iterate over all of them
export function verifyArbitraryPopupContent(expectedPlaces) {
  cy.get('.point-title').should('exist').invoke('text')
    .then((title) => {
      const expectedPlace1 = expectedPlaces[0];
      const expectedPlace2 = expectedPlaces[1];
      if (title === expectedPlace1.title) {
        verifyPopupContent(expectedPlace1);
      } else if (title === expectedPlace2.title) {
        verifyPopupContent(expectedPlace2);
      }
    });
}

function verifyPopupContent(expectedContent) {
  cy.get('.point-subtitle')
    .should('have.text', expectedContent.subtitle);

  expectedContent.categories.forEach(([category, value]) => {
    cy.contains(category).should('exist');
    cy.contains(value).should('exist');
  });

  if (expectedContent.CTA) {
    cy.contains(expectedContent.CTA.displayValue).should('exist');
    cy.contains('button', expectedContent.CTA.displayValue).click();
    cy.get('@openStub').should('have.been.calledOnceWith',
      expectedContent.CTA.value, '_blank');
  }
}

export function verifyProblemForm() {
  cy.contains('report a problem').should('exist').click();
  cy.intercept('POST', '/api/report-location').as('reportLocation');

  cy.get('form').should('exist').within(() => {
    cy.get('select').should('exist').within(() => {
      cy.get('option').then((options) => {
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

  cy.wait('@reportLocation').then((interception) => {
    expect(interception.request.body).to.have.property('id');
    expect(interception.request.body).to.have.property('description');
    expect(interception.request.body.description).to.equal('Custom issue description');
    expect(interception.response.statusCode).to.equal(200);
    expect(interception.response.body.message).to.equal('Location reported');
  });

  cy.contains('p', 'Location reported').should('exist');
  cy.get('form').should('not.exist');
}
