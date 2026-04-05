from flask import Flask, request, jsonify, send_from_directory
import instaloader
import os
import subprocess

app = Flask(__name__)
L = instaloader.Instaloader(download_video_thumbnails=False, save_metadata=False)

BRAND_NAME = "@TRENDYGAMMA"  # ← CHANGE THIS to your brand/channel name

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
    # Use first line of caption as title
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
    title = data.get('title', 'Watch This!')
    brand = BRAND_NAME

    input_path = '/tmp/input.mp4'
    output_path = f'/tmp/output_{os.urandom(4).hex()}.mp4'

    # Download video
    subprocess.run(['wget', '-O', input_path, video_url], check=True)

    # Add caption title at TOP + brand watermark at BOTTOM
    drawtext = (
        f"drawtext=text='{title}':"
        f"fontsize=40:fontcolor=white:x=(w-text_w)/2:y=40:"
        f"box=1:boxcolor=black@0.6:boxborderw=8,"
        f"drawtext=text='{brand}':"
        f"fontsize=36:fontcolor=white:x=(w-text_w)/2:y=h-60:"
        f"box=1:boxcolor=black@0.6:boxborderw=8"
    )

    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', drawtext,
        '-codec:a', 'copy',
        output_path
    ]
    subprocess.run(cmd, check=True)

    file_url = f"{request.host_url}files/{os.path.basename(output_path)}"
    return jsonify({"success": True, "video_url": file_url})

@app.route('/files/<filename>')
def serve_file(filename):
    return send_from_directory('/tmp', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
