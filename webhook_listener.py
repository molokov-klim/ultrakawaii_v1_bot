from flask import Flask, request, jsonify
import subprocess
import logging

# Настройка логирования
logging.basicConfig(filename='/home/hash/logs/webhook_listener.log', level=logging.INFO)

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    if data.get('action') == 'published':
        try:
            subprocess.run(["git", "pull"], check=True)
            subprocess.run(["systemctl", "restart", "bot.service"], check=True)
            logging.info("Bot successfully updated and restarted.")
            return jsonify({'status': 'ok'})
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to update and restart bot: {e}")
            return jsonify({'status': 'failed'}), 500

    return jsonify({'status': 'ignored'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
