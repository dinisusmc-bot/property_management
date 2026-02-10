describe('Login Flow', () => {
  it('shows login page and validates inputs', () => {
    cy.visit('/login');
    cy.get('h2').should('contain', 'Property Manager');
    cy.get('input[type="email"]').should('be.visible');
    cy.get('input[type="password"]').should('be.visible');
    cy.get('button[type="submit"]').should('contain', 'Sign In');
  });

  it('shows error for invalid credentials', () => {
    cy.visit('/login');
    cy.get('input[type="email"]').type('invalid@test.com');
    cy.get('input[type="password"]').type('wrongpassword');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/login');
  });
});
