# Environment Setup - Detailed Guide

## Step 3: Set Up Environment - Complete Instructions

The environment setup is crucial because the application needs your Google Maps API key to function. Here's exactly what to do:

### 3a. Copy the Environment Template

```bash
cp .env.example .env
```

This command creates a new file called `.env` by copying the template `.env.example`. The template looks like this:

```
# Google Maps API Configuration
GOOGLE_MAPS_API_KEY=YOUR_API_KEY_HERE

# Optional: Streamlit Configuration
# STREAMLIT_SERVER_PORT=8501
```

### 3b. Edit the .env File

You need to replace `YOUR_API_KEY_HERE` with your actual Google Maps API key. Here's how:

**Option 1: Using a Text Editor**
```bash
# On Mac/Linux
nano .env
# or
vim .env
# or
code .env  # if you have VS Code

# On Windows
notepad .env
```

**Option 2: Using Command Line**
```bash
# On Mac/Linux
echo "GOOGLE_MAPS_API_KEY=your_actual_api_key_here" > .env  # pragma: allowlist secret

# Make sure to replace 'your_actual_api_key_here' with your real key
```

### 3c. Getting a Google Maps API Key (If You Don't Have One)

1. **Go to Google Cloud Console**
   - Visit https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a New Project** (or use existing)
   - Click "Select a project" → "New Project"
   - Name it something like "ECE-Tool"
   - Click "Create"

3. **Enable Required APIs**
   - Go to "APIs & Services" → "Library"
   - Search for and enable these THREE APIs:
     - **Geocoding API** (for converting addresses to coordinates)
     - **Places API** (for finding competitors)
     - **Routes API** (for distance/drive time calculations)

4. **Create API Key**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the generated key

5. **Secure Your Key** (Optional but Recommended)
   - Click on your API key
   - Under "API restrictions", select "Restrict key"
   - Choose only the 3 APIs you enabled
   - Under "Application restrictions", you can add IP addresses if needed

### 3d. Verify Your .env File

After editing, your `.env` file should look something like this:

```
# Google Maps API Configuration
GOOGLE_MAPS_API_KEY=AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY  # pragma: allowlist secret
```
(Note: This is a fake key for example purposes)

**To verify it's set correctly:**
```bash
# Check if the file exists and has content
cat .env

# Should output something like:
# GOOGLE_MAPS_API_KEY=AIzaSyD-9tSrke72PouQMnMX-a7eZSW0jkFMBWY  # pragma: allowlist secret
```

### 3e. Important Notes

1. **Keep Your API Key Secret**
   - Never commit `.env` to git (it's already in .gitignore)
   - Don't share your API key publicly
   - Each developer should use their own key

2. **API Key Costs**
   - Google provides $200 free credit monthly
   - The app uses approximately:
     - Geocoding: $5 per 1,000 requests
     - Places Nearby: $32 per 1,000 requests
     - Routes: $5 per 1,000 requests
   - Analyzing 400 schools costs roughly $200

3. **Troubleshooting API Key Issues**

   **"Invalid API key" Error:**
   - Check you copied the key correctly (no extra spaces)
   - Ensure all 3 APIs are enabled in Google Cloud Console
   - Wait 5 minutes after creating a new key (propagation delay)
   - Check API key restrictions aren't too strict

   **"Quota exceeded" Error:**
   - Check your Google Cloud billing/quotas
   - You may need to enable billing (even for free tier)

### 3f. Alternative: Using Streamlit Secrets (for Streamlit Cloud)

If deploying to Streamlit Cloud, you can use their secrets management:

1. Don't create a `.env` file
2. In Streamlit Cloud dashboard, go to app settings
3. Add secret:
   ```toml
   GOOGLE_MAPS_API_KEY = "your_api_key_here"  # pragma: allowlist secret
   ```

### Quick Test After Setup

To verify your API key works:
```bash
# Run this Python test
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('GOOGLE_MAPS_API_KEY')
if key and key != 'YOUR_API_KEY_HERE':
    print('✅ API key is set!')
    print(f'   Key starts with: {key[:10]}...')
else:
    print('❌ API key not set properly')
"
```

### Visual Guide: Google Cloud Console

Here's what to look for in the Google Cloud Console:

1. **APIs & Services Dashboard**
   - You should see all 3 APIs listed as "Enabled"
   - Geocoding API ✓
   - Places API ✓
   - Routes API ✓

2. **API Key Restrictions**
   - API restrictions: "Restrict key"
   - Selected APIs: Only the 3 APIs above
   - This prevents unauthorized usage

3. **Monitoring Usage**
   - Check "APIs & Services" → "Metrics"
   - Monitor your API usage to stay within free tier
   - Set up billing alerts if needed

### Next Steps

Once your `.env` file is properly configured with a valid Google Maps API key:

1. **Test the setup:**
   ```bash
   ./scripts/verify-setup.sh
   ```

2. **Run the application:**
   ```bash
   # With Docker
   docker-compose up

   # Or with Python
   streamlit run app.py
   ```

3. **Verify it works:**
   - The app should load without API errors
   - Try a single location analysis
   - Check that competitor data loads

If you encounter any issues, refer to the troubleshooting section above or check the [INSTALL.md](../INSTALL.md) file for more help.
