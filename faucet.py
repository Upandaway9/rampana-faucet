from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Rampana Faucet is Live!'

if __name__ == '__main__':
    app.run()
