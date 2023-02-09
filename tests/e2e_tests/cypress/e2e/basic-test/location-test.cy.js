describe('Geolocation prompt', () => {
  it('asks for permission to share location', () => {

    cy.window().then((win) => {
      const spy = cy.spy(win.navigator.geolocation, 'getCurrentPosition');
      cy.visit('/');

      cy.wait(1000);
//      expect(spy).to.be.called;

      cy.wait(500);
      win.navigator.permissions.query({ name: 'geolocation' }).then((permissionStatus) => {
        expect(permissionStatus.state).to.eq('prompt');
      });
    });
  });
});
