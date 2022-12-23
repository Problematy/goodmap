describe('the most basic test', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('displays filter list with two categories with 5 items', () => {
    cy.get('input[type="checkbox"]').should('have.length', 5)
    cy.get('form span').should('have.length', 2)
  })

})
