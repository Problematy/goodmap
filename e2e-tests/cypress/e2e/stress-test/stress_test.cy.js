describe("Stress test", () => {

  it('Should load all markers and measure performance', function () {
    let slowestTime = 0;
    const numRuns = 5;
    let runTimes = [];
    const minExpectedMarkers = 10; // Minimum markers that should be visible in initial viewport

    Cypress._.times(numRuns, () => {
      // Intercept API call to track when locations are loaded
      cy.intercept('GET', '/api/locations*').as('loadLocations');

      cy.visit('/');

      cy.log(`Run ${runTimes.length + 1} of ${numRuns}`);

      cy.window().then((win) => {
        let startTime = win.performance.now();

        // Wait for map container to be ready
        cy.get('#map', { timeout: 60000 }).should('be.visible');

        // Wait for locations API call to complete
        cy.wait('@loadLocations', { timeout: 60000 });

        // Wait for markers to stabilize (stop increasing in count)
        // This ensures all initial markers are rendered
        let previousCount = 0;
        cy.waitUntil(
          () => {
            return cy.document().then((doc) => {
              const markers = doc.querySelectorAll('.leaflet-marker-icon, .leaflet-marker-cluster');
              const currentCount = markers.length;

              // Log for debugging
              if (currentCount !== previousCount) {
                cy.log(`Marker count changed: ${previousCount} -> ${currentCount}`);
              }

              // Check if count has stabilized AND meets minimum requirement
              const isStable = currentCount === previousCount && currentCount >= minExpectedMarkers;

              previousCount = currentCount;
              return isStable;
            });
          },
          {
            timeout: 60000,
            interval: 500,
            errorMsg: `Markers did not stabilize at minimum ${minExpectedMarkers} within timeout`
          }
        ).then(() => {
          cy.get('.leaflet-marker-icon, .leaflet-marker-cluster').then((markers) => {
            cy.window().then((win) => {
              let endTime = win.performance.now();
              const runTime = endTime - startTime;
              const markerCount = markers.length;

              cy.log(`Run ${runTimes.length + 1} took ${runTime}ms and loaded ${markerCount} markers/clusters`);
              runTimes.push({
                time: runTime,
                markerCount: markerCount
              });

              if (runTime > slowestTime) {
                slowestTime = runTime;
              }

              // Verify minimum number of markers are loaded
              expect(markerCount).to.be.greaterThan(minExpectedMarkers,
                `Expected more than ${minExpectedMarkers} markers but got ${markerCount}`);
            });
          });
        });
      });
    });

    cy.then(() => {
      const maxAllowedTime = 20000; // 20 seconds for 100k points with lazy loading

      // Always write performance data, even if we didn't complete all runs
      if (runTimes.length > 0) {
        // Calculate stats
        const times = runTimes.map(r => r.time);
        const avgTime = times.reduce((a, b) => a + b, 0) / times.length;
        const minTime = Math.min(...times);
        const avgMarkers = runTimes.reduce((a, b) => a + b.markerCount, 0) / runTimes.length;

        // Write performance metrics to file for PR comment
        const perfData = {
          numRuns: runTimes.length,
          expectedRuns: numRuns,
          runTimes: runTimes.map((r, i) => ({
            run: i + 1,
            time: Math.round(r.time),
            markers: r.markerCount
          })),
          avgTime: Math.round(avgTime),
          minTime: Math.round(minTime),
          maxTime: Math.round(slowestTime),
          avgMarkers: Math.round(avgMarkers),
          maxAllowed: maxAllowedTime,
          passed: slowestTime < maxAllowedTime && runTimes.length === numRuns
        };

        cy.writeFile('cypress/results/stress-test-perf.json', perfData);
        cy.log(`Performance data saved - Avg: ${Math.round(avgTime)}ms, Max: ${Math.round(slowestTime)}ms, Avg Markers: ${Math.round(avgMarkers)}`);
      } else {
        // No runs completed - write failure data
        const perfData = {
          numRuns: 0,
          expectedRuns: numRuns,
          runTimes: [],
          avgTime: 0,
          minTime: 0,
          maxTime: 0,
          avgMarkers: 0,
          maxAllowed: maxAllowedTime,
          passed: false,
          error: 'No test runs completed'
        };
        cy.writeFile('cypress/results/stress-test-perf.json', perfData);
      }

      // Assertions
      expect(runTimes.length).to.equal(numRuns, `Expected ${numRuns} runs but only ${runTimes.length} completed`);
      expect(slowestTime).to.be.lessThan(maxAllowedTime, `The slowest run (${Math.round(slowestTime)}ms) should be below ${maxAllowedTime}ms`);
    });
  });
});
