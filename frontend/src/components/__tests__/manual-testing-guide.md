# Manual Testing Guide for Error Scenarios

This guide provides step-by-step instructions for manually testing all error handling features in FlipLens.

## Prerequisites

1. Start the backend server: `cd backend && python run.py`
2. Start the frontend development server: `cd frontend && npm start`
3. Open the application in your browser
4. Open browser DevTools (F12)

## 1. Network Error Testing

### Test Network Disconnection
1. **Disconnect Network**: Turn off WiFi or disconnect network cable
2. **Perform Search**: Try searching for "iPhone" or any item
3. **Expected Result**: 
   - Error message: "Unable to connect to server. Please check your internet connection."
   - Retry button should be visible
   - If cached data exists, it should be displayed with "Cached" badge

### Test Network Reconnection
1. **Reconnect Network**: Turn WiFi back on
2. **Click Retry**: Click the retry button on the error message
3. **Expected Result**: 
   - Search should work normally
   - Error should disappear
   - Fresh results should load

## 2. Timeout Error Testing

### Simulate Slow Network
1. **Open DevTools**: Go to Network tab
2. **Set Throttling**: Select "Slow 3G" or "Fast 3G"
3. **Perform Search**: Try searching for an item
4. **Expected Result**:
   - If timeout occurs: "Request timed out. Please check your connection and try again."
   - Retry button should show retry count (e.g., "Retry (1/3)")

### Test Multiple Timeouts
1. **Keep Slow Network**: Maintain slow network setting
2. **Click Retry Multiple Times**: Click retry button repeatedly
3. **Expected Result**:
   - Retry count should increment: (1/3), (2/3), (3/3)
   - After 3 attempts: "Max retries reached" message
   - Retry button should disappear

## 3. Server Error Testing

### Simulate 500 Error
1. **Stop Backend Server**: Kill the Flask backend process
2. **Perform Search**: Try searching for an item
3. **Expected Result**:
   - Error message: "Server error occurred. Please try again later."
   - Retry button should be visible

### Test Server Recovery
1. **Restart Backend Server**: Start the Flask server again
2. **Click Retry**: Click the retry button
3. **Expected Result**: Search should work normally

## 4. Validation Error Testing

### Test Invalid Search
1. **Empty Search**: Try searching with empty string
2. **Expected Result**: No error (should be handled gracefully)

### Test Invalid Save Data
1. **Perform Search**: Search for any item
2. **Stop Backend**: Kill the backend server
3. **Try to Save**: Click save button on any item
4. **Expected Result**: Error message should appear with retry option

## 5. Rate Limit Error Testing

### Simulate Rate Limiting
1. **Open DevTools**: Go to Network tab
2. **Set Up Mock**: In Network tab, right-click on search request
3. **Mock Response**: Set status to 429 with headers: `retry-after: 60`
4. **Perform Search**: Try searching
5. **Expected Result**:
   - Error message: "Too many requests. Please wait a moment and try again."
   - Retry button should show: "Retry in 60s"

## 6. Offline Functionality Testing

### Test Offline Detection
1. **Go Offline**: In DevTools Network tab, check "Offline" checkbox
2. **Expected Result**:
   - Red offline indicator should appear at top of screen
   - Should show connection type and last online time
   - Yellow offline banner should appear in main content

### Test Offline Caching
1. **Perform Search Online**: Search for "iPhone" while online
2. **Go Offline**: Check "Offline" checkbox in DevTools
3. **Search Again**: Search for "iPhone" again
4. **Expected Result**:
   - Results should load from cache
   - "Cached" badge should appear in results header
   - "(showing cached results)" text should appear

### Test Cache Expiration
1. **Set Short Cache Time**: Modify cache expiration in code (for testing)
2. **Perform Search**: Search for an item
3. **Wait for Expiration**: Wait for cache to expire
4. **Go Offline and Search**: Search for the same item
5. **Expected Result**: Should show network error (no cached data)

## 7. Loading States Testing

