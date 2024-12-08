from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import google.generativeai as genai
from sqlalchemy import text
from transformers import pipeline



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:AyoutaAmana13@localhost/ecomerce_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')  # Add this line for session management
db = SQLAlchemy(app)

# Charger le pipeline d'analyse des sentiments
sentiment_analyzer = pipeline("sentiment-analysis")

# Set up Google Gemini
genai.configure(api_key='AIzaSyBHO21bwXzbnj_QIPw0Rf_WPA1DKcQFPgY')
model = genai.GenerativeModel('gemini-pro')

#Création de la BDD 
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)


#Analyser les sentiments de l'utilisateur
def analyze_sentiment(user_input):
    result = sentiment_analyzer(user_input)
    sentiment = result[0]['label']  # Positif, Négatif, Neutre
    score = result[0]['score']  # Confiance du modèle
    return sentiment, score


def fetch_store_data():
    """Fetch all store data from the database"""
    categories = Category.query.all()
    products = Product.query.all()
    
    store_data = "Store Information:\n\n"
    
    for category in categories:
        store_data += f"Category: {category.name}\n"
        for product in category.products:
            store_data += f"- {product.name}: ${product.price:.2f}, Size: {product.size}, Color: {product.color}, Quantity: {product.quantity}\n"
            store_data += f"  Description: {product.description}\n\n"
    
    return store_data

# def get_chatbot_response(user_input, conversation_history):
#     """Generate a response using the RAG system with Google Gemini, including conversation history"""
#     store_data = fetch_store_data()
    
#     prompt = f"""You are a helpful assistant for our clothing store. Use the following store information to answer the user's questions. 
#     If the information is not in the store data, politely say you don't have that information and offer to help with something else. 
#     Maintain context from the conversation history.

# Store Data:
# {store_data}

# Conversation History:
# {conversation_history}

# User: {user_input}"""
#     response = model.generate_content(prompt)
#     return response.text

def get_chatbot_response(user_input, conversation_history):
    # Analyse des sentiments
    sentiment, confidence = analyze_sentiment(user_input)

    # Récupérer les données du magasin
    store_data = fetch_store_data()

    # Adapter le prompt en fonction du sentiment
    if sentiment == "NEGATIVE":
        tone = "empathic"
        prefix = "matz3afch khoya la3ziz had denya makatib"
    elif sentiment == "POSITIVE":
        tone = "friendly"
        prefix = "That's great! I'm happy to help you further."
    else:
        tone = "neutral"
        prefix = "Thank you for your message. How can I assist you?"

    prompt = f"""
    You are a {tone} assistant for our clothing store. Use the following store information to answer the user's questions.

    Store Data:
    {store_data}

    Conversation History:
    {conversation_history}

    User: {user_input}
    """
    response = model.generate_content(prompt)

    # Ajouter un préfixe basé sur l'émotion
    print("sentiment est"+sentiment)
    return f"{prefix}\n{response.text}"



#LES INTERFACES POSSIBLES 
@app.route('/')
def home():
    categories = Category.query.all()
    products = Product.query.all()
    return render_template('index.html', categories=categories, products=products)

#Product interface
@app.route('/product/<int:product_id>')
def product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

#Catégorie interface
@app.route('/category/<int:category_id>')
def category(category_id):
    category = Category.query.get_or_404(category_id)
    return render_template('category.html', category=category)

#Ajouter produit interface
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        size = request.form['size']
        color = request.form['color']
        quantity = int(request.form['quantity'])
        category_id = int(request.form['category_id'])
        
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_product = Product(name=name, description=description, price=price,
                                size=size, color=color, quantity=quantity,
                                image=filename, category_id=category_id)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('home'))
    
    categories = Category.query.all()
    return render_template('add_product.html', categories=categories)

#interface de discussion CHAT
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    # Initialize or retrieve conversation history from session
    if 'conversation' not in session:
        session['conversation'] = []

    # Add user input to conversation history
    session['conversation'].append(f"User: {user_input}")

    # Generate response using conversation history
    conversation_history = "\n".join(session['conversation'][-5:])  # Use last 5 messages for context
    response = get_chatbot_response(user_input, conversation_history)

    # Add bot response to conversation history
    session['conversation'].append(f"Assistant: {response}")
    session.modified = True  # Ensure session is saved

    return jsonify({'response': response, 'conversation': session['conversation']})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)