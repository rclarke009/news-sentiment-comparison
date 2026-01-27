# ZAP Setup Guide

## Option 1: Docker (Recommended - Easiest)

This is the easiest way to get ZAP running for automated scanning:

```bash
# Start ZAP in Docker (with API access enabled)
docker run -d -p 8080:8080 --name zap zaproxy/zap-stable zap.sh -daemon -host 0.0.0.0 -port 8080 -config api.disablekey=true -config 'api.addrs.addr.name=.*' -config 'api.addrs.addr.regex=true'

# Verify it's running
docker ps | grep zap

# Check logs if needed
docker logs zap

# Stop ZAP when done
docker stop zap
docker rm zap
```

## Option 2: ZAP GUI with API Enabled

If you've downloaded and installed ZAP (double-clicked the app):

1. **Enable the API in ZAP GUI:**
   - Open ZAP
   - Go to **Tools → Options → API**
   - Check **"Enable API"**
   - Set **Address** to `0.0.0.0` (or leave as `127.0.0.1` for local only)
   - Set **Port** to `8080` (or note the port if different)
   - Click **OK**

2. **Find ZAP installation directory:**
   - On macOS, ZAP is usually installed in `/Applications/OWASP ZAP.app`
   - The command-line tools are in: `/Applications/OWASP ZAP.app/Contents/Java/zap.sh`

3. **Run ZAP from command line (alternative):**
   ```bash
   # Start ZAP in daemon mode
   /Applications/OWASP\ ZAP.app/Contents/Java/zap.sh -daemon -host 0.0.0.0 -port 8080
   ```

4. **Test the API:**
   ```bash
   # Check if API is accessible
   curl http://localhost:8080/JSON/core/view/version/
   ```

5. **If using a different port:**
   ```bash
   # Use --zap-url to specify the port
   python scripts/zap_scan.py --target https://sentiment-lens.onrender.com --zap-url http://localhost:8090
   ```

## Option 3: Install ZAP via Homebrew (macOS)

```bash
# Install ZAP
brew install --cask owasp-zap

# Start ZAP in daemon mode
/Applications/OWASP\ ZAP.app/Contents/Java/zap.sh -daemon -host 0.0.0.0 -port 8080
```

## Troubleshooting

### "ZAP did not become ready in time"

1. **Check if ZAP is actually running:**
   - GUI: Look for the ZAP window
   - Docker: `docker ps | grep zap`
   - Command line: `ps aux | grep zap`

2. **Check the port:**
   - Default is 8080
   - Try: `curl http://localhost:8080/JSON/core/view/version/`
   - If that works, ZAP API is running

3. **Check firewall:**
   - Make sure port 8080 isn't blocked

4. **Try a different port:**
   ```bash
   # If 8080 is in use, use 8090
   python scripts/zap_scan.py --target <URL> --zap-url http://localhost:8090
   ```

5. **Enable API in GUI:**
   - Tools → Options → API → Enable API

### "Connection refused"

- ZAP isn't running, or API isn't enabled
- Check the steps above

### Docker issues

- Make sure Docker is running: `docker ps`
- Check if port 8080 is already in use: `lsof -i :8080`
- Use a different port: `docker run -d -p 8090:8080 ...` then `--zap-url http://localhost:8090`