### Test Search Loading
1. **Set Slow Network**: Use "Slow 3G" throttling
2. **Perform Search**: Search for any item
3. **Expected Result**:
   - Loading spinner should appear
   - Search button should be disabled
   - Loading skeleton should show in results area

### Test Save Loading
1. **Perform Search**: Search for any item
2. **Click Save**: Click save button on an item
3. **Expected Result**:
   - Save button should show loading state
   - Button should be disabled during save
   - Loading spinner should appear on button

## 8. Retry Logic Testing

### Test Retry with Success
1. **Stop Backend**: Kill the backend server
2. **Perform Search**: Try searching (should fail)
3. **Start Backend**: Restart the server
4. **Click Retry**: Click retry button
5. **Expected Result**: Search should succeed

### Test Retry with Persistent Failure
1. **Stop Backend**: Keep backend stopped
2. **Perform Search**: Try searching
3. **Click Retry Multiple Times**: Click retry 3 times
4. **Expected Result**:
   - Should show retry count each time
   - After 3 attempts: "Max retries reached"
   - No more retry button

## 9. Error Display Testing

### Test Error Dismissal
1. **Trigger Any Error**: Create any error condition
2. **Click Dismiss**: Click the "Dismiss" button
3. **Expected Result**: Error message should disappear

### Test Error Persistence
1. **Trigger Error**: Create an error condition
2. **Don't Dismiss**: Leave error message visible
3. **Perform New Action**: Try a new search or action
4. **Expected Result**: Error should persist until dismissed or retried

## 10. Edge Cases Testing

### Test Multiple Concurrent Errors
1. **Stop Backend**: Kill the server
2. **Perform Multiple Actions**: Try searching and saving simultaneously
3. **Expected Result**: Should handle multiple errors gracefully

### Test Error During Loading
1. **Start Search**: Begin a search
2. **Stop Backend**: Kill server during search
3. **Expected Result**: Should transition from loading to error state

### Test Cache Corruption
1. **Manually Corrupt Cache**: In DevTools Application tab, modify localStorage
2. **Perform Search**: Try searching
3. **Expected Result**: Should handle corrupted cache gracefully

## 11. Mobile Testing

### Test on Mobile Device
1. **Open on Mobile**: Access app on mobile device
2. **Test Offline**: Turn off mobile data/WiFi
3. **Test Touch Interactions**: Test error buttons and retry functionality
4. **Expected Result**: All error handling should work on mobile

### Test Responsive Error Display
1. **Resize Browser**: Test different screen sizes
2. **Check Error Messages**: Ensure error messages are readable
3. **Test Button Sizes**: Ensure retry/dismiss buttons are touch-friendly
4. **Expected Result**: Error UI should be responsive and accessible

## 12. Performance Testing

### Test Error Recovery Performance
1. **Measure Load Times**: Use DevTools Performance tab
2. **Trigger Errors**: Create various error conditions
3. **Measure Recovery**: Time how long it takes to recover
4. **Expected Result**: Error recovery should be fast (< 2 seconds)

### Test Cache Performance
1. **Load Large Dataset**: Search for items with many results
2. **Go Offline**: Disconnect network
3. **Measure Cache Load**: Time how long cached results take to load
4. **Expected Result**: Cached results should load quickly (< 500ms)

## Success Criteria

All tests should pass with the following criteria:
- ✅ Error messages are clear and actionable
- ✅ Retry functionality works correctly
- ✅ Loading states are visible and appropriate
- ✅ Offline functionality works as expected
- ✅ Cache system functions properly
- ✅ UI remains responsive during errors
- ✅ Error recovery is fast and reliable
- ✅ Mobile experience is good
- ✅ No console errors (except expected network errors)

## Reporting Issues

If any test fails:
1. **Document the Issue**: Note what was expected vs what happened
2. **Include Steps**: Provide exact steps to reproduce
3. **Include Environment**: Note browser, OS, network conditions
4. **Include Screenshots**: Capture error states and UI issues
5. **Check Console**: Look for any JavaScript errors or warnings 