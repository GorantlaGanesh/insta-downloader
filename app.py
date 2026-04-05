from flask import Flask, request, jsonify, send_from_directory
import instaloader
import os
import time

app = Flask(__name__)
L = instaloader.Instaloader(download_video_thumbnails=False, save_metadata=False)

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
    
    return jsonify({"success": True, "video_url": video_url})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3000)))
