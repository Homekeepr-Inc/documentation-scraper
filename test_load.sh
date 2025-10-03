#!/bin/bash

# Load SCRAPER_SECRET from environment
if [ -z "$SCRAPER_SECRET" ]; then
    echo "Error: SCRAPER_SECRET environment variable not set"
    exit 1
fi

echo "Starting load test with 10 sequential Samsung manual downloads (15s delay between each)..."

# Array to store response codes
declare -a codes

# Function to run curl and capture code
run_curl() {
    local url=$1
    local output=$2
    local code=$(curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "$url" -o "$output" -w "%{http_code}" -s)
    codes+=($code)
    echo "Request to $url: HTTP $code"
}

# Run curls with 5s delay
run_curl "https://api.homekeepr.co/scrape/samsung/RF29A9671SR/AA" "RF29A9671SR_AA.pdf"
sleep 10
run_curl "https://api.homekeepr.co/scrape/samsung/RF23A9671SR/AA" "RF23A9671SR_AA.pdf"
sleep 10
run_curl "https://api.homekeepr.co/scrape/samsung/RF27T5501SR/AA" "RF27T5501SR_AA.pdf"
sleep 10
run_curl "https://api.homekeepr.co/scrape/samsung/RF28R7351SG/AA" "RF28R7351SG_AA.pdf"
sleep 10
run_curl "https://api.homekeepr.co/scrape/samsung/RS27T5200SR/AA" "RS27T5200SR_AA.pdf"
sleep 10
run_curl "https://api.homekeepr.co/scrape/samsung/WV60A9900AV/A5" "WV60A9900AV_A5.pdf"
sleep 10
run_curl "https://api.homekeepr.co/scrape/samsung/WF53BB8900AD/US" "WF53BB8900AD_US.pdf"
sleep 10
run_curl "https://api.homekeepr.co/scrape/samsung/WF46BG6500AV/US" "WF46BG6500AV_US.pdf"
sleep 10
run_curl "https://api.homekeepr.co/scrape/samsung/WA54CG7550AV/US" "WA54CG7550AV_US.pdf"
sleep 10
run_curl "https://api.homekeepr.co/scrape/samsung/WV50A9465AV/A5" "WV50A9465AV_A5.pdf"

echo ""
echo "Load test complete. Response metrics:"

# Count occurrences
declare -A count
total=${#codes[@]}
for code in "${codes[@]}"; do
    ((count[$code]++))
done

# Print metrics
for code in "${!count[@]}"; do
    pct=$(( count[$code] * 100 / total ))
    echo "HTTP $code: ${count[$code]} requests ($pct%)"
done

echo "Total requests: $total"