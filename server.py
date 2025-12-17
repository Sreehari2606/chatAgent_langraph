from flask import Flask, request, jsonify, send_from_directory
from agent.graph import code_agent
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configure the base directory for file browsing (user's home or specific folder)
BASE_DIR = os.path.expanduser("~")  # Start from user's home directory

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/styles.css')
def styles():
    return send_from_directory('static', 'styles.css')

@app.route('/script.js')
def script():
    return send_from_directory('static', 'script.js')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    file_path = data.get('file_path', '')
    file_content = data.get('file_content', '')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Build initial state with file context if available
        initial_state = {"user_query": user_message}
        if file_path:
            initial_state["file_path"] = file_path
        if file_content:
            initial_state["file_content"] = file_content
        
        result = code_agent.invoke(initial_state)
        response = result.get("llm_result", "No response generated.")
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    """List files and directories in a given path"""
    path = request.args.get('path', BASE_DIR)
    
    # Security check - prevent directory traversal
    try:
        abs_path = os.path.abspath(path)
    except:
        return jsonify({'error': 'Invalid path'}), 400
    
    if not os.path.exists(abs_path):
        return jsonify({'error': 'Path does not exist'}), 404
    
    if not os.path.isdir(abs_path):
        return jsonify({'error': 'Path is not a directory'}), 400
    
    try:
        items = []
        for item in os.listdir(abs_path):
            item_path = os.path.join(abs_path, item)
            try:
                is_dir = os.path.isdir(item_path)
                size = os.path.getsize(item_path) if not is_dir else 0
                items.append({
                    'name': item,
                    'path': item_path,
                    'isDirectory': is_dir,
                    'size': size,
                    'extension': os.path.splitext(item)[1].lower() if not is_dir else ''
                })
            except (PermissionError, OSError):
                # Skip files we can't access
                continue
        
        # Sort: directories first, then files alphabetically
        items.sort(key=lambda x: (not x['isDirectory'], x['name'].lower()))
        
        return jsonify({
            'currentPath': abs_path,
            'parentPath': os.path.dirname(abs_path) if abs_path != os.path.dirname(abs_path) else None,
            'items': items
        })
    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/read', methods=['GET'])
def read_file():
    """Read contents of a file"""
    path = request.args.get('path', '')
    
    if not path:
        return jsonify({'error': 'No path provided'}), 400
    
    try:
        abs_path = os.path.abspath(path)
    except:
        return jsonify({'error': 'Invalid path'}), 400
    
    if not os.path.exists(abs_path):
        return jsonify({'error': 'File does not exist'}), 404
    
    if os.path.isdir(abs_path):
        return jsonify({'error': 'Path is a directory'}), 400
    
    # Check file size (limit to 1MB for safety)
    if os.path.getsize(abs_path) > 1024 * 1024:
        return jsonify({'error': 'File too large (max 1MB)'}), 400
    
    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return jsonify({
            'path': abs_path,
            'content': content,
            'filename': os.path.basename(abs_path)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/write', methods=['POST'])
def write_file():
    """Write contents to a file"""
    data = request.json
    path = data.get('path', '')
    content = data.get('content', '')
    
    if not path:
        return jsonify({'error': 'No path provided'}), 400
    
    try:
        abs_path = os.path.abspath(path)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'success': True, 'path': abs_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/drives', methods=['GET'])
def list_drives():
    """List available drives (Windows) or root (Unix)"""
    import platform
    
    if platform.system() == 'Windows':
        import string
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append({'name': f"{letter}:", 'path': drive})
        return jsonify({'drives': drives})
    else:
        return jsonify({'drives': [{'name': '/', 'path': '/'}]})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

