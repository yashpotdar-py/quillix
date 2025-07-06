#!/bin/bash
echo "=============================================="
echo "🧪 Testing Quillix Backend Discord Webhooks"
echo "=============================================="

BASE_URL="http://localhost:8000"

echo "1. Testing webhook status..."
curl -s "$BASE_URL/discord/webhooks" | jq '.'

echo -e "\n2. Testing default webhook..."
curl -s -X POST "$BASE_URL/discord/send-message?webhook_type=default" \
  -H "Content-Type: application/json" \
  -d '{"content": "🧪 Test from DEFAULT webhook!", "username": "Default Tester"}' | jq '.'

echo -e "\n3. Testing testing webhook..."
curl -s -X POST "$BASE_URL/discord/send-message?webhook_type=testing" \
  -H "Content-Type: application/json" \
  -d '{"content": "🧪 Test from TESTING webhook!", "username": "Testing Bot"}' | jq '.'

echo -e "\n4. Testing system notification"
curl -s -X POST "$BASE_URL/discord/send-system-notification" \
  -H "Content-Type: application/json" \
  -d '{"message": "System is running smoothly!"}' | jq '.'

echo -e "\n5. Testing health check message..."
curl -s -X POST "$BASE_URL/discord/health-check" | jq '.'

echo "=============================================="
echo "🧪 Testing Quillix Backend Consolidated Reports"
echo "=============================================="

BASE_URL="http://localhost:8000"

echo "1. Testing Summary Report..."
curl -s -X POST "$BASE_URL/scraper/scrape-and-notify?scraper_name=techcrunch&report_style=summary" | jq '.status'

echo -e "\n2. Testing Compact Report..."
curl -s -X POST "$BASE_URL/scraper/scrape-and-notify?scraper_name=techcrunch&report_style=compact" | jq '.status'

echo -e "\n3. Testing Detailed Report..."
curl -s -X POST "$BASE_URL/scraper/scrape-and-notify?scraper_name=techcrunch&report_style=detailed" | jq '.status'

echo -e "\n4. Testing Daily Digest..."
curl -s -X POST "$BASE_URL/scraper/send-daily-digest?scraper_name=techcrunch" | jq '.status'

echo -e "\n✅ Report tests completed!"
echo -e "\n✅ Webhook tests completed!"