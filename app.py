from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Rock, Paper, Scissors!"

if __name__ == "__main__":
    app.run(debug=True, port=5003)