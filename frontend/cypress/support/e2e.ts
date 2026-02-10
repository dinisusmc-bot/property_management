// Enable command logging
Cypress.on('uncaught:exception', (err, runnable) => {
  return false;
});

before(() => {
  cy.log('E2E Test Suite Started');
});

after(() => {
  cy.log('E2E Test Suite Finished');
});
