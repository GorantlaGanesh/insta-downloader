const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');

const app = express();
app.use(cors());
app.use(express.json());
app.use('/files', express.static('/tmp'));

app.post('/download', (req, res) => {
  const { url } = req.body;
  if (!url) return res.status(400).json({ error: 'No URL provided' });

  const filename = `video_${Date.now()}.mp4`;
  const filepath = `/tmp/${filename}`;

  const cmd = `yt-dlp \
    --no-check-certificate \
    --add-header "User-Agent:Mozilla/5.0" \
    --add-header "Accept-Language:en-US,en;q=0.9" \
    -o "${filepath}" \
    --merge-output-format mp4 \
    "${url}"`;

  exec(cmd, { timeout: 60000 }, (error, stdout, stderr) => {
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
