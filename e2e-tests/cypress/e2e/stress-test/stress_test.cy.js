describe("Stress test", () => {

  it('Should map stop loading and measure performance', function () {
    let slowestTime = 0;
    const numRuns = 5;
    let runTimes = [];

    Cypress._.times(numRuns, () => {
      cy.visit('/');

      cy.log(`Run ${runTimes.length + 1} of ${numRuns}`);

      cy.window().then((win) => {
        let startTime = win.performance.now();

        cy.get('#map', { timeout: 60000 }).children({ timeout: 60000 })
          .then(() => {
            cy.window().then((win) => {
              let endTime = win.performance.now();
              const runTime = endTime - startTime;
              cy.log(`Run ${runTimes.length + 1} took ${runTime}ms`);
              runTimes.push(runTime);

              if (runTime > slowestTime) {
                slowestTime = runTime;
              }
            });
          });
      });
    });

    cy.then(() => {
      const maxAllowedTime = 100;

      // Always write performance data, even if we didn't complete all runs
      if (runTimes.length > 0) {
        // Calculate stats
        const avgTime = runTimes.reduce((a, b) => a + b, 0) / runTimes.length;
        const minTime = Math.min(...runTimes);

        // Write performance metrics to file for PR comment
        const perfData = {
          numRuns: runTimes.length,
          expectedRuns: numRuns,
          runTimes: runTimes.map((t, i) => ({ run: i + 1, time: Math.round(t) })),
          avgTime: Math.round(avgTime),
          minTime: Math.round(minTime),
          maxTime: Math.round(slowestTime),
          maxAllowed: maxAllowedTime,
          passed: slowestTime < maxAllowedTime && runTimes.length === numRuns
        };

        cy.writeFile('cypress/results/stress-test-perf.json', perfData);
        cy.log(`Performance data saved - Avg: ${Math.round(avgTime)}ms, Max: ${Math.round(slowestTime)}ms`);
      } else {
        // No runs completed - write failure data
        const perfData = {
          numRuns: 0,
          expectedRuns: numRuns,
          runTimes: [],
          avgTime: 0,
          minTime: 0,
          maxTime: 0,
          maxAllowed: maxAllowedTime,
          passed: false,
          error: 'No test runs completed'
        };
        cy.writeFile('cypress/results/stress-test-perf.json', perfData);
      }

      // Assertions
      expect(runTimes.length).to.equal(numRuns, `Expected ${numRuns} runs but only ${runTimes.length} completed`);
      expect(slowestTime).to.be.lessThan(maxAllowedTime, `The slowest run should be below ${maxAllowedTime}ms`);
    });
  });
});
