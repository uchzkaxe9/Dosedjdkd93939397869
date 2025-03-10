from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import re
import random
import string

app = Flask(__name__)

# Directory for storing downloaded videos
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Store short links mapping to real filenames
short_links = {}

def generate_short_code(length=6):
    """Generate a random short code for the URL"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def sanitize_filename(title, max_length=30):
    """Sanitize filename: Remove special characters & limit length"""
    title = re.sub(r'[\/:*?"<>|]', '', title)  # Remove illegal characters
    title = re.sub(r'\s+', ' ', title).strip()  # Normalize spaces
    title = re.sub(r'[^a-zA-Z0-9\s]', '', title)  # Keep only alphanumeric & spaces
    return title[:max_length].strip()  # Limit filename length

def is_facebook_url(url):
    """Check if the URL is a valid Facebook video URL"""
    return "facebook.com" in url or "fb.watch" in url

def download_facebook_video(url):
    """Download Facebook video and return the filename"""
    try:
        if not is_facebook_url(url):
            return "INVALID_URL"

        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)  # Extract metadata
            title = sanitize_filename(info['title'])
            ext = info.get('ext', 'mp4')  # Default to .mp4 if missing
            safe_filename = f"{title}.{ext}"

            ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_FOLDER, safe_filename)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl_fixed:
                ydl_fixed.download([url])

            return safe_filename

    except Exception as e:
        return "DOWNLOAD_ERROR"

@app.route('/download', methods=['GET'])
def download():
    """API Endpoint to download a Facebook video"""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    filename = download_facebook_video(url)

    if filename == "INVALID_URL":
        return jsonify({'error': 'This is not a Facebook URL'}), 400
    elif filename == "DOWNLOAD_ERROR":
        return jsonify({'error': 'Failed to download video. Check URL or try again later.'}), 500

    # Generate a short random code for the URL
    short_code = generate_short_code()
    short_links[short_code] = filename  # Store the mapping

    full_download_url = request.host_url + "d/" + short_code
    return jsonify({
        'status': 'success',
        'file': filename,
        'download_url': full_download_url,
        'credit': '@AzR_projects'
    })

@app.route('/d/<short_code>', methods=['GET'])
def serve_short_link(short_code):
    """Redirect short link to the actual file download"""
    if short_code in short_links:
        filename = short_links[short_code]
        return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)
    else:
        return jsonify({'error': 'Invalid or expired link'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
