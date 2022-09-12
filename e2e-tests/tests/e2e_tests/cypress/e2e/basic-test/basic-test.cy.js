describe('the most basic test', () => {
  beforeEach(() => {
    // TODO this probably should be written in some cypress configuration
    cy.visit('http://127.0.0.1:5000')
  })

  it('displays filter list with two categories with 5 items', () => {
    cy.get('input[type="checkbox"]').should('have.length', 5)
    cy.get('form span').should('have.length', 2)
  })

})
