from flask import Flask, request, jsonify, send_from_directory
import instaloader
import os
import subprocess
import re

app = Flask(__name__)
L = instaloader.Instaloader(download_video_thumbnails=False, save_metadata=False)

BRAND_NAME = "@TRENDYGAMMA"

def clean_text(text):
    # Remove emojis and special characters that break FFmpeg
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Remove special FFmpeg characters
    text = text.replace("'", "").replace('"', '').replace(':', '').replace('\\', '')
    return text.strip()[:50]

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url', '')
    shortcode = url.split('/reel/')[1].split('/')[0]
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    video_url = post.video_url
    caption = post.caption or ''
    title = caption.split('\n')[0][:60] if caption else 'Watch This!'
    return jsonify({
        "success": True,
        "video_url": video_url,
        "caption": caption,
        "title": title
    })

@app.route('/add-title', methods=['POST'])
def add_title():
    data = request.json
    video_url = data.get('video_url', '')
    raw_title = data.get('title', 'Watch This!')

    # Clean text for FFmpeg
    title = clean_text(raw_title) or 'Watch This'
    brand = clean_text(BRAND_NAME) or 'TRENDYGAMMA'

    input_path = '/tmp/input.mp4'
    output_path = f'/tmp/output_{os.urandom(4).hex()}.mp4'

    try:
        # Download video
        subprocess.run(
            ['wget', '-q', '--no-check-certificate', '-O', input_path, video_url],
            check=True, timeout=60
        )

        # Add title top + brand bottom
        drawtext = (
            f"drawtext=text='{title}':fontsize=40:fontcolor=white"
            f":x=(w-text_w)/2:y=40:box=1:boxcolor=black@0.6:boxborderw=8,"
            f"drawtext=text='{brand}':fontsize=36:fontcolor=white"
            f":x=(w-text_w)/2:y=h-60:box=1:boxcolor=black@0.6:boxborderw=8"
        )

        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-vf', drawtext,
            '-codec:a', 'copy',
            output_path
        ], check=True, timeout=120)

        file_url = f"{request.host_url}files/{os.path.basename(output_path)}"
        return jsonify({"success": True, "video_url": file_url})

    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files/<filename>')
def serve_file(filename):
    return send_from_directory('/tmp', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
