from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess
import re
import requests as req

app = Flask(__name__)

BRAND_NAME = "@AURAEDITZ"

def clean_text(text):
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    text = text.replace("'", "").replace('"', '').replace(':', '').replace('\\', '')
    return text.strip()[:50]

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    url = data.get('url', '').strip()

    try:
        # Use Cobalt API - no Instagram login needed!
        cobalt = req.post(
            'https://api.cobalt.tools/',
            json={"url": url},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        result = cobalt.json()
        video_url = result.get('url')

        if not video_url:
            return jsonify({"error": "Could not get video URL"}), 500

        # Use filename as title
        raw_title = "Watch This"
        caption = ""

        title = clean_text(raw_title) or 'Watch This'
        brand = clean_text(BRAND_NAME) or 'AURAEDITZ'

        input_path = '/tmp/input.mp4'
        output_path = f'/tmp/output_{os.urandom(4).hex()}.mp4'

        # Download video
        response = req.get(video_url, timeout=60, stream=True)
        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Title fade in + Brand slide in
        drawtext = (
            f"drawtext=text='{title}'"
            f":fontsize=36"
            f":fontcolor=white"
            f":x=(w-text_w)/2"
            f":y=40"
            f":box=1:boxcolor=black@0.5:boxborderw=8"
            f":alpha='if(lt(t,1),t,1)'"
            f","
            f"drawtext=text='{brand}'"
            f":fontsize=32"
            f":fontcolor=yellow"
            f":x='if(lt(t,1),w-text_w*(t),w-text_w-20)'"
            f":y=h-55"
            f":box=1:boxcolor=black@0.6:boxborderw=8"
            f":alpha='if(lt(t,1),t,1)'"
        )

        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-vf', drawtext,
            '-codec:a', 'copy',
            output_path
        ], check=True, timeout=120)

        file_url = f"{request.host_url}files/{os.path.basename(output_path)}"
        return jsonify({
            "success": True,
            "video_url": file_url,
            "title": raw_title,
            "caption": caption
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files/<filename>')
def serve_file(filename):
    return send_from_directory('/tmp', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
