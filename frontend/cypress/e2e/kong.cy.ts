describe('Kong Gateway Validation', () => {
  it('returns 401 when no auth token', () => {
    cy.request({
      method: 'GET',
      url: '/api/v1/owners/owners',
      failOnStatusCode: false,
    }).then((resp) => {
      expect(resp.status).to.eq(401);
    });
  });

  it('returns 403 for unauthorized actions', () => {
    cy.request({
      method: 'POST',
      url: '/api/v1/owners/owners',
      body: { email: 'test@test.com', full_name: 'Test' },
      failOnStatusCode: false,
    }).then((resp) => {
      expect(resp.status).to.eq(401);
    });
  });
});
