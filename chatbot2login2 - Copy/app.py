from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from uuid import uuid4
import openai
from dotenv import load_dotenv
import os
import logging 

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./test.db' # Use an actual path
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
CORS(app)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", 'secret-key')
app.config['SESSION_TYPE'] = 'filesystem'

Session(app)

load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")

# User database for storing login credentials
users_db = {}

def generate_text(prompt, chat_history):
    # Add new user message to chat history
    chat_history.append({"role": "user", "content": prompt})

    # Generate the assistant's response using OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=chat_history  # Pass the complete chat history
    )

    # Extract assistant's message
    assistant_message = response['choices'][0]['message']['content']

    # Log the prompt and chat history but not API key
    logging.info(f"Prompt: {prompt}, Chat history: {chat_history}")

    # Add assistant's message to chat history
    chat_history.append({"role": "assistant", "content": assistant_message})

    return assistant_message

@app.route('/')
def home():
    if 'username' not in session:
        return redirect('/index')
    session['user_id'] = session.get('user_id', str(uuid4()))
    session['chat_history'] = []
    return redirect('/index.html')

@app.route('/index')

def index():
    if 'username' not in session:
        return redirect('/login')
    return render_template('index.html')

@app.route('/register', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Username or password cannot be empty")
            return render_template('register.html')

        user = User.query.filter_by(username=username).first()

        if user is not None:
            flash("Username already exists")
            return render_template('register.html')

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Username or password cannot be empty")
            return render_template('login.html')

        # Check if the user is registered
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash("Invalid username or password")
            return render_template('login.html')

        # Login the user
        session['username'] = username

        # Redirect the user to the index page
        return redirect(url_for('index'))

    # Handle GET request to display login form
    return render_template('login.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect('/login')

    username = session['username']

    # Get the user's chat history
    user_data = users_db[username]
    chat_history = user_data['chat_history']

    if request.method == 'POST':
        data = request.get_json()
        message = data.get('message')
        if message:
            chat_history.append(message)
            
    return render_template('chat.html', username=username, messages=chat_history)

@app.route('/generate_post', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        user_input = data.get('text')

        chat_history = session.get('chat_history', [])
        
        if not chat_history:
            # Initial system message
            chat_history.append({"role": "system", "content": "Hi, I am Social Scribe, a helpful marketing assistant. What's your name?"})
        else:
            # User message
            chat_history.append({"role": "user", "content": user_input})

            if len(chat_history) == 2:  # User name received
                user_name = user_input
                session['user_name'] = user_name
                chat_history.append({"role": "system", "content": f"Great to meet you, {user_name}! What is your business?"})
            elif len(chat_history) == 4:  # Business information received
                chat_history.append({"role": "system", "content": "What is the purpose of your LinkedIn post?"})
            elif len(chat_history) == 6:  # Purpose of post received
                chat_history.append({"role": "system", "content": "What tone or style do you prefer for your post?"})
            elif len(chat_history) == 8:  # Preferred tone received
                chat_history.append({"role": "system", "content": "What should be the approximate length of your post?"})
            elif len(chat_history) == 10:  # Post length received
                chat_history.append({"role": "system", "content": "What should be the call to action in your post?"})
            elif len(chat_history) == 12:  # Call to action received
                chat_history.append({"role": "system", "content": "What keywords do you want to include in your post?"})
            elif len(chat_history) < 14:  # Collecting initial information
                chat_history.append({"role": "user", "content": user_input})
            elif len(chat_history) == 14:  # All information collected, generate post
                chat_history.append({"role": "user", "content": user_input})

                # Extract information from the chat history
                user_business = chat_history[3]['content']  # The user's business
                post_purpose = chat_history[5]['content']  # The purpose of the post
                preferred_tone = chat_history[7]['content']  # The preferred tone/style
                post_length = chat_history[9]['content']  # The preferred post length
                call_to_action = chat_history[11]['content']  # The call to action
                keywords = chat_history[13]['content']  # The keywords to include

                # Prepare the prompt for the OpenAI API
                prompt = f"I need to write a {post_purpose} post for {user_business}. The post should be {post_length}, use a {preferred_tone} tone, include the call to action '{call_to_action}', and use the following keywords: {keywords}."

                # Generate the post using the OpenAI API
                post = generate_text(prompt, chat_history)

                # Add the generated post to the chat history
                post_message = "Here is your generated post:\n\n" + post
                chat_history.append({"role": "system", "content": post_message})

            else:  # Post generated, continue conversation
                # Add the user's message to the chat history
                chat_history.append({"role": "user", "content": user_input})

                # Limit chat history to the last few messages
                limited_chat_history = chat_history[-7:]

                # Generate the assistant's response using the OpenAI API
                assistant_message = generate_text(user_input, limited_chat_history)

                # Add the assistant's message to the chat history
                chat_history.append({"role": "assistant", "content": assistant_message})

        session['chat_history'] = chat_history

        print("Chat history:", chat_history)
        print("User name:", session.get('user_name'))

        return jsonify(chat_history[-1]['content'])
    
    except Exception as e:
        logging.exception("Exception in /generate_post: ")
        return jsonify(str(e)), 500
    
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('chat_history', None)
    return redirect('/')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
