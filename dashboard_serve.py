from flask import Flask, jsonify, render_template
import redis
import statistics

app = Flask(__name__)
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.route('/api/stats')
def stats():
    total_messages = int(redis_client.get("chatbot:total_messages") or 0)
    active_users = redis_client.scard("chatbot:active_users")
    response_times = redis_client.lrange("chatbot:response_times", 0, -1)
    response_times = list(map(float, response_times)) if response_times else []
    avg_response_time = round(statistics.mean(response_times), 2) if response_times else 0

    return jsonify({
        "total_messages": total_messages,
        "active_users": active_users,
        "avg_response_time": avg_response_time
    })

@app.route('/')
def index():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(port=5000, debug=True)
