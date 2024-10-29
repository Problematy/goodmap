describe('Popup Tests', () => {
  beforeEach(() => {
    cy.visit('/');
    cy.wait(3000);
  })
  const expectedPlace1 = {
    title: "Grunwaldzki",
    subtitle: "big bridge",
  };
  const expectedPlace2 = {
    title: "Zwierzyniecka",
    subtitle: "small bridge",
  };

  it('displays title and subtitle in the popup', () => {
    const zoomInTimes = 1;
    for (let i = 0; i < zoomInTimes; i++) {
      cy.get('.leaflet-marker-icon').first().click();
      cy.wait(500);
    }

    cy.get('.leaflet-marker-icon').first().then(($marker) => {
      cy.wrap($marker).click();
      cy.wait(500);

      cy.get('.leaflet-popup-content')
        .should('exist')
        .within(() => {

          cy.get('.point-title')
            .should('exist')
            .invoke('text')
            .then((title) => {
              if (title === expectedPlace1.title) {
                cy.get('.point-subtitle')
                  .should('have.text', expectedPlace1.subtitle)
              } else if (title === expectedPlace2.title) {
                cy.get('.point-subtitle')
                  .should('have.text', expectedPlace2.subtitle)
              }
            });
        });
    });
  });
});
