### 1. Clone the Repository

```bash
git clone https://github.com/tejasree-1898/smart-resume-screener.git
cd smart-resume-screener

### 2. Backend Setup
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your OpenAI API key
echo OPENAI_API_KEY=your_openai_api_key_here > .env

# Run the backend
python -m app.main

### 3. Frontend Setup
cd frontend

# Install dependencies
npm install

# Start the frontend
npm start
