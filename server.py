import sqlite3
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()
    # Create messages table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT NOT NULL,
                  message TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

class RequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
        
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/messages':
            try:
                conn = sqlite3.connect('database.sqlite')
                c = conn.cursor()
                c.execute('SELECT * FROM messages ORDER BY timestamp DESC')
                rows = c.fetchall()
                conn.close()
                messages = []
                for row in rows:
                    messages.append({'id': row[0], 'name': row[1], 'email': row[2], 'message': row[3], 'timestamp': row[4]})
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'data': messages}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        # Redirect root to myself.html
        if self.path == '/':
            self.path = '/myself.html'
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/contact':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                name = data.get('name', '').strip()
                email = data.get('email', '').strip()
                message = data.get('message', '').strip()
                
                if not name or not email or not message:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'All fields are required.'}).encode('utf-8'))
                    return
                
                conn = sqlite3.connect('database.sqlite')
                c = conn.cursor()
                c.execute('INSERT INTO messages (name, email, message) VALUES (?, ?, ?)',
                          (name, email, message))
                conn.commit()
                last_id = c.lastrowid
                conn.close()
                
                self.send_response(201)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'id': last_id, 'message': 'Message sent successfully!'}).encode('utf-8'))
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Failed to save message: ' + str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=RequestHandler, port=3000):
    init_db()
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Server is running!')
    print(f'Please open your browser and visit: http://localhost:{port}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    print("Stopping server...")
    httpd.server_close()

if __name__ == '__main__':
    run()
