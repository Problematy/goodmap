const zoomInTimes = 1;

export function zoomInMap() {
  for (let i = 0; i < zoomInTimes; i++) {
    cy.get('.leaflet-marker-icon').first().click();
    cy.wait(500);
  }
}

export function verifyPopupContent(expectedContent) {
    cy.get('.point-subtitle')
      .should('have.text', expectedContent.subtitle);

    expectedContent.categories.forEach(([category, value]) => {
      cy.contains(category).should('exist');
      cy.contains(value).should('exist');
    });

    if (expectedContent.CTA) {
      cy.contains(expectedContent.CTA.displayValue).should('exist');
      cy.contains('button', expectedContent.CTA.displayValue).click();
      cy.get('@openStub').should('have.been.calledOnceWith',
        expectedContent.CTA.value, '_blank');
    }
  }

// TODO - Find a way to search for a specific point, not iterate over all of them
export function verifyArbitraryPopupContent(expectedPlaces) {
      cy.get('.point-title').should('exist').invoke('text')
        .then((title) => {
          const expectedPlace1 = expectedPlaces[0];
          const expectedPlace2 = expectedPlaces[1];
          if (title === expectedPlace1.title) {
            verifyPopupContent(expectedPlace1);
          } else if (title === expectedPlace2.title) {
            verifyPopupContent(expectedPlace2);
          }
        });
}


function desktopTest() {
    zoomInMap();

    cy.get('.leaflet-marker-icon').each(($marker) => {
      cy.wrap($marker).click();
      cy.wait(500);
      verifyPopupElementsOnDesktop();
    });
}

function MobileTest() {
      cy.on('window:before:load', (win) => {
        Object.defineProperty(win.navigator, 'userAgent', {
          value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
        });
      })

    zoomInMap();

    cy.get('.leaflet-marker-icon').each(($marker) => {
      cy.wrap($marker).click();
      cy.wait(500);
      verifyPopupElementsOnMobile
    });
}



export function verifyProblemForm() {
  cy.contains('report a problem').should('exist').click();

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

}

function verifyPopupElementsOnDesktop() {
      cy.get('.leaflet-popup-content').should('exist')
        .within(() => {
          verifyArbitraryPopupContent(expectedPlaces);

          verifyProblemForm();
        });
      cy.get('.leaflet-popup-close-button').should('exist').then(($button) => {
        cy.wrap($button).click();
        cy.wait(500);
      });
}

function verifyPopupElementsOnMobile() {
      cy.get('.MuiDialogContent-root').should('exist')
        .within(() => {
          verifyArbitraryPopupContent(expectedPlaces);

          verifyProblemForm();
          // Verify "navigate me" button
        });
        cy.get('.MuiIconButton-root').should('exist').then(($button) => {
          cy.wrap($button).click();
          cy.wait(500);
        });
}
