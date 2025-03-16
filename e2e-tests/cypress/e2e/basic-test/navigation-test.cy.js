describe('Navigation Bar Test for small devices', () => {
    const viewports = ['iphone-6', 'ipad-2', 'samsung-s10'];
    beforeEach(() => {
        cy.visit('/');
    });

    viewports.forEach(viewport => {
        it(`Hamburger menu is vertically centered with the logo on ${viewport}`, () => {
            cy.viewport(viewport);

            cy.get('.navbar-brand').then(logo => {
                const logoPosition = logo.position();
                const logoHeight = logo.outerHeight();
                const logoCenter = logoPosition.top + logoHeight / 2;
                cy.log('Logo Center:', logoCenter);

                cy.get('.navbar-toggler').each(($hamburger, index) => {
                    const hamburgerPosition = $hamburger.position();
                    const hamburgerHeight = $hamburger.outerHeight();
                    const hamburgerCenter = hamburgerPosition.top + hamburgerHeight / 2;
                    cy.log(`Hamburger Center ${index + 1}:`, hamburgerCenter);

                    expect(hamburgerCenter).to.be.closeTo(logoCenter, 3);
                });
            });
        });

        it(`Left menu is visible after clicking left hamburger on ${viewport}`, () => {
            cy.viewport(viewport);
            cy.get('#left-panel').should('be.not.visible');
            cy.get('.navbar-toggler').first().click();
            cy.get('#left-panel').should('be.visible');

            cy.get('#filter-form')
                .should('be.visible')
                .then(filterForm => {
                    const filterFormRect = filterForm[0].getBoundingClientRect();
                    const filterFormTop = filterFormRect.top;

                    cy.log('Filter Form Top:', filterFormTop);

                    cy.get('.navbar').then($navbar => {
                        const navbarPosition = $navbar.position();
                        const navbarHeight = $navbar.outerHeight();
                        const navbarBottom = navbarPosition.top + navbarHeight;
                        cy.log('Navbar Bottom:', navbarBottom);

                        expect(filterFormTop).to.be.greaterThan(navbarBottom);
                    });
                });
        });
    });
});
