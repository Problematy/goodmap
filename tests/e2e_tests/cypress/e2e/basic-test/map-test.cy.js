describe('Map Tests', () => {
    beforeEach(() => {
        cy.visit('/');
    });

    it('displays filter list with two categories with 5 items', () => {
        cy.get('input[type="checkbox"]').should('have.length', 5);
        cy.get('form span').should('have.length', 2);
    });

    it('Should not have scrollbars', () => {
        // Get the dimensions of the viewport and the entire page
        cy.window().then(win => {
            const { innerWidth, innerHeight } = win;
            const { scrollWidth, scrollHeight } = win.document.documentElement;

            // Assert if the page width or height is less than or equal to the viewport dimensions,
            // indicating no scrollbars
            expect(scrollWidth <= innerWidth).to.be.true;
            expect(scrollHeight <= innerHeight).to.be.true;
        });
    });
});
