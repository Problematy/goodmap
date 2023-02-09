describe('Geolocation prompt', () => {
  beforeEach(() => {
    cy.clearCookies();
    cy.clearLocalStorage();
  });

  it('asks for permission to share location', () => {
    cy.window().then((win) => {
      cy.visit('/');
      cy.wait(500);
      win.navigator.permissions.query({ name: 'geolocation' }).then((permissionStatus) => {
        expect(permissionStatus.state).to.eq('prompt');
      });
    });
  });
});
