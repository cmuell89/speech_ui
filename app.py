from flask import Flask, render_template
from webhooks.webhook import initialize, connect_to_database, webhook


b = connect_to_database()
initialize(db)

app = Flask(__name__)
app.register_blueprint(webhook)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')


@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')


# run the app
if __name__ == '__main__':
    db = connect_to_database()
    initialize(db)
    app.run()
