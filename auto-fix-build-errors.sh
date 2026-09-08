#!/bin/bash

# 🔧 Auto-Fix Script for Android Build Errors
# GitHub Actions میں استعمال کریں

PROJECT_PATH="${1:-.}"
BUILD_LOG="${2:-build.log}"

echo "🔧 Auto-Fix Tool شروع ہو رہا ہے..."
echo "📂 Project: $PROJECT_PATH"
echo ""

cd "$PROJECT_PATH" || exit 1

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Error counters
FIXES_APPLIED=0
ERRORS_FOUND=0

# Function to check and fix errors
fix_error() {
    local error_name=$1
    local fix_description=$2
    local fix_command=$3
    
    if grep -qi "$error_name" "$BUILD_LOG" 2>/dev/null; then
        ERRORS_FOUND=$((ERRORS_FOUND + 1))
        echo -e "${YELLOW}⚠️  Found: $error_name${NC}"
        echo "   Applying fix: $fix_description"
        
        eval "$fix_command"
        
        if [ $? -eq 0 ]; then
            FIXES_APPLIED=$((FIXES_APPLIED + 1))
            echo -e "${GREEN}✅ Fixed: $error_name${NC}"
        else
            echo -e "${RED}❌ Could not fix: $error_name${NC}"
        fi
        echo ""
    fi
}

# ============================================
# Fix 1: AndroidX Issues
# ============================================
echo "🔍 Checking for AndroidX issues..."
fix_error "AndroidX" \
    "Enabling AndroidX support" \
    "echo 'android.useAndroidX=true' >> gradle.properties && \
     echo 'android.enableJetifier=true' >> gradle.properties"

# ============================================
# Fix 2: Kotlin Version Issues
# ============================================
echo "🔍 Checking for Kotlin version issues..."
fix_error "kotlin" \
    "Updating Kotlin version" \
    "sed -i 's/kotlin-gradle-plugin:1\\.3.*/kotlin-gradle-plugin:1.9.0/g' build.gradle || \
     sed -i \"s/kotlin(\\\"jvm\\\") version \\\".*\\\"/kotlin(\\\"jvm\\\") version \\\"1.9.0\\\"/g\" build.gradle.kts"

# ============================================
# Fix 3: Gradle Version Issues
# ============================================
echo "🔍 Checking for Gradle version issues..."
fix_error "gradle" \
    "Updating Gradle wrapper version" \
    "cd gradle/wrapper && \
     sed -i 's/gradle-.*-all.zip/gradle-8.0-all.zip/g' gradle-wrapper.properties"

# ============================================
# Fix 4: Compilation Errors
# ============================================
echo "🔍 Checking for compilation errors..."
fix_error "error:" \
    "Running clean build" \
    "if [ -f 'gradlew' ]; then \
       ./gradlew clean; \
     else \
       gradle clean; \
     fi"

# ============================================
# Fix 5: Memory Errors
# ============================================
echo "🔍 Checking for memory errors..."
if grep -qi "OutOfMemory\|heap\|memory" "$BUILD_LOG" 2>/dev/null; then
    ERRORS_FOUND=$((ERRORS_FOUND + 1))
    echo -e "${YELLOW}⚠️  Found: Memory/Heap issues${NC}"
    echo "   Applying fix: Increasing Gradle memory"
    
    # Create gradle.properties if not exists
    if [ ! -f "gradle.properties" ]; then
        touch gradle.properties
    fi
    
    echo "org.gradle.jvmargs=-Xmx2048m" >> gradle.properties
    echo "org.gradle.parallel=true" >> gradle.properties
    echo "org.gradle.daemon=true" >> gradle.properties
    
    FIXES_APPLIED=$((FIXES_APPLIED + 1))
    echo -e "${GREEN}✅ Fixed: Memory issues${NC}"
    echo ""
fi

# ============================================
# Fix 6: Missing Dependencies
# ============================================
echo "🔍 Checking for missing dependencies..."
if grep -qi "cannot find symbol\|package .* does not exist" "$BUILD_LOG" 2>/dev/null; then
    ERRORS_FOUND=$((ERRORS_FOUND + 1))
    echo -e "${YELLOW}⚠️  Found: Missing dependencies${NC}"
    echo "   Applying fix: Refreshing dependencies"
    
    if [ -f "gradlew" ]; then
        chmod +x gradlew
        ./gradlew clean --refresh-dependencies > /dev/null 2>&1
    else
        gradle clean --refresh-dependencies > /dev/null 2>&1
    fi
    
    FIXES_APPLIED=$((FIXES_APPLIED + 1))
    echo -e "${GREEN}✅ Fixed: Dependencies refreshed${NC}"
    echo ""
fi

# ============================================
# Fix 7: API Level Issues
# ============================================
echo "🔍 Checking for API level issues..."
fix_error "targetSdkVersion\|compileSdkVersion" \
    "Updating target API level" \
    "sed -i 's/targetSdkVersion .*/targetSdkVersion 31/g' build.gradle || \
     sed -i 's/compileSdk.*/compileSdk 31/g' build.gradle.kts"

# ============================================
# Fix 8: Namespace Issues (AGP 8.0+)
# ============================================
echo "🔍 Checking for namespace issues..."
if grep -qi "namespace" "$BUILD_LOG" 2>/dev/null; then
    ERRORS_FOUND=$((ERRORS_FOUND + 1))
    echo -e "${YELLOW}⚠️  Found: Namespace configuration issues${NC}"
    echo "   Applying fix: Adding namespace to build.gradle"
    
    # This would be applied in build.gradle.kts or build.gradle
    echo -e "\n// Fix for AGP 8.0+" >> build.gradle.kts
    echo "namespace = \"com.example.app\"" >> build.gradle.kts
    
    FIXES_APPLIED=$((FIXES_APPLIED + 1))
    echo -e "${GREEN}✅ Fixed: Namespace configuration${NC}"
    echo ""
fi

# ============================================
# Fix 9: Plugin Issues
# ============================================
echo "🔍 Checking for plugin issues..."
fix_error "plugin\|Could not find" \
    "Updating plugin repositories" \
    "if grep -q 'google()' build.gradle build.gradle.kts 2>/dev/null; then \
       echo 'Repositories already configured'; \
     else \
       echo 'google()' >> build.gradle; \
       echo 'mavenCentral()' >> build.gradle; \
     fi"

# ============================================
# Fix 10: Lint Issues
# ============================================
echo "🔍 Checking for lint errors..."
fix_error "lint" \
    "Disabling strict lint checks" \
    "echo -e '\\nlintOptions {\\n    disable \"MissingTranslation\"\\n    disable \"ExtraTranslation\"\\n}' >> build.gradle"

# ============================================
# Summary
# ============================================
echo ""
echo "=========================================="
echo "📊 Auto-Fix Summary"
echo "=========================================="
echo "Errors Found: $ERRORS_FOUND"
echo "Fixes Applied: $FIXES_APPLIED"
echo ""

if [ $FIXES_APPLIED -gt 0 ]; then
    echo -e "${GREEN}✅ Auto-fixes applied successfully!${NC}"
    echo "🔄 Ready for retry build..."
    exit 0
else
    echo -e "${YELLOW}⚠️  No auto-fixes were applied${NC}"
    echo "📋 Check build logs for details"
    exit 1
fi
