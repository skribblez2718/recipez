#!/bin/bash
# Comprehensive API Testing Script for Recipez
# Based on OpenAPI spec at /home/user/projects/recipez/docs/openapi.yaml

source /home/user/projects/recipez/test_tokens.sh

# Output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
SKIP=0
declare -a FAILURES=()

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"
    local data="$5"
    local token="${6:-$USER_TOKEN}"
    local content_type="${7:-application/json}"

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Authorization: Bearer $token" \
            "$BASE_URL$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: $content_type" \
            -d "$data" \
            "$BASE_URL$endpoint" 2>&1)
    fi

    status=$(echo "$response" | tail -1)
    body=$(echo "$response" | head -n -1)

    if [ "$status" -eq "$expected_status" ]; then
        echo -e "${GREEN}PASS${NC}: $name (HTTP $status)"
        ((PASS++))
        echo "$body"
    else
        echo -e "${RED}FAIL${NC}: $name - Expected $expected_status, got $status"
        ((FAIL++))
        FAILURES+=("$name: Expected $expected_status, got $status. Response: $body")
        echo "$body"
    fi
    echo ""
}

echo "=============================================="
echo "       RECIPEZ API COMPREHENSIVE TESTS       "
echo "=============================================="
echo "Base URL: $BASE_URL"
echo "Started at: $(date)"
echo ""

# ==================== HEALTH ENDPOINTS ====================
echo "=== HEALTH ENDPOINTS ==="
test_endpoint "Health Check" "GET" "/health" 200
test_endpoint "Readiness Check" "GET" "/health/ready" 200

# ==================== PROFILE ENDPOINTS ====================
echo "=== PROFILE ENDPOINTS ==="
test_endpoint "Get Profile" "GET" "/api/profile/me" 200
test_endpoint "List API Keys" "GET" "/api/profile/api-keys" 200
test_endpoint "Update Profile Image" "PUT" "/api/profile/image" 200 '{"image_url":"/static/img/test.png"}'

# Create API key for testing
echo "Creating API key..."
API_KEY_RESP=$(curl -s -X POST -H "Authorization: Bearer $USER_TOKEN" -H "Content-Type: application/json" \
    -d '{"name":"Test API Key","scopes":["category:read"],"never_expires":true}' \
    "$BASE_URL/api/profile/api-keys")
echo "API Key Response: $API_KEY_RESP"
API_KEY_ID=$(echo "$API_KEY_RESP" | jq -r '.response.api_key.api_key_id // empty')
if [ -n "$API_KEY_ID" ]; then
    echo -e "${GREEN}PASS${NC}: Create API Key (HTTP 201)"
    ((PASS++))
    test_endpoint "Delete API Key" "DELETE" "/api/profile/api-keys/$API_KEY_ID" 200
else
    echo -e "${RED}FAIL${NC}: Create API Key"
    ((FAIL++))
    FAILURES+=("Create API Key: Failed to create")
fi

# ==================== CATEGORY ENDPOINTS ====================
echo "=== CATEGORY ENDPOINTS ==="
test_endpoint "Get All Categories" "GET" "/api/category/all" 200

# Create a category for testing
CAT_RESP=$(curl -s -X POST -H "Authorization: Bearer $USER_TOKEN" -H "Content-Type: application/json" \
    -d '{"category_name":"API Test Category"}' \
    "$BASE_URL/api/category/create")
echo "Create Category Response: $CAT_RESP"
CAT_ID=$(echo "$CAT_RESP" | jq -r '.response.category.category_id // empty')
if [ -n "$CAT_ID" ]; then
    echo -e "${GREEN}PASS${NC}: Create Category"
    ((PASS++))

    test_endpoint "Get Category" "GET" "/api/category/$CAT_ID" 200
    test_endpoint "Update Category" "PUT" "/api/category/update/$CAT_ID" 200 '{"category_name":"API Test Category Updated"}'
    test_endpoint "Preview Delete Category" "GET" "/api/category/delete/$CAT_ID/preview" 200
else
    echo -e "${RED}FAIL${NC}: Create Category"
    ((FAIL++))
    FAILURES+=("Create Category: Failed to create")
    CAT_ID=""
fi

# ==================== IMAGE ENDPOINTS ====================
echo "=== IMAGE ENDPOINTS ==="
# Create a minimal test image (1x1 PNG base64)
TEST_IMAGE_B64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
IMG_RESP=$(curl -s -X POST -H "Authorization: Bearer $USER_TOKEN" -H "Content-Type: application/json" \
    -d "{\"image_data\":\"$TEST_IMAGE_B64\",\"image_path\":\"api-test-image.png\"}" \
    "$BASE_URL/api/image/create")
echo "Create Image Response: $IMG_RESP"
IMG_ID=$(echo "$IMG_RESP" | jq -r '.response.image.image_id // empty')
if [ -n "$IMG_ID" ]; then
    echo -e "${GREEN}PASS${NC}: Create Image"
    ((PASS++))
