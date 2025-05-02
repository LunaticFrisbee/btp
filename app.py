from flask import Flask, jsonify, render_template, request
import redis
import time
import json
import os
from datetime import datetime

app = Flask(__name__)

# Configure Redis - in production, you'd use environment variables
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

# Configuration
IP_RATE_LIMIT = 5  # Maximum requests per IP in the time window
GLOBAL_RATE_LIMIT = 15  # Maximum total requests in the time window
WINDOW_SIZE = 60  # Time window in seconds (1 minute)

# Mock user data
USERS = {
    "192.168.1.100": "User1",
    "192.168.1.101": "User2",
    "192.168.1.102": "User3",
    "192.168.1.103": "User4"
}

# Mock data to return
MOCK_DATA = [
    {"id": 1, "name": "Product A", "price": 19.99},
    {"id": 2, "name": "Product B", "price": 29.99},
    {"id": 3, "name": "Product C", "price": 39.99},
    {"id": 4, "name": "Product D", "price": 49.99},
    {"id": 5, "name": "Product E", "price": 59.99}
]

def check_rate_limit(ip_address):
    """
    Check both IP-based and global rate limits
    Returns: (can_proceed, ip_limit_count, global_limit_count)
    """
    current_time = int(time.time())
    window_start = current_time - WINDOW_SIZE
    
    # Use a Redis pipeline for atomic operations
    pipe = redis_client.pipeline()
    
    # Clean up old records before checking
    ip_key = f"rate_limit:ip:{ip_address}"
    global_key = "rate_limit:global"
    
    # Add the current request timestamp to the sorted sets
    pipe.zadd(ip_key, {current_time: current_time})
    pipe.zadd(global_key, {f"{current_time}:{ip_address}": current_time})
    
    # Remove old requests outside the window
    pipe.zremrangebyscore(ip_key, 0, window_start)
    pipe.zremrangebyscore(global_key, 0, window_start)
    
    # Count the number of requests in the current window
    pipe.zcard(ip_key)
    pipe.zcard(global_key)
    
    # Set expiry on the keys so they're automatically cleaned up
    pipe.expire(ip_key, WINDOW_SIZE * 2)
    pipe.expire(global_key, WINDOW_SIZE * 2)
    
    # Execute all commands atomically
    results = pipe.execute()
    
    # Get the counts from the results
    ip_request_count = results[4]
    global_request_count = results[5]
    
    # Check if either limit is exceeded
    ip_limit_exceeded = ip_request_count > IP_RATE_LIMIT
    global_limit_exceeded = global_request_count > GLOBAL_RATE_LIMIT
    
    can_proceed = not (ip_limit_exceeded or global_limit_exceeded)
    
    return can_proceed, ip_request_count, global_request_count


@app.route('/')
def index():
    return render_template('index.html', users=USERS)


@app.route('/api/data')
def get_data():
    # Get client IP
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Check rate limits
    can_proceed, ip_count, global_count = check_rate_limit(ip_address)
    
    # Record this request
    redis_client.incr("request_counter")
    
    # Check if the client has exceeded rate limits
    if not can_proceed:
        if ip_count > IP_RATE_LIMIT:
            return jsonify({
                "error": "IP rate limit exceeded",
                "ip_count": ip_count,
                "global_count": global_count,
                "ip_limit": IP_RATE_LIMIT,
                "global_limit": GLOBAL_RATE_LIMIT,
                "window_size": WINDOW_SIZE
            }), 429
        else:
            return jsonify({
                "error": "Global rate limit exceeded",
                "ip_count": ip_count,
                "global_count": global_count,
                "ip_limit": IP_RATE_LIMIT,
                "global_limit": GLOBAL_RATE_LIMIT, 
                "window_size": WINDOW_SIZE
            }), 429
    
    # If rate limit is not exceeded, return the data
    return jsonify({
        "data": MOCK_DATA,
        "timestamp": datetime.now().isoformat(),
        "ip_address": ip_address,
        "user": USERS.get(ip_address, "Unknown User"),
        "rate_limit_info": {
            "ip_count": ip_count,
            "global_count": global_count,
            "ip_limit": IP_RATE_LIMIT,
            "global_limit": GLOBAL_RATE_LIMIT,
            "window_size": WINDOW_SIZE
        }
    })


@app.route('/api/stats')
def get_stats():
    # Get the request counter
    request_count = redis_client.get("request_counter")
    if not request_count:
        request_count = 0
    
    # Get all active IP counts in the current window
    current_time = int(time.time())
    window_start = current_time - WINDOW_SIZE
    
    ip_stats = {}
    for ip in USERS.keys():
        ip_key = f"rate_limit:ip:{ip}"
        count = redis_client.zcount(ip_key, window_start, current_time)
        ip_stats[ip] = {
            "count": count,
            "user": USERS.get(ip, "Unknown")
        }
    
    # Get the global count
    global_count = redis_client.zcard("rate_limit:global")
    
    return jsonify({
        "total_requests": int(request_count),
        "current_window": {
            "global_count": global_count,
            "ip_stats": ip_stats,
            "window_size": WINDOW_SIZE,
            "window_end": current_time,
            "window_start": window_start
        }
    })


if __name__ == '__main__':
    # Initialize the request counter if it doesn't exist
    if not redis_client.exists("request_counter"):
        redis_client.set("request_counter", 0)
    
    app.run(debug=True, host='0.0.0.0', port=5000)