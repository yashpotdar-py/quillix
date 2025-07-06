#!/bin/bash
echo "🧪 Testing Quillix Backend API"
echo "==============================="

BASE_URL="http://localhost:8000"

echo "1. Testing root endpoint..."
curl -s "$BASE_URL/" | jq '.'

echo -e "\n2. Testing health check..."
curl -s "$BASE_URL/system/health" | jq '.'

echo -e "\n3. Testing Discord message..."
curl -s -X POST "$BASE_URL/discord/send-message" \
  -H "Content-Type: application/json" \
  -d '{"content": "🧪 Test from curl!", "username": "Curl Tester"}' | jq '.'

echo -e "\n4. Testing scraper list..."
curl -s "$BASE_URL/scraper/scrapers" | jq '.'

echo -e "\n5. Testing scrape (without Discord)..."
curl -s -X POST "$BASE_URL/scraper/scrape?scraper_name=techcrunch&send_to_discord=false" | jq '.data.total_count'

echo -e "\n6. Testing scrape (with Discord)..."
curl -s -X POST "$BASE_URL/scraper/scrape?scraper_name=techcrunch&send_to_discord=true" | jq '.data.total_count'

echo -e "\n✅ Quick tests completed!"