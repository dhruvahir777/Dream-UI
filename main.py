from flask import Flask, render_template, request
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

app = Flask(__name__)

# Function to sanitize filenames
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

# Function to download the website
def download_webpage(url, folder_name):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Download linked resources (images, JS, CSS, Videos, GIFs)
        update_links(soup, url, folder_name, headers)

        # Create directory to save the website
        os.makedirs(folder_name, exist_ok=True)

        # Save the HTML file
        with open(os.path.join(folder_name, "index.html"), "w", encoding="utf-8") as file:
            file.write(str(soup))
        print(f"Website saved as folder: {folder_name}")
    except Exception as e:
        print(f"Error: {e}")

# Function to update resources in the HTML
def update_links(soup, base_url, folder_name, headers):
    for tag in soup.find_all(["link", "script", "img", "video"]):
        attr = "href" if tag.name == "link" else "src"
        if tag.has_attr(attr):
            file_url = urljoin(base_url, tag[attr])
            local_path = download_and_save(file_url, folder_name, headers)
            if local_path:
                tag[attr] = local_path

    # Handle <video> tag sources separately
    for tag in soup.find_all("video"):
        for source_tag in tag.find_all("source"):
            if source_tag.has_attr("src"):
                file_url = urljoin(base_url, source_tag["src"])
                local_path = download_and_save(file_url, folder_name, headers)
                if local_path:
                    source_tag["src"] = local_path

# Function to download and save files (CSS, JS, Images, Videos, GIFs)
def download_and_save(file_url, folder_name, headers):
    try:
        # Get file extension
        file_extension = file_url.split('.')[-1].lower()

        # Handle common file formats
        allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'avi', 'css', 'js']
        if file_extension not in allowed_extensions:
            return None

        parsed_url = urlparse(file_url)
        file_path = sanitize_filename(parsed_url.path.lstrip("/"))
        save_path = os.path.join(folder_name, file_path)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        response = requests.get(file_url, headers=headers, stream=True)
        response.raise_for_status()
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)

        return os.path.relpath(save_path, folder_name)
    except Exception as e:
        print(f"Failed to download {file_url}: {e}")
        return None

# Route for home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle the form submission and trigger website download
@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    download_type = request.form['downloadType']
    folder_name = generate_folder_name(url)  # Generate folder name

    # Start the website download
    download_webpage(url, folder_name)
    
    # After downloading, render result.html with folder_name and download_type
    return render_template('result.html', folder_name=folder_name, download_type=download_type)

# Helper function to generate folder name from URL
def generate_folder_name(url):
    site_name = urlparse(url).hostname
    site_name = site_name.replace('www.', '')  # Remove 'www.' if exists
    folder_name = f"DreemUI_{site_name}"
    return folder_name

if __name__ == "__main__":
    app.run(debug=True)
