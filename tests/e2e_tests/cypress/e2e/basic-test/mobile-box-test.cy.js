describe('Popup Tests on Mobile', () => {
  const viewports = ['iphone-x', 'iphone-6', 'ipad-2', 'samsung-s10']
//  const viewports = ['iphone-x']

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

  viewports.forEach((viewport) => {

    it(`displays title and subtitle in the popup on ${viewport}`, () => {

      cy.on('window:before:load', (win) => {
        Object.defineProperty(win.navigator, 'userAgent', {
          value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
        });
      })
      cy.viewport(viewport);

//      cy.reload();
      cy.visit('/');
    cy.wait(500);


      cy.window().then((win) => {
        cy.stub(win, 'open').as('openStub');
      });



      const zoomInTimes = 1;
      for (let i = 0; i < zoomInTimes; i++) {
        cy.get('.leaflet-marker-icon').first().click({ force: true });
        cy.wait(500);
      }

      // TODO - Find a way to search for a specific point, not iterate over all of them
      cy.get('.leaflet-marker-icon').each(($marker) => {
        cy.wrap($marker).click({ force: true });
        cy.wait(500);

        cy.get('.MuiDialogContent-root').should('exist')
          .within(() => {

            function verifyPopupContent(expectedContent) {
              cy.get('.point-subtitle')
                .should('have.text', expectedContent.subtitle);

              expectedContent.categories.forEach(([category, value]) => {
                cy.contains(category).should('exist');
                cy.contains(value).should('exist');
              });

              if (expectedContent.CTA) {
                cy.contains(expectedContent.CTA.displayValue).should('exist');
                cy.contains('button', expectedContent.CTA.displayValue).click({ force: true });
                cy.get('@openStub').should('have.been.calledOnceWith',
                  expectedContent.CTA.value, '_blank');
              }
            }


            cy.get('.point-title').should('exist').invoke('text')
              .then((title) => {
                if (title === expectedPlace1.title) {
                  verifyPopupContent(expectedPlace1);
                } else if (title === expectedPlace2.title) {
                  verifyPopupContent(expectedPlace2);
                }
              });
            cy.contains('report a problem').should('exist').click({ force: true });

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

          });

        cy.get('.MuiIconButton-root').should('exist').then(($button) => {
          cy.wrap($button).click({ force: true });
          cy.wait(500);
        });
      });
    });
  });

});
