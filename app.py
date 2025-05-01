from flask import Flask, request, jsonify
import redis
import time

app = Flask(__name__)

# Initialize Redis
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# Whitelisted IPs
WHITELISTED_IPS = {"127.0.0.1", "192.168.1.1"}  # Add your whitelisted IPs here

def is_rate_limited(ip):
    current_time = int(time.time())
    key = f"rate_limit:{ip}"
    
    # Increment the request count for this IP
    request_count = redis_client.get(key)
    
    if request_count is None:
        # First request, set the count and expiration
        redis_client.set(key, 1, ex=60)  # 1 request per minute
        return False
    elif int(request_count) < 10:
        # Allow the request and increment the count
        redis_client.incr(key)
        return False
    else:
        # Rate limit exceeded
        return True

@app.before_request
def limit_remote_addr():
    if request.remote_addr not in WHITELISTED_IPS:
        return jsonify({"error": "Your IP is not whitelisted."}), 403
    if is_rate_limited(request.remote_addr):
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify({"data": "Here is your data!"})

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the API!"})

if __name__ == '__main__':
    app.run(debug=True)