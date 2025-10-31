# Local Testing on Mac (Without Hardware)

This server can now run on your Mac without Raspberry Pi hardware! The code automatically detects missing hardware libraries and switches to a mock/dummy mode that prints color changes to the console.

## Setup

1. **Install Python dependencies** (without the hardware-specific ones):
   ```bash
   pip install flask flask_cors jsmin python-dotenv requests
   ```

   Note: You can skip installing `unicornhat`, `unicornhatmini`, `gpiozero`, and `RPi.GPIO` - they're not needed for testing.

2. **Optional: Create a `.env` file** for configuration:
   ```bash
   cp .env.example .env
   # Edit .env to configure:
   # - Webhook URLs (if you want to test those)
   # - STARTUP_MODE (OFF, AVAILABLE, BUSY, AWAY, or RAINBOW)
   ```

## Running the Server

Start the server:
```bash
python server.py
```

You should see output like:
```
Hardware libraries not available. Running in mock mode.
gpiozero not available. CPU temperature will be mocked.
🦄 DummyHat initialized (8x4 grid)
🔆 Brightness set to: 1
🔄 Rotation set to: 90°
Starting up in RAINBOW mode
 * Running on http://0.0.0.0:5000/
```

### Configuration Options

You can configure the server behavior using environment variables in your `.env` file:

**Startup Mode** - The initial display mode when the server starts:
```bash
# In your .env file:
STARTUP_MODE=OFF         # Start with display off
# or
STARTUP_MODE=AVAILABLE   # Start showing green (available)
# or
STARTUP_MODE=BUSY        # Start showing red (busy)
# or
STARTUP_MODE=AWAY        # Start showing yellow (away)
# or
STARTUP_MODE=RAINBOW     # Start with rainbow animation (default)
```

**Port** - The port the server listens on:
```bash
PORT=5000    # Default (recommended for macOS to avoid AirPlay conflict)
# or
PORT=5001    # Original default
# or
PORT=8080    # Any other port you prefer
```

## Testing the Endpoints

### Using curl:

**Available (Green):**
```bash
curl -X POST http://localhost:5000/api/available
```
Console output: `💡 Display: RGB(0, 144, 0) - GREEN (Available)`

**Busy (Red):**
```bash
curl -X POST http://localhost:5000/api/busy
```
Console output: `💡 Display: RGB(179, 0, 0) - RED (Busy)`

**Away (Yellow):**
```bash
curl -X POST http://localhost:5000/api/away
```
Console output: `💡 Display: RGB(255, 191, 0) - YELLOW (Away)`

**Off:**
```bash
curl -X POST http://localhost:5000/api/off
```
Console output: `💡 Display: [OFF]`

**Rainbow:**
```bash
curl -X POST http://localhost:5000/api/rainbow \
  -H "Content-Type: application/json" \
  -d '{"brightness": 0.8, "speed": 0.1}'
```
Or simply:
```bash
curl http://localhost:5000/api/rainbow
```
Console output: Multiple color changes displaying the rainbow animation

**Status:**
```bash
curl http://localhost:5000/api/status
```
Returns JSON with current state, including the mock CPU temperature (42.0°C)

### Using the Browser:

1. Open http://localhost:5000/ to access the frontend
2. Click the status buttons to change states
3. Watch the console where you ran `python server.py` to see the color changes

## What You'll See

The DummyHat mock will print to the console:
- 🦄 Initialization messages
- 🔆 Brightness changes
- 🔄 Rotation changes
- 💡 Color changes with RGB values and human-readable color names

## Webhook Testing

If you configure webhook URLs in your `.env` file, you'll also see webhook call logs:
```
Webhook called for Available: 200
```

Or error messages if webhooks fail:
```
Webhook error for Busy: Connection refused
```

## Notes

- The mock mode simulates an 8x4 pixel grid (same as Unicorn pHAT)
- CPU temperature is mocked as 42.0°C
- All endpoints work exactly the same as on Raspberry Pi
- The frontend will work normally and display status changes