else
    echo -e "${YELLOW}WARN${NC}: Create Image might have failed, checking for existing default image"
    # Use a default image ID if creation failed
    IMG_ID=""
fi

# ==================== RECIPE ENDPOINTS ====================
echo "=== RECIPE ENDPOINTS ==="
test_endpoint "Get All Recipes" "GET" "/api/recipe/all" 200

# Need both category and image to create recipe
if [ -n "$CAT_ID" ]; then
    # Try to get an image ID if we don't have one
    if [ -z "$IMG_ID" ]; then
        # Query for any existing image (use first from a recipe)
        RECIPES=$(curl -s -H "Authorization: Bearer $USER_TOKEN" "$BASE_URL/api/recipe/all")
        IMG_ID=$(echo "$RECIPES" | jq -r '.[0].recipe_image.image_id // .response[0].recipe_image.image_id // empty')
    fi

    if [ -n "$IMG_ID" ]; then
        # Create recipe
        RECIPE_RESP=$(curl -s -X POST -H "Authorization: Bearer $USER_TOKEN" -H "Content-Type: application/json" \
            -d "{\"recipe_name\":\"API Test Recipe\",\"recipe_description\":\"Test recipe created by API tests\",\"recipe_category_id\":\"$CAT_ID\",\"recipe_image_id\":\"$IMG_ID\"}" \
            "$BASE_URL/api/recipe/create")
        echo "Create Recipe Response: $RECIPE_RESP"
        RECIPE_ID=$(echo "$RECIPE_RESP" | jq -r '.response.recipe.recipe_id // empty')

        if [ -n "$RECIPE_ID" ]; then
            echo -e "${GREEN}PASS${NC}: Create Recipe"
            ((PASS++))

            test_endpoint "Get Recipe" "GET" "/api/recipe/$RECIPE_ID" 200
            test_endpoint "Update Recipe" "PUT" "/api/recipe/update/$RECIPE_ID" 200 '{"recipe_name":"API Test Recipe Updated","recipe_description":"Updated description"}'

            # ==================== INGREDIENT ENDPOINTS ====================
            echo "=== INGREDIENT ENDPOINTS ==="
            ING_RESP=$(curl -s -X POST -H "Authorization: Bearer $USER_TOKEN" -H "Content-Type: application/json" \
                -d "{\"recipe_id\":\"$RECIPE_ID\",\"ingredients\":[{\"ingredient_name\":\"Test Ingredient\",\"ingredient_quantity\":\"1\",\"ingredient_measurement\":\"cup\"}]}" \
                "$BASE_URL/api/ingredient/create")
            echo "Create Ingredient Response: $ING_RESP"
            ING_ID=$(echo "$ING_RESP" | jq -r '.response.ingredients[0].ingredient_id // empty')
            if [ -n "$ING_ID" ]; then
                echo -e "${GREEN}PASS${NC}: Create Ingredient"
                ((PASS++))
                test_endpoint "Get Ingredient" "GET" "/api/ingredient/$ING_ID" 200
                test_endpoint "Update Ingredient" "PUT" "/api/ingredient/update/$ING_ID" 200 '{"ingredient_name":"Updated Ingredient","ingredient_quantity":"2","ingredient_measurement":"tablespoon"}'
                test_endpoint "Delete Ingredient" "DELETE" "/api/ingredient/delete/$ING_ID" 200
            else
                echo -e "${RED}FAIL${NC}: Create Ingredient"
                ((FAIL++))
                FAILURES+=("Create Ingredient: Failed to create")
            fi

            # ==================== STEP ENDPOINTS ====================
            echo "=== STEP ENDPOINTS ==="
            STEP_RESP=$(curl -s -X POST -H "Authorization: Bearer $USER_TOKEN" -H "Content-Type: application/json" \
                -d "{\"recipe_id\":\"$RECIPE_ID\",\"steps\":[{\"step_description\":\"Test step instructions\"}]}" \
                "$BASE_URL/api/step/create")
            echo "Create Step Response: $STEP_RESP"
            STEP_ID=$(echo "$STEP_RESP" | jq -r '.response.steps[0].step_id // empty')
            if [ -n "$STEP_ID" ]; then
                echo -e "${GREEN}PASS${NC}: Create Step"
                ((PASS++))
                test_endpoint "Get Steps by Recipe" "GET" "/api/step/$RECIPE_ID" 200
                test_endpoint "Update Step" "PUT" "/api/step/update/$STEP_ID" 200 '{"step_description":"Updated step instructions"}'
                test_endpoint "Delete Step" "DELETE" "/api/step/delete/$STEP_ID" 200
            else
                echo -e "${RED}FAIL${NC}: Create Step"
                ((FAIL++))
                FAILURES+=("Create Step: Failed to create")
            fi

            # Batch update category test
            test_endpoint "Batch Update Recipe Category" "POST" "/api/recipe/batch-update-category" 200 \
                "{\"updates\":[{\"recipe_id\":\"$RECIPE_ID\",\"category_id\":\"$CAT_ID\"}]}"

            # Delete recipe at the end
            test_endpoint "Delete Recipe" "DELETE" "/api/recipe/delete/$RECIPE_ID" 200
        else
            echo -e "${RED}FAIL${NC}: Create Recipe"
            ((FAIL++))
            FAILURES+=("Create Recipe: Failed to create")
        fi
    else
        echo -e "${YELLOW}SKIP${NC}: Recipe tests - no image available"
        ((SKIP++))
    fi
