# Islam-Mate API Test Suite v3.3
# Fixes: prayer/methods URL, azkar slug URL, hijri/today,
#        rate-limit sleep, removed lat/lng wrong-param tests,
#        removed non-existent azkar slugs (morning, evening)

$BASE   = "http://localhost:8000/api/v1"
$pass   = 0
$fail   = 0
$SLEEP  = 300   # ms between requests — stay under rate limit

function Test-Endpoint {
    param(
        [string]$Label,
        [string]$Url,
        [int]$ExpectedStatus = 200
    )
    Start-Sleep -Milliseconds $SLEEP
    try {
        $resp = Invoke-WebRequest -Uri $Url -Method GET -UseBasicParsing -ErrorAction Stop
        $status = $resp.StatusCode
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        if (-not $status) { $status = 0 }
    }

    if ($status -eq $ExpectedStatus) {
        Write-Host ("  PASS [{0}] {1}" -f $status, $Label) -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host ("  FAIL [{0}] {1}" -f $status, $Label) -ForegroundColor Red
        Write-Host ("       URL: {0}" -f $Url)
        Write-Host ("       Expected: {0}" -f $ExpectedStatus)
        $script:fail++
    }
}

Write-Host "=== Islam-Mate API Test Suite v3.3 ===" -ForegroundColor Cyan
Write-Host ""

# ── Health ──────────────────────────────────────────────────────────────────
Write-Host "[Health]"
Test-Endpoint "root"   "http://localhost:8000/"
Test-Endpoint "health" "http://localhost:8000/health"
Write-Host ""

# ── Prayer Times ─────────────────────────────────────────────────────────────
Write-Host "[Prayer Times]"
Test-Endpoint "prayer list methods"                   "$BASE/prayer/methods"
Test-Endpoint "prayer by coords (latitude/longitude)" "$BASE/prayer-times?latitude=30.04&longitude=31.23"
Test-Endpoint "prayer auto (IP)"                      "$BASE/prayer-times/auto"
Write-Host ""

# ── Qibla ────────────────────────────────────────────────────────────────────
Write-Host "[Qibla]"
Test-Endpoint "qibla (latitude/longitude)" "$BASE/qibla?latitude=30.04&longitude=31.23"
Write-Host ""

# ── Ramadan ──────────────────────────────────────────────────────────────────
Write-Host "[Ramadan]"
Test-Endpoint "ramadan (latitude/longitude)" "$BASE/ramadan?latitude=30.04&longitude=31.23"
Write-Host ""

# ── Hijri ─────────────────────────────────────────────────────────────────────
Write-Host "[Hijri]"
Test-Endpoint "hijri today"   "$BASE/hijri/today"
Test-Endpoint "hijri convert" "$BASE/hijri/convert?date=2025-03-01"
Test-Endpoint "hijri events"  "$BASE/hijri/events"
Write-Host ""

# ── Azkar ────────────────────────────────────────────────────────────────────
Write-Host "[Azkar]"
Test-Endpoint "azkar list"            "$BASE/azkar"
Test-Endpoint "azkar morning_evening" "$BASE/azkar/slug/morning_evening"
Test-Endpoint "azkar after_prayer"    "$BASE/azkar/slug/after_prayer"
Test-Endpoint "azkar sleep"           "$BASE/azkar/slug/sleep"
Test-Endpoint "azkar waking_up"       "$BASE/azkar/slug/waking_up"
Test-Endpoint "azkar anxiety"         "$BASE/azkar/slug/anxiety"
Write-Host ""

# ── Dua ──────────────────────────────────────────────────────────────────────
Write-Host "[Dua]"
Test-Endpoint "dua list"              "$BASE/dua"
Test-Endpoint "dua by category=sleep" "$BASE/dua/sleep"
Write-Host ""

# ── Allah Names ───────────────────────────────────────────────────────────────
Write-Host "[Allah Names]"
Test-Endpoint "names list"   "$BASE/allah-names"
Test-Endpoint "name by id=1" "$BASE/allah-names/1"
Test-Endpoint "name random"  "$BASE/allah-names/random"
Write-Host ""

# ── Hadith ────────────────────────────────────────────────────────────────────
Write-Host "[Hadith]"
Test-Endpoint "hadith collections" "$BASE/hadith"
Test-Endpoint "hadith bukhari"     "$BASE/hadith/bukhari"
Test-Endpoint "hadith bukhari/1"   "$BASE/hadith/bukhari/1"
Test-Endpoint "hadith muslim"      "$BASE/hadith/muslim"
Test-Endpoint "hadith nawawi40"    "$BASE/hadith/nawawi40"
Test-Endpoint "hadith nawawi40/1"  "$BASE/hadith/nawawi40/1"
Test-Endpoint "hadith random"      "$BASE/hadith/random"
Write-Host ""

# ── Adhan ─────────────────────────────────────────────────────────────────────
Write-Host "[Adhan]"
Test-Endpoint "adhan all"          "$BASE/adhan"
Test-Endpoint "adhan by id=1"      "$BASE/adhan/1"
Test-Endpoint "adhan random"       "$BASE/adhan/random"
Test-Endpoint "adhan muezzins"     "$BASE/adhan/muezzins"
Test-Endpoint "adhan muezzin id=1" "$BASE/adhan/muezzins/1"
Write-Host ""

# ── Location ─────────────────────────────────────────────────────────────────
Write-Host "[Location]"
Test-Endpoint "location detect" "$BASE/location/detect"
Test-Endpoint "location search" "$BASE/location/search?q=Cairo"
Test-Endpoint "location auto"   "$BASE/location/auto"
Test-Endpoint "location config" "$BASE/location/config"
Write-Host ""

# ── Zakat ─────────────────────────────────────────────────────────────────────
Write-Host "[Zakat]"
Test-Endpoint "zakat info"      "$BASE/zakat"
Test-Endpoint "zakat nisab"     "$BASE/zakat/nisab"
Test-Endpoint "zakat calculate" "$BASE/zakat/calculate"
Write-Host ""

# ── Islamic Events ────────────────────────────────────────────────────────────
Write-Host "[Islamic Events]"
Test-Endpoint "hijri events 2025"     "$BASE/hijri/events?year=2025"
Test-Endpoint "hijri events holidays" "$BASE/hijri/events?type=holiday"
Write-Host ""

# ── Al-Sharaawi ───────────────────────────────────────────────────────────────
Write-Host "[Al-Sharaawi]"
Test-Endpoint "sharaawi list"    "$BASE/alsharaawi"
Test-Endpoint "sharaawi by id=1" "$BASE/alsharaawi/1"
Test-Endpoint "sharaawi random"  "$BASE/alsharaawi/random"
Write-Host ""

# ── Summary ──────────────────────────────────────────────────────────────────
$total = $pass + $fail
Write-Host ("=== Results: {0}/{1} PASS | {2} FAIL ===" -f $pass, $total, $fail) -ForegroundColor Cyan
if ($fail -gt 0) { Write-Host "Fix the FAIL entries above then re-run." -ForegroundColor Yellow }
else             { Write-Host "All tests passing!" -ForegroundColor Green }