from flask import Flask, render_template

app = Flask(__name__)
app.config["SECRET_KEY"] = "UcFSu9zW5ksmujM4"


@app.route('/', methods=['GET'])
def index():
    return render_template('main.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
