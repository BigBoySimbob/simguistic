from flask import Flask
from routes.learning import learning_bp
from routes.review import review_bp

app = Flask(__name__)

# Register blueprints for different routes
app.register_blueprint(learning_bp, url_prefix='/simguistic')
app.register_blueprint(review_bp, url_prefix='/simguistic')

if __name__ == '__main__':
    app.run(debug=True)