# Quick Setup: Connect to Real Nova Sonic

## Step 1: Get AWS Credentials

### Option A: From AWS Console
1. Go to https://console.aws.amazon.com/iam/
2. Click "Users" → Select your user (or create new)
3. Click "Security credentials" tab
4. Click "Create access key"
5. Select "Application running outside AWS"
6. Copy the credentials shown

### Option B: From AWS CLI
```bash
# If you have AWS CLI configured
cat ~/.aws/credentials
```

### Option C: Temporary Credentials (SSO)
```bash
aws sso login
aws configure export-credentials --profile your-profile
```

## Step 2: Add Credentials to .env

Edit `/workshop/lon04-reading-coach/.env`:

```bash
# Add these lines (replace with your actual credentials)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# If using temporary credentials, also add:
# AWS_SESSION_TOKEN=your-session-token-here

# Ensure these are set:
AWS_REGION=us-west-2
READING_AGENT_TYPE=nova_sonic
```

## Step 3: Install Nova SDK

```bash
cd /workshop/lon04-reading-coach
source .venv/bin/activate
pip install aws-sdk-bedrock-runtime smithy-aws-event-stream smithy-aws-core
```

## Step 4: Restart Backend

```bash
# Kill existing backend
pkill -f uvicorn

# Start with new credentials
cd /workshop/lon04-reading-coach
uv run uvicorn src.application.api:app --host 0.0.0.0 --port 8000
```

## Step 5: Verify Nova Sonic is Active

Check logs:
```bash
tail -f /tmp/backend.log | grep -i nova
```

You should see:
```
✅ Using Nova Sonic reading agent
```

## Step 6: Test with Frontend

1. Open: https://d2ly2yw37wzs0h.cloudfront.net/ports/3000/app.html
2. Click "Start Session"
3. Speak into microphone
4. You should now get:
   - Real speech analysis
   - Intelligent feedback from Nova Sonic
   - Context-aware page turns
   - Audio responses from Fable the Fox

## Troubleshooting

### "Nova Sonic SDK not available"
- SDK requires Python 3.12+
- Check: `python --version` in .venv
- The SDK may not be publicly released yet

### "Invalid credentials"
- Verify Access Key ID starts with AKIA or ASIA
- Check for extra spaces in credentials
- Ensure session token is complete (if using temporary creds)

### "Access Denied"
Your IAM user needs these permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": "arn:aws:bedrock:*:*:model/amazon.nova-sonic-v1:0"
}
```

### "Model not found"
- Nova Sonic may not be available in your region
- Try region: us-west-2 or us-east-1
- Check if you have access to Bedrock Nova models

## Current Status

Right now you're using **SimpleReadingAgent** which:
- ✅ Receives audio
- ✅ Turns pages after ~60 audio chunks
- ❌ Doesn't analyze speech content
- ❌ Doesn't provide feedback

With **Nova Sonic** you'll get:
- ✅ Real-time speech analysis
- ✅ Reading comprehension feedback
- ✅ Pronunciation help
- ✅ Intelligent page turns based on reading completion
- ✅ Audio responses from AI coach

## Files to Edit

1. **Add credentials**: `/workshop/lon04-reading-coach/.env`
2. **Template reference**: `/workshop/lon04-reading-coach/.env.template`
3. **Current config**: Already set to use Nova Sonic when available

## Security

⚠️ **IMPORTANT**:
- Never commit `.env` to git
- Rotate credentials regularly
- Use temporary credentials when possible
- Restrict IAM permissions to minimum required
