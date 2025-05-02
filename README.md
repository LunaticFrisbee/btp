# Rate Limited API Application

This application demonstrates IP-based and global rate limiting using Redis and Flask. The app provides a simple UI that displays data fetched from an API endpoint and tracks the number of incoming requests.

## Features

- **IP-based Rate Limiting**: Maximum 5 requests per IP in a 60-second window
- **Global Rate Limiting**: Maximum 15 requests total across all users in a 60-second window
- **Request Counter**: Tracks the total number of API requests since server start
- **Real-time Stats**: Visual representation of rate limit consumption for each user
- **Mock Users**: 4 mock users with different IP addresses

## Technical Implementation

- **Flask**: Web framework for the API and UI
- **Redis**: In-memory data store used for rate limiting
- **Time Bucket Algorithm**: Implemented using Redis sorted sets for accurate time-based limiting
- **Atomic Operations**: All Redis operations are executed atomically using pipelines

## Project Structure

```
.
├── app.py              # Main Flask application
├── templates/
│   └── index.html      # UI template
├── requirements.txt    # Python dependencies
```

## Rate Limiting Implementation

The application uses Redis sorted sets to implement a sliding window rate limiter:

1. Each request's timestamp is added to Redis sorted sets (one for IP-specific, one for global)
2. Old timestamps outside the current window are removed
3. The count of remaining timestamps is compared against the configured limits
4. If either limit is exceeded, the request is rejected with a 429 status code

All Redis operations are performed atomically using Redis pipelines to ensure data consistency.

## How to Run

### Manual Setup

1. Install Redis on your system
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```

## Using the Application

1. Open your browser and navigate to `http://localhost:5000`
2. The UI will display panels for each mock user
3. Click the "Fetch Data" button to simulate API requests from different users
4. Observe how rate limiting is applied based on individual IP addresses and global limits
5. The request counter at the top tracks the total number of API requests
6. Progress bars show how close each user is to hitting their rate limit

## Configuration

You can modify the following parameters in `app.py`:

- `IP_RATE_LIMIT`: Maximum requests per IP in the time window (default: 5)
- `GLOBAL_RATE_LIMIT`: Maximum total requests in the time window (default: 15)
- `WINDOW_SIZE`: Time window in seconds (default: 60)
