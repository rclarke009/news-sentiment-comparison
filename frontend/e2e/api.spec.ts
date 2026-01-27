import { test, expect } from '@playwright/test';

/**
 * API tests - test the backend API directly (without browser)
 * 
 * These tests make HTTP requests directly to the API endpoints.
 * Useful for:
 * - Testing API responses and status codes
 * - Validating data structures
 * - Testing error handling
 * - Faster than E2E tests (no browser overhead)
 */

// Base URL for API - defaults to localhost, can be overridden with PLAYWRIGHT_API_URL
const API_BASE_URL = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000/api/v1';

test.describe('API Endpoints', () => {
  
  test('health check endpoint returns healthy status', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/health`);
    expect(response.ok()).toBeTruthy();
    
    const body = await response.json();
    expect(body).toHaveProperty('status');
    expect(body.status).toBe('healthy');
    expect(body).toHaveProperty('timestamp');
  });

  test('sources endpoint returns conservative and liberal sources', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/sources`);
    expect(response.ok()).toBeTruthy();
    
    const body = await response.json();
    expect(body).toHaveProperty('conservative');
    expect(body).toHaveProperty('liberal');
    expect(Array.isArray(body.conservative)).toBe(true);
    expect(Array.isArray(body.liberal)).toBe(true);
  });

  test('today endpoint returns 404 or valid comparison', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/today`);
    
    // Either 404 (no data) or 200 (has data)
    if (response.status() === 404) {
      const body = await response.json();
      expect(body).toHaveProperty('detail');
      // This is expected if no data has been collected yet
    } else {
      expect(response.ok()).toBeTruthy();
      const body = await response.json();
      expect(body).toHaveProperty('date');
      expect(body).toHaveProperty('conservative');
      expect(body).toHaveProperty('liberal');
    }
  });

  test('history endpoint returns valid structure', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/history?days=7`);
    expect(response.ok()).toBeTruthy();
    
    const body = await response.json();
    expect(body).toHaveProperty('comparisons');
    expect(body).toHaveProperty('days');
    expect(Array.isArray(body.comparisons)).toBe(true);
    expect(typeof body.days).toBe('number');
  });

  test('stats endpoint returns valid structure', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/stats?days=30`);
    
    // Either 404 (no data) or 200 (has data)
    if (response.status() === 404) {
      const body = await response.json();
      expect(body).toHaveProperty('detail');
    } else {
      expect(response.ok()).toBeTruthy();
      const body = await response.json();
      expect(body).toHaveProperty('total_days');
      expect(body).toHaveProperty('conservative_avg');
      expect(body).toHaveProperty('liberal_avg');
    }
  });

  test('date endpoint validates date format', async ({ request }) => {
    // Test invalid date format
    const invalidResponse = await request.get(`${API_BASE_URL}/date/invalid-date`);
    expect(invalidResponse.status()).toBe(400);
    
    const invalidBody = await invalidResponse.json();
    expect(invalidBody).toHaveProperty('detail');
    expect(invalidBody.detail).toContain('Invalid date format');
  });

  test('most-uplifting endpoint requires valid side parameter', async ({ request }) => {
    // Test missing side parameter
    const response = await request.get(`${API_BASE_URL}/most-uplifting`);
    expect(response.status()).toBe(422); // FastAPI validation error
    
    // Test invalid side
    const invalidResponse = await request.get(`${API_BASE_URL}/most-uplifting?side=invalid`);
    expect(invalidResponse.status()).toBe(400);
  });
});
