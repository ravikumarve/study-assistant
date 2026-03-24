# Demo GIF Creation Guide

## Tools Needed
- `peek` (Linux screen recorder) or OBS Studio
- `ffmpeg` for GIF conversion
- Google Chrome or Firefox

## Steps to Create Demo GIF

1. **Start the application:**
   ```bash
   python app.py
   ```

2. **Record screen with peek:**
   ```bash
   # Install peek on Ubuntu/Debian
   sudo apt install peek
   
   # Record 30-second demo
   peek -g -d 30 -o demo-recording.mp4
   ```

3. **Convert to GIF:**
   ```bash
   ffmpeg -i demo-recording.mp4 -vf "fps=10,scale=800:-1:flags=lanczos" -c:v gif -f gif demo.gif
   ```

4. **Optimize GIF:**
   ```bash
   gifsicle -O3 demo.gif -o demo-optimized.gif
   ```

## Demo Content to Record
- Application startup
- Navigation between features
- AI explanation generation
- Quiz interaction
- Flashcard flipping
- Theme switching
- Mobile responsive view