from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def ask_something():
    text = request.form['request']

    #text goes to chatGPT
    #chatGPT gives answer

    answer = "Lorem ipsum odor amet, consectetuer adipiscing elit. Eu mus eros tempor nostra sapien habitasse. Duis porttitor inceptos orci tortor; fames eros. Interdum nostra potenti curae curae, neque ante fames sapien amet. Magnis laoreet urna dui aptent, dolor erat fermentum nam. Suscipit egestas maximus platea ullamcorper ante parturient commodo luctus aenean. Magna a cursus sociosqu est est quam. Mus sociosqu quisque sit viverra nascetur nulla tristique. Ultrices lacus gravida lobortis morbi tempor auctor consectetur velit. Litora mattis id ridiculus cubilia purus ultrices turpis mus."

    return render_template('index.html', answer=answer)

if __name__ == '__main__':
    app.run(port=5000)