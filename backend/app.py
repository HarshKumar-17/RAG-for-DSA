from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from final import ask_question, chat_history
import os

app = Flask(__name__)
CORS(app)

FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), "../frontend")

# -----------------------------
# Serve frontend
# -----------------------------

@app.route("/")
def home():
    return send_from_directory(FRONTEND_FOLDER, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_FOLDER, filename)


# -----------------------------
# Chat endpoint
# -----------------------------

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    message = data.get("message")

    if not message:
        return jsonify({"response": "Please enter a question."}), 400

    try:
        answer = ask_question(message)
        return jsonify({"response": answer})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500


# -----------------------------
# Get chat history
# -----------------------------

@app.route("/history", methods=["GET"])
def get_history():

    history = []

    for msg in chat_history:
        if msg.__class__.__name__ == "HumanMessage":
            history.append({"role": "user", "content": msg.content})
        else:
            history.append({"role": "bot", "content": msg.content})

    return jsonify({"history": history})


# -----------------------------
# Reset chat
# -----------------------------

@app.route("/reset", methods=["POST"])
def reset_chat():

    chat_history.clear()

    return jsonify({"status": "cleared"})


# -----------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)