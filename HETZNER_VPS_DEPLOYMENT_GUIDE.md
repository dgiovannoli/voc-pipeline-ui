# Hetzner VPS Deployment Guide: Real-Time Embedding Webhook

## Overview
This guide walks you through deploying your FastAPI webhook server to a Hetzner VPS for real-time embedding updates. The webhook will automatically embed and upsert new/updated records from Supabase to Pinecone.

## Prerequisites
- Hetzner VPS with root access
- Your VPS IP address and root password
- Your project code (GitHub repo or local files)
- OpenAI API key
- Pinecone API key

---

## Step 1: Connect to Your Hetzner VPS

1. **Open Terminal on your Mac**
2. **Connect to your VPS:**
   ```bash
   ssh root@<your-vps-ip>
   ```
   - Replace `<your-vps-ip>` with your actual VPS IP address
   - First time connection may ask to trust the host - type `yes`
   - Enter your root password (it won't show as you type)

**Example:**
```bash
ssh root@123.456.789.10
```

---

## Step 2: Update Server and Install Dependencies

Run these commands one by one:

```bash
# Update package list and upgrade existing packages
apt update && apt upgrade -y

# Install Python, pip, virtual environment, and git
apt install python3 python3-pip python3-venv git -y
```

**What this does:**
- Updates your server's software
- Installs Python 3 and essential tools
- Installs git for cloning your repository

---

## Step 3: Get Your Project Code

### Option A: Clone from GitHub (Recommended)
```bash
# Clone your repository
git clone <your-git-repo-url>

# Navigate to the project directory
cd voc-pipeline-ui
```

**Replace `<your-git-repo-url>` with your actual GitHub URL**

### Option B: Upload Local Files
If you prefer to upload your local files:
1. Use SFTP or SCP to transfer files
2. Or zip your project and upload via Hetzner console
3. Unzip on the server: `unzip your-project.zip`

---

## Step 4: Set Up Python Virtual Environment

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install additional packages needed for the webhook
pip install fastapi uvicorn pinecone-client openai python-dotenv
```

**What this does:**
- Creates an isolated Python environment
- Installs all required packages
- Ensures clean dependency management

---

## Step 5: Configure Environment Variables

1. **Create a .env file:**
   ```bash
   nano .env
   ```

2. **Add your API keys (replace with your actual keys):**
   ```
   OPENAI_API_KEY=sk-your-openai-key-here
   PINECONE_API_KEY=your-pinecone-key-here
   PINECONE_INDEX=client-voc-embeddings
   ```

3. **Save the file:**
   - Press `Ctrl + O` (write out)
   - Press `Enter` (confirm filename)
   - Press `Ctrl + X` (exit nano)

**Security Note:** Keep your API keys secure and never share them publicly.

---

## Step 6: Test the Setup

```bash
# Make sure you're in the project directory and virtual environment is active
cd voc-pipeline-ui
source .venv/bin/activate

# Test that everything is working
python -c "import fastapi, uvicorn, pinecone, openai; print('All packages imported successfully!')"
```

You should see: `All packages imported successfully!`

---

## Step 7: Run the Webhook Server

```bash
# Make sure virtual environment is active
source .venv/bin/activate

# Start the FastAPI server
uvicorn realtime_embed_webhook:app --host 0.0.0.0 --port 8080
```

**What this does:**
- Starts your webhook server on port 8080
- Makes it accessible from the internet
- Listens for POST requests from Supabase

**Keep this running!** (You can open a new SSH window for other commands)

---

## Step 8: Configure Firewall

```bash
# Allow traffic on port 8080
ufw allow 8080

# Enable the firewall
ufw enable
```

**What this does:**
- Opens port 8080 for incoming webhook requests
- Enables the firewall for security

---

## Step 9: Set Up Supabase Webhook

1. **Go to your Supabase Dashboard**
2. **Navigate to Database → Webhooks**
3. **Create a new webhook:**
   - **Name:** `embedding-webhook`
   - **URL:** `http://<your-vps-ip>:8080/webhook`
   - **Events:** Select `INSERT` and `UPDATE`
   - **Table:** Choose your target table (e.g., `stage3_findings`)
   - **Payload:** Full record (default)

**Example URL:** `http://123.456.789.10:8080/webhook`

---

## Step 10: Test the End-to-End Flow

1. **Add or update a record in Supabase**
2. **Watch your VPS terminal for logs:**
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8080
   INFO:     Received webhook payload: {...}
   INFO:     Upserted finding <id> to Pinecone.
   ```

3. **Check Pinecone to verify the embedding was added**

---

## Step 11: Make It Production-Ready (Optional)

### Keep Server Running After Reboot
Create a systemd service:

```bash
# Create service file
nano /etc/systemd/system/embedding-webhook.service
```

Add this content:
```ini
[Unit]
Description=Embedding Webhook Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/voc-pipeline-ui
Environment=PATH=/root/voc-pipeline-ui/.venv/bin
ExecStart=/root/voc-pipeline-ui/.venv/bin/uvicorn realtime_embed_webhook:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
systemctl daemon-reload
systemctl enable embedding-webhook
systemctl start embedding-webhook
```

### Add HTTPS (Recommended for Production)
1. Install Caddy: `apt install caddy`
2. Configure Caddyfile for your domain
3. Update Supabase webhook to use HTTPS URL

---

## Troubleshooting

### Common Issues:

1. **"Command not found: uvicorn"**
   - Make sure virtual environment is activated: `source .venv/bin/activate`

2. **"Permission denied"**
   - Make sure you're running as root or have proper permissions

3. **"Connection refused"**
   - Check if port 8080 is open: `ufw status`
   - Verify server is running: `netstat -tlnp | grep 8080`

4. **"API key error"**
   - Check your .env file has correct API keys
   - Verify keys are valid in OpenAI/Pinecone dashboards

### Useful Commands:
```bash
# Check if server is running
ps aux | grep uvicorn

# Check logs
journalctl -u embedding-webhook -f

# Test webhook endpoint
curl -X POST http://localhost:8080/webhook -H "Content-Type: application/json" -d '{"test": "data"}'
```

---

## Security Considerations

1. **Use HTTPS in production**
2. **Add authentication to webhook endpoint**
3. **Regular security updates: `apt update && apt upgrade`**
4. **Monitor logs for suspicious activity**
5. **Use non-root user for production**

---

## Next Steps

1. **Monitor the webhook logs** to ensure it's working
2. **Set up monitoring/alerting** for production
3. **Consider adding a job queue** for high-volume scenarios
4. **Implement webhook authentication** for security

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all steps were completed correctly
3. Check server logs for error messages
4. Ensure all API keys are valid and have proper permissions

---

**Your real-time embedding webhook is now live and will automatically update Pinecone whenever new data is added to Supabase!** 🚀 