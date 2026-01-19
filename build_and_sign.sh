#!/bin/bash

# build_and_sign.sh
# Script to build, sign, and copy the APK to the project root
# Usage: ./build_and_sign.sh [debug|release]

set -e

BUILD_TYPE="${1:-debug}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="lotm-reader"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "=================================================="
echo "Lord of the Mysteries Reader - Build Script"
echo "=================================================="
echo ""
echo "Project Root: $PROJECT_ROOT"
echo "Build Type: $BUILD_TYPE"
echo ""

cd "$PROJECT_ROOT"

if [ "$BUILD_TYPE" = "release" ]; then
    echo "Building RELEASE APK..."
    echo ""
    
    KEYSTORE_FILE="$PROJECT_ROOT/release.keystore"
    KEYSTORE_ALIAS="lotm-reader-key"
    
    if [ ! -f "$KEYSTORE_FILE" ]; then
        echo "⚠️  Keystore not found. Generating new keystore..."
        echo ""
        echo "Please enter keystore password (will be used for signing):"
        
        keytool -genkeypair \
            -keystore "$KEYSTORE_FILE" \
            -alias "$KEYSTORE_ALIAS" \
            -keyalg RSA \
            -keysize 2048 \
            -validity 10000 \
            -dname "CN=LoTM Reader, OU=Development, O=Reader, L=City, ST=State, C=US"
        
        echo ""
        echo "✓ Keystore generated at: $KEYSTORE_FILE"
        echo "  Alias: $KEYSTORE_ALIAS"
        echo ""
        echo "IMPORTANT: Save this keystore file securely!"
        echo "You'll need it to sign future updates."
        echo ""
    fi
    
    if [ ! -f "$PROJECT_ROOT/keystore.properties" ]; then
        echo "Creating keystore.properties file..."
        cat > "$PROJECT_ROOT/keystore.properties" << EOF
storeFile=$KEYSTORE_FILE
storePassword=CHANGE_ME
keyAlias=$KEYSTORE_ALIAS
keyPassword=CHANGE_ME
EOF
        echo ""
        echo "⚠️  Edit keystore.properties and set your passwords!"
        echo "   File: $PROJECT_ROOT/keystore.properties"
        echo ""
        read -p "Press Enter after updating passwords..." 
    fi
    
    if ! grep -q "signingConfigs" "$PROJECT_ROOT/app/build.gradle.kts"; then
        echo ""
        echo "⚠️  WARNING: Signing configuration not found in build.gradle.kts"
        echo "   You need to add signing configuration for release builds."
        echo "   See: https://developer.android.com/studio/publish/app-signing"
        echo ""
    fi
    
    ./gradlew clean assembleRelease
    
    SOURCE_APK="$PROJECT_ROOT/app/build/outputs/apk/release/app-release.apk"
    OUTPUT_APK="$PROJECT_ROOT/${APP_NAME}-release-${TIMESTAMP}.apk"
    LATEST_APK="$PROJECT_ROOT/${APP_NAME}-release-latest.apk"
    
    if [ -f "$SOURCE_APK" ]; then
        cp "$SOURCE_APK" "$OUTPUT_APK"
        cp "$SOURCE_APK" "$LATEST_APK"
        
        echo ""
        echo "=================================================="
        echo "✓ BUILD SUCCESSFUL"
        echo "=================================================="
        echo ""
        echo "Release APK copied to:"
        echo "  • $OUTPUT_APK"
        echo "  • $LATEST_APK"
        echo ""
        
        APK_SIZE=$(du -h "$OUTPUT_APK" | cut -f1)
        echo "APK Size: $APK_SIZE"
        echo ""
        
        if command -v apksigner &> /dev/null; then
            echo "Verifying APK signature..."
            apksigner verify --verbose "$OUTPUT_APK" && echo "✓ APK signature verified" || echo "⚠️  Signature verification failed"
            echo ""
        fi
        
        echo "To install on device:"
        echo "  adb install -r $LATEST_APK"
        echo ""
    else
        echo ""
        echo "❌ ERROR: Release APK not found at expected location"
        echo "   Expected: $SOURCE_APK"
        exit 1
    fi
    
else
    echo "Building DEBUG APK..."
    echo ""
    
    ./gradlew clean assembleDebug
    
    SOURCE_APK="$PROJECT_ROOT/app/build/outputs/apk/debug/app-debug.apk"
    OUTPUT_APK="$PROJECT_ROOT/${APP_NAME}-debug-${TIMESTAMP}.apk"
    LATEST_APK="$PROJECT_ROOT/${APP_NAME}-debug-latest.apk"
    
    if [ -f "$SOURCE_APK" ]; then
        cp "$SOURCE_APK" "$OUTPUT_APK"
        cp "$SOURCE_APK" "$LATEST_APK"
        
        echo ""
        echo "=================================================="
        echo "✓ BUILD SUCCESSFUL"
        echo "=================================================="
        echo ""
        echo "Debug APK copied to:"
        echo "  • $OUTPUT_APK"
        echo "  • $LATEST_APK"
        echo ""
        
        APK_SIZE=$(du -h "$OUTPUT_APK" | cut -f1)
        echo "APK Size: $APK_SIZE"
        echo ""
        
        echo "To install on device:"
        echo "  adb install -r $LATEST_APK"
        echo ""
        echo "Or use the build script with auto-install:"
        echo "  ./build_and_sign.sh debug install"
        echo ""
    else
        echo ""
        echo "❌ ERROR: Debug APK not found at expected location"
        echo "   Expected: $SOURCE_APK"
        exit 1
    fi
fi

if [ "$2" = "install" ] || [ "$2" = "-i" ]; then
    echo "=================================================="
    echo "Installing to connected device..."
    echo "=================================================="
    echo ""
    
    if command -v adb &> /dev/null; then
        DEVICE_COUNT=$(adb devices | grep -c "device$" || true)
        
        if [ "$DEVICE_COUNT" -eq 0 ]; then
            echo "❌ No Android devices connected"
            echo ""
            echo "Connect a device via USB or start an emulator, then run:"
            echo "  adb install -r $LATEST_APK"
            echo ""
            exit 1
        elif [ "$DEVICE_COUNT" -eq 1 ]; then
            echo "Installing to device..."
            adb install -r "$LATEST_APK"
            echo ""
            echo "✓ App installed successfully!"
            echo ""
            echo "To launch the app:"
            echo "  adb shell am start -n com.reader.lotm/.MainActivity"
            echo ""
        else
            echo "Multiple devices detected:"
            adb devices
            echo ""
            echo "Specify device with:"
            echo "  adb -s <device_id> install -r $LATEST_APK"
            echo ""
        fi
    else
        echo "❌ adb not found in PATH"
        echo ""
        echo "Install Android SDK Platform Tools to use adb"
        echo "Then manually install: $LATEST_APK"
        echo ""
    fi
fi

echo "=================================================="
echo "Build output files in project root:"
ls -lh "$PROJECT_ROOT"/*.apk 2>/dev/null || echo "  (no APK files yet)"
echo ""
echo "To clean old APK files:"
echo "  rm $PROJECT_ROOT/*.apk"
echo "=================================================="
echo ""