fi

# Delete category at end
if [ -n "$CAT_ID" ]; then
    test_endpoint "Delete Category" "DELETE" "/api/category/delete/$CAT_ID" 200
fi

# Delete image at end
if [ -n "$IMG_ID" ]; then
    test_endpoint "Delete Image" "DELETE" "/api/image/delete/$IMG_ID" 200
fi

# ==================== AI ENDPOINTS ====================
echo "=== AI ENDPOINTS ==="
test_endpoint "AI Create Recipe" "POST" "/api/ai/create" 200 '{"message":"Create a simple pasta recipe"}'

# ==================== GROCERY ENDPOINT ====================
echo "=== GROCERY ENDPOINT ==="
# Skip if no recipes with ingredients exist
echo -e "${YELLOW}SKIP${NC}: Grocery send requires recipe with ingredients and email service"
((SKIP++))

# ==================== EMAIL ENDPOINTS ====================
echo "=== EMAIL ENDPOINTS ==="
# These will send actual emails, so we test that they accept correct format but may fail due to no SMTP
test_endpoint "Email Recipe Share (format check)" "POST" "/api/email/recipe-share" 200 \
    '{"email":"test@example.com","recipe_name":"Test Recipe","recipe_link":"https://example.com/recipe","sender_name":"API Test"}'

# ==================== SYSTEM USER ENDPOINTS ====================
echo "=== SYSTEM USER ENDPOINTS (yeschef) ==="
test_endpoint "User Read by Email (system)" "POST" "/api/user/read/email" 200 '{"email":"apitest@example.com"}' "$SYSTEM_TOKEN"

# Code endpoints - create, read, verify, delete
echo "Creating verification code..."
CODE_RESP=$(curl -s -X POST -H "Authorization: Bearer $SYSTEM_TOKEN" -H "Content-Type: application/json" \
    -d '{"email":"codetest@example.com","session_id":"test-session-id"}' \
    "$BASE_URL/api/code/create")
echo "Create Code Response: $CODE_RESP"
CODE_VALUE=$(echo "$CODE_RESP" | jq -r '.response.code // empty')
if [ -n "$CODE_VALUE" ]; then
    echo -e "${GREEN}PASS${NC}: Create Code"
    ((PASS++))

    # Read code
    test_endpoint "Read Code (system)" "POST" "/api/code/read" 200 \
        '{"email":"codetest@example.com","session_id":"test-session-id"}' "$SYSTEM_TOKEN"

    # Delete code
    READ_RESP=$(curl -s -X POST -H "Authorization: Bearer $SYSTEM_TOKEN" -H "Content-Type: application/json" \
        -d '{"email":"codetest@example.com","session_id":"test-session-id"}' \
        "$BASE_URL/api/code/read")
    CODE_ID=$(echo "$READ_RESP" | jq -r '.response.code.code_id // empty')
    if [ -n "$CODE_ID" ]; then
        test_endpoint "Delete Code (system)" "POST" "/api/code/delete" 200 "{\"code_id\":\"$CODE_ID\"}" "$SYSTEM_TOKEN"
    fi
else
    echo -e "${RED}FAIL${NC}: Create Code"
    ((FAIL++))
    FAILURES+=("Create Code: Failed to create")
fi

# ==================== ERROR HANDLING TESTS ====================
echo "=== ERROR HANDLING TESTS ==="
test_endpoint "Missing Auth Header" "GET" "/api/profile/me" 401 "" ""
test_endpoint "Invalid UUID" "GET" "/api/recipe/not-a-uuid" 400
test_endpoint "Non-existent Recipe" "GET" "/api/recipe/00000000-0000-0000-0000-000000000000" 404
test_endpoint "Invalid Category Name" "POST" "/api/category/create" 400 '{"category_name":"!@#$%"}'
test_endpoint "Missing Required Field" "POST" "/api/recipe/create" 400 '{"recipe_name":"Test"}'

# ==================== SUMMARY ====================
echo ""
echo "=============================================="
echo "                 TEST SUMMARY                 "
echo "=============================================="
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
echo -e "Skipped: ${YELLOW}$SKIP${NC}"
echo ""

if [ ${#FAILURES[@]} -gt 0 ]; then
    echo "=== FAILURES DETAIL ==="
    for failure in "${FAILURES[@]}"; do
        echo -e "${RED}$failure${NC}"
        echo ""
    done
fi

echo "Completed at: $(date)"
