describe('Navigation Bar Test', () => {
  beforeEach(() => {
    cy.visit('http://localhost:5000');
  });

  it('Hamburger menu is vertically centered with the logo on smaller devices', () => {
    // Set the viewport to emulate a smaller device
    cy.viewport('iphone-6');

    // wait for the page to load
    cy.wait(1000);  // TODO: replace with a better way to wait for page to load

    // Get the position and dimensions of the logo
    cy.get('.navbar-brand').then((logo) => {
      const logoPosition = logo.position();
      const logoHeight = logo.outerHeight();
      const logoCenter = logoPosition.top + logoHeight / 2;
      cy.log('Logo Center:', logoCenter);

      // Get the positions of all hamburgers
      cy.get('.navbar-toggler').then((hamburgers) => {
        // Iterate over each hamburger and compare its center with the logo center
        hamburgers.each((index, hamburger) => {
          cy.wrap(hamburger).then(($hamburger) => {
            const hamburgerPosition = $hamburger.position();
            const hamburgerHeight = $hamburger.outerHeight();
            const hamburgerCenter = hamburgerPosition.top + hamburgerHeight / 2;
            cy.log('Hamburger Center:', hamburgerCenter);

            // Assert that the hamburger menu is vertically centered with the logo
            expect(hamburgerCenter).to.be.closeTo(logoCenter, 1);
          });
        });
      });
    });
  });
});
