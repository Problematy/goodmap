describe('Navigation Bar Test for small devices', () => {
  const viewports = ['iphone-6', 'ipad-2', 'samsung-s10']
  beforeEach(() => {
    cy.visit('http://localhost:5000');
  });

  viewports.forEach((viewport) => {
    it(`Hamburger menu is vertically centered with the logo on ${viewport}`, () => {
      cy.viewport(viewport);

      // Get the position and dimensions of the logo
      cy.get('.navbar-brand').then((logo) => {
        const logoPosition = logo.position();
        const logoHeight = logo.outerHeight();
        const logoCenter = logoPosition.top + logoHeight / 2;
        cy.log('Logo Center:', logoCenter);

        // Get the positions of all hamburgers
        cy.get('.navbar-toggler').each(($hamburger, index) => {
          const hamburgerPosition = $hamburger.position();
          const hamburgerHeight = $hamburger.outerHeight();
          const hamburgerCenter = hamburgerPosition.top + hamburgerHeight / 2;
          cy.log(`Hamburger Center ${index + 1}:`, hamburgerCenter);

          // Assert that the hamburger menu is vertically centered with the logo
          expect(hamburgerCenter).to.be.closeTo(logoCenter, 3)
        });
      });
    });
  });
});
