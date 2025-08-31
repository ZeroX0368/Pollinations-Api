
from flask import Flask, request, jsonify, send_file
import requests
import io
from PIL import Image
import os
from urllib.parse import quote
import uuid
import time
import random

app = Flask(__name__)

# Store generated images in memory (in production, use a database or file storage)
image_cache = {}

@app.route('/api/image')
def generate_image():
    # Start timing the request
    start_time = time.time()
    
    # Get the prompt from query parameters
    prompt = request.args.get('prompt')
    
    if not prompt:
        return jsonify({'error': 'Prompt parameter is required'}), 400
    
    try:
        # URL encode the prompt and call the Pollinations AI API with enhanced parameters
        encoded_prompt = quote(prompt)
        width = random.randint(1024, 2000)
        height = random.randint(1024, 2000)
        seed = random.randint(100000, 999999)
        
        api_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=midjourney&nologo=true&private=false&enhance=true&seed={seed}"
        
        # Add headers and timeout for better reliability
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Check if response contains image data
            if 'image' in response.headers.get('content-type', '').lower():
                # Generate random image ID
                image_id = str(uuid.uuid4()).replace('-', '')[:16]
                
                # Store the image data in cache
                image_cache[image_id] = response.content
                
                # Create image URL similar to Discord CDN format
                base_url = request.url_root.rstrip('/')
                image_url = f"{base_url}/cdn/images/{image_id}.png"
                
                # Calculate request duration
                end_time = time.time()
                duration = round((end_time - start_time), 2)
                
                return jsonify({
                    'status': 'success',
                    'Server': 'https://discord.gg/Zg2XkS5hq9',
                    'message': 'Image generated successfully',
                    'image': image_url,
                    'image_id': image_id,
                    'duration': f"{duration}s",
                    'parameters': {
                        'width': width,
                        'height': height,
                        'seed': seed,
                        'model': 'midjourney'
                    }
                })
            else:
                end_time = time.time()
                duration = round((end_time - start_time), 2)
                return jsonify({
                    'error': 'Response is not an image',
                    'content_type': response.headers.get('content-type', 'unknown'),
                    'duration': f"{duration}s"
                }), 500
        else:
            end_time = time.time()
            duration = round((end_time - start_time), 2)
            return jsonify({
                'error': f'API returned status {response.status_code}',
                'response': response.text[:200],
                'duration': f"{duration}s"
            }), 500
            
    except Exception as e:
        end_time = time.time()
        duration = round((end_time - start_time), 2)
        return jsonify({
            'error': str(e),
            'duration': f"{duration}s"
        }), 500

@app.route('/cdn/images/<image_id>.png')
def serve_image(image_id):
    """Serve the actual generated image"""
    if image_id in image_cache:
        # Return the cached image data
        return send_file(
            io.BytesIO(image_cache[image_id]),
            mimetype='image/png',
            as_attachment=False,
            download_name=f'{image_id}.png'
        )
    else:
        return jsonify({
            'error': 'Image not found',
            'image_id': image_id
        }), 404

@app.route('/api/ai/openai')
def openai_text():
    # Start timing the request
    start_time = time.time()
    
    # Get the prompt from query parameters
    prompt = request.args.get('prompt')
    
    if not prompt:
        end_time = time.time()
        duration = round((end_time - start_time), 2)
        return jsonify({
            'error': 'Prompt parameter is required',
            'duration': f"{duration}s"
        }), 400
    
    try:
        # Call the Pollinations AI text API
        api_url = "https://text.pollinations.ai/"
        
        # Send POST request with prompt
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        # Calculate request duration
        end_time = time.time()
        duration = round((end_time - start_time), 2)
        
        if response.status_code == 200:
            # Get the response text and clean up formatting
            response_text = response.text.strip()
            
            # Remove escape characters and format properly
            response_text = response_text.replace('\\n', '\n')
            response_text = response_text.replace('\\u2014', '—')
            response_text = response_text.replace('\\"', '"')
            
            return jsonify({
                'status': 'success',
                'Server': 'https://discord.gg/Zg2XkS5hq9',
                'message': 'Text generated successfully',
                'response': response_text,
                'duration': f"{duration}s",
                'model': 'OpenAi'
            })
        else:
            return jsonify({
                'error': f'API returned status {response.status_code}',
                'response': response.text[:200],
                'duration': f"{duration}s"
            }), 500
            
    except Exception as e:
        end_time = time.time()
        duration = round((end_time - start_time), 2)
        return jsonify({
            'error': str(e),
            'duration': f"{duration}s"
        }), 500

@app.route('/')
def index():
    return '''
    <h1>AI Generation API</h1>
    <h2>Image Generation</h2>
    <p>Use: <code>/api/image?prompt=your_prompt_here</code></p>
    <p>Example: <a href="/api/image?prompt=cute cat">/api/image?prompt=cute cat</a></p>
    
    <h2>Text Generation (OpenAI-style)</h2>
    <p>Use: <code>/api/ai/openai?prompt=your_prompt_here</code></p>
    <p>Example: <a href="/api/ai/openai?prompt=Write a short poem about coding">/api/ai/openai?prompt=Write a short poem about coding</a></p>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
