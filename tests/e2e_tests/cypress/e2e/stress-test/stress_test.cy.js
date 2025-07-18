describe("Stress test", () => {

  it('Should map stop loading and measure performance', function () {
    let slowestTime = 0;
    const numRuns = 5;
    let runTimes = [];

    Cypress._.times(numRuns, () => {
      cy.visit('/');
      cy.window().then((win) => {
        let startTime = win.performance.now();

        cy.get('#map', { timeout: 60000 }).children({ timeout: 60000 })
          .then(() => {
            cy.window().then((win) => {
              let endTime = win.performance.now();
              const runTime = endTime - startTime;
              const runText = `Rune e2e tests: Run ${runTimes.length + 1} took ${runTime}ms`;
              cy.log(runText);
              cy.task('appendToGithubStepSummary', runText);
              runTimes.push(runTime);

              if (runTime > slowestTime) {
                slowestTime = runTime;
              }
            });
          });
      });
    });

    cy.then(() => {
      const maxAllowedTime = 20000;
      expect(slowestTime).to.be.lessThan(maxAllowedTime, `The slowest run should be below ${maxAllowedTime}ms`);
    });
  });
});
