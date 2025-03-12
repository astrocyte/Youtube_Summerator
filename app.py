from flask import Flask, render_template, request, jsonify, send_file
import json
import os
from datetime import datetime
from youtube_downloader import download_video, extract_video_id, is_url
from ytsummarator import get_transcript
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Store tasks and their status
tasks = {}

def process_youtube_url(task_id, url, options):
    """Process a YouTube URL with the selected options."""
    try:
        tasks[task_id]['status'] = 'processing'
        
        if options.get('download_video'):
            format = options.get('format', 'mp4')
            quality = options.get('quality', 'best')
            download_video(url, format, quality)
            
        if options.get('download_transcript') or options.get('generate_summary'):
            get_transcript(url)
            
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['completion_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    except Exception as e:
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/submit', methods=['POST'])
def submit_urls():
    data = request.json
    urls = data.get('urls', [])
    new_tasks = []
    
    for url_data in urls:
        url = url_data.get('url')
        if not url or not is_url(url):
            continue
            
        task_id = f"task_{len(tasks)}"
        task = {
            'id': task_id,
            'url': url,
            'options': url_data.get('options', {}),
            'status': 'queued',
            'submission_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'completion_time': None,
            'error': None
        }
        tasks[task_id] = task
        new_tasks.append(task)
        
        # Start processing in background
        thread = threading.Thread(
            target=process_youtube_url,
            args=(task_id, url, url_data.get('options', {}))
        )
        thread.daemon = True
        thread.start()
    
    return jsonify({'tasks': new_tasks})

@app.route('/api/tasks')
def get_tasks():
    return jsonify({'tasks': list(tasks.values())})

@app.route('/api/save', methods=['POST'])
def save_list():
    """Save the current list of URLs and their options to a JSON file."""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'youtube_list_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump({'tasks': list(tasks.values())}, f, indent=2)
            
        return jsonify({
            'success': True,
            'message': f'List saved as {filename}',
            'filename': filename
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error saving list: {str(e)}'
        }), 500

@app.route('/api/load', methods=['POST'])
def load_list():
    """Load a saved list of URLs and their options."""
    try:
        file = request.files['file']
        if file:
            data = json.load(file)
            loaded_tasks = data.get('tasks', [])
            
            # Clear existing tasks
            tasks.clear()
            
            # Add loaded tasks
            for task in loaded_tasks:
                task_id = f"task_{len(tasks)}"
                task['id'] = task_id
                task['status'] = 'queued'  # Reset status
                tasks[task_id] = task
            
            return jsonify({
                'success': True,
                'message': 'List loaded successfully',
                'tasks': list(tasks.values())
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading list: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 