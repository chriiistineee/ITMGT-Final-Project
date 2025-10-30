# app.py - Flask Backend Server
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import base64
import os
from datetime import datetime
import hashlib

app = Flask(__name__)
CORS(app)

# Database initialization
def init_db():
    conn = sqlite3.connect('ghost_projects.db')
    c = conn.cursor()
    
    # Create submissions table with tamper-proof hash
    c.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            location TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            description TEXT NOT NULL,
            photo_data TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            ip_address TEXT,
            data_hash TEXT NOT NULL,
            UNIQUE(data_hash)
        )
    ''')
    
    # Create verification table
    c.execute('''
        CREATE TABLE IF NOT EXISTS verifications (
            location_key TEXT PRIMARY KEY,
            report_count INTEGER,
            verified INTEGER DEFAULT 0,
            last_updated TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Generate tamper-proof hash
def generate_hash(data):
    hash_string = f"{data['project_name']}{data['location']}{data['timestamp']}"
    return hashlib.sha256(hash_string.encode()).hexdigest()

# Get database connection
def get_db():
    conn = sqlite3.connect('ghost_projects.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

# Submit new report
@app.route('/api/submit', methods=['POST'])
def submit_report():
    try:
        data = request.json
        
        # Validate required fields
        required = ['projectName', 'location', 'description', 'photo']
        if not all(field in data for field in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Create tamper-proof timestamp and hash
        timestamp = datetime.now().isoformat()
        submission_data = {
            'project_name': data['projectName'],
            'location': data['location'],
            'timestamp': timestamp
        }
        data_hash = generate_hash(submission_data)
        
        # Get IP address
        ip_address = request.remote_addr
        
        conn = get_db()
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO submissions 
                (project_name, location, latitude, longitude, description, 
                 photo_data, timestamp, ip_address, data_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['projectName'],
                data['location'],
                data.get('latitude'),
                data.get('longitude'),
                data['description'],
                data['photo'],
                timestamp,
                ip_address,
                data_hash
            ))
            
            submission_id = c.lastrowid
            
            # Update verification count if location provided
            if data.get('latitude') and data.get('longitude'):
                location_key = f"{data['latitude']},{data['longitude']}"
                
                c.execute('''
                    INSERT INTO verifications (location_key, report_count, last_updated)
                    VALUES (?, 1, ?)
                    ON CONFLICT(location_key) 
                    DO UPDATE SET 
                        report_count = report_count + 1,
                        last_updated = ?,
                        verified = CASE WHEN report_count + 1 >= 4 THEN 1 ELSE 0 END
                ''', (location_key, timestamp, timestamp))
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'id': submission_id,
                'hash': data_hash,
                'message': 'Report submitted successfully'
            })
            
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Duplicate submission detected'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Get all reports
@app.route('/api/reports', methods=['GET'])
def get_reports():
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('''
            SELECT 
                s.*,
                COALESCE(v.report_count, 1) as report_count,
                COALESCE(v.verified, 0) as verified
            FROM submissions s
            LEFT JOIN verifications v 
                ON v.location_key = (s.latitude || ',' || s.longitude)
            ORDER BY s.timestamp DESC
        ''')
        
        reports = []
        for row in c.fetchall():
            reports.append({
                'id': row['id'],
                'projectName': row['project_name'],
                'location': row['location'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'description': row['description'],
                'photo': row['photo_data'],
                'timestamp': row['timestamp'],
                'hash': row['data_hash'],
                'reportCount': row['report_count'],
                'verified': bool(row['verified'])
            })
        
        return jsonify(reports)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Get statistics
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) as total FROM submissions')
        total = c.fetchone()['total']
        
        c.execute('SELECT COUNT(*) as verified FROM verifications WHERE verified = 1')
        verified = c.fetchone()['verified']
        
        c.execute('SELECT COUNT(*) as pending FROM verifications WHERE verified = 0')
        pending = c.fetchone()['pending']
        
        c.execute('SELECT COUNT(DISTINCT latitude || longitude) as unique_locs FROM submissions WHERE latitude IS NOT NULL')
        unique_locations = c.fetchone()['unique_locs']
        
        return jsonify({
            'total': total,
            'verified': verified,
            'pending': pending,
            'uniqueLocations': unique_locations
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Verify hash (tamper-proof check)
@app.route('/api/verify/<hash_id>', methods=['GET'])
def verify_hash(hash_id):
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT * FROM submissions WHERE data_hash = ?', (hash_id,))
        row = c.fetchone()
        
        if row:
            # Regenerate hash to verify integrity
            verification_data = {
                'project_name': row['project_name'],
                'location': row['location'],
                'timestamp': row['timestamp']
            }
            computed_hash = generate_hash(verification_data)
            
            return jsonify({
                'valid': computed_hash == hash_id,
                'record': dict(row),
                'message': 'Record is tamper-proof and valid' if computed_hash == hash_id else 'WARNING: Record may be tampered'
            })
        else:
            return jsonify({'error': 'Hash not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8000)