describe('Dashboard', () => {
  beforeEach(() => {
    cy.visit('/login');
    cy.get('input[type="email"]').type('admin@demo.com');
    cy.get('input[type="password"]').type('password');
    cy.get('button[type="submit"]').click();
  });

  it('displays metrics correctly', () => {
    cy.url().should('include', '/dashboard');
    cy.contains('Total Properties').should('be.visible');
    cy.contains('Occupied Units').should('be.visible');
    cy.contains('Maintenance Requests').should('be.visible');
    cy.contains('Monthly Revenue').should('be.visible');
  });

  it('sidebar navigation works', () => {
    cy.get('nav a').contains('Owners').should('be.visible');
    cy.get('nav a').contains('Properties').should('be.visible');
    cy.get('nav a').contains('Units').should('be.visible');
    cy.get('nav a').contains('Maintenance').should('be.visible');
  });
});
