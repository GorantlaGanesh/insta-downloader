const express = require('express');
const cors = require('cors');
const { exec, execSync } = require('child_process');

const app = express();
app.use(cors());
app.use(express.json());
app.use('/files', express.static('/tmp'));

// Install yt-dlp on startup
try {
  execSync('pip install yt-dlp', { stdio: 'inherit' });
  console.log('yt-dlp installed successfully');
} catch (e) {
  try {
    execSync('pip3 install yt-dlp', { stdio: 'inherit' });
    console.log('yt-dlp installed via pip3');
  } catch (e2) {
    console.error('Could not install yt-dlp:', e2.message);
  }
}

app.post('/download', (req, res) => {
  const { url } = req.body;
  if (!url) return res.status(400).json({ error: 'No URL provided' });

  const filename = `video_${Date.now()}.mp4`;
  const filepath = `/tmp/${filename}`;

  // Try multiple yt-dlp paths
  const ytdlp = 'python3 -m yt_dlp';

  const cmd = `${ytdlp} \
    --no-check-certificate \
    --add-header "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
    -o "${filepath}" \
    --merge-output-format mp4 \
    "${url}"`;

  exec(cmd, { timeout: 120000 }, (error, stdout, stderr) => {
    if (error) {
      console.error(stderr);
      return res.status(500).json({ 
        error: 'Download failed', 
        details: stderr 
      });
    }
    const fileUrl = `${req.protocol}://${req.get('host')}/files/${filename}`;
    res.json({ success: true, video_url: fileUrl, filename });
  });
});

app.get('/health', (req, res) => res.json({ status: 'ok' }));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Running on port ${PORT}`));
