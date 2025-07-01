// Test script for error handling implementation
const axios = require('axios');

const API_BASE_URL = 'http://localhost:5000/api';

async function testErrorHandling() {
  console.log('🧪 Testing Error Handling Implementation\n');

  // Test 1: Valid search request
  console.log('1️⃣ Testing valid search request...');
  try {
    const response = await axios.post(`${API_BASE_URL}/search`, {
      query: 'iPhone',
      limit: 3
    });
    console.log('✅ Valid search successful:', response.data.status);
  } catch (error) {
    console.log('❌ Valid search failed:', error.response?.data || error.message);
  }

  // Test 2: Validation error (missing query)
  console.log('\n2️⃣ Testing validation error (missing query)...');
  try {
    await axios.post(`${API_BASE_URL}/search`, {
      limit: 5
    });
    console.log('❌ Should have failed with validation error');
  } catch (error) {
    console.log('✅ Validation error caught:', error.response?.data?.error);
  }

  // Test 3: Invalid endpoint (404)
  console.log('\n3️⃣ Testing 404 error...');
  try {
    await axios.get(`${API_BASE_URL}/nonexistent`);
    console.log('❌ Should have failed with 404 error');
  } catch (error) {
    console.log('✅ 404 error caught:', error.response?.status, error.response?.data?.error);
  }

  // Test 4: Invalid JSON
  console.log('\n4️⃣ Testing invalid JSON...');
  try {
    await axios.post(`${API_BASE_URL}/search`, 'invalid json', {
      headers: { 'Content-Type': 'application/json' }
    });
    console.log('❌ Should have failed with JSON parse error');
  } catch (error) {
    console.log('✅ JSON parse error caught:', error.response?.status);
  }

  // Test 5: Network timeout (simulated)
  console.log('\n5️⃣ Testing timeout error...');
  try {
    await axios.get(`${API_BASE_URL}/search`, {
      timeout: 1, // 1ms timeout to force timeout error
      params: { q: 'test' }
    });
    console.log('❌ Should have failed with timeout error');
  } catch (error) {
    if (error.code === 'ECONNABORTED') {
      console.log('✅ Timeout error caught:', error.code);
    } else {
      console.log('❌ Unexpected error:', error.message);
    }
  }

  // Test 6: Health check
  console.log('\n6️⃣ Testing health check...');
  try {
    const response = await axios.get(`${API_BASE_URL}/health`);
    console.log('✅ Health check successful:', response.data.status);
  } catch (error) {
    console.log('❌ Health check failed:', error.message);
  }

  console.log('\n🎉 Error handling tests completed!');
  console.log('\n📝 Next steps:');
  console.log('1. Open http://localhost:3000 in your browser');
  console.log('2. Try searching for items to see normal operation');
  console.log('3. Disconnect your internet to test network errors');
  console.log('4. Check browser console for error logs');
  console.log('5. Verify error display components show appropriate messages');
}

// Run the tests
testErrorHandling().catch(console.error); 