# Shop Billing Software

A complete shop billing and invoice management system built with Flask.

## Features

- Customer management
- Product inventory
- Invoice creation with GST
- PDF invoice generation
- WhatsApp sharing
- Transport charges
- Multiple copy printing (Original/Duplicate/Triplicate)

## Local Deployment

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd shop-billing-software
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**
   ```bash
   python init_db.py
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Access the application**
   Open your browser and go to `http://localhost:5000`

## Render.com Deployment

### Step 1: Push to GitHub

1. **Initialize git repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Create a new repository on GitHub** (github.com/new)

3. **Connect local repository to GitHub**
   ```bash
   git remote add origin https://github.com/your-username/shop-billing-software.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render

1. **Sign up/Login to Render.com** (render.com)

2. **Create a new Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select "shop-billing-software" repository

3. **Configure Build Settings**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`
   - **Runtime**: Python 3.11

4. **Configure Environment Variables** (if needed)
   - Add any required environment variables

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete (2-3 minutes)

6. **Access your application**
   - Render will provide a URL like `https://your-app.onrender.com`

### Important Notes for Render

- **Database**: SQLite works on Render but data may be lost on redeployment
- **For production**: Consider using PostgreSQL (Render provides free PostgreSQL)
- **Free tier**: Render provides free tier with limited resources
- **Sleep mode**: Free tier apps sleep after 15 minutes of inactivity

## Production Considerations

### Database Migration (Optional)

For production use, consider migrating to PostgreSQL:

1. **Add PostgreSQL to requirements.txt**
   ```
   psycopg2-binary==2.9.7
   ```

2. **Update config.py to use PostgreSQL**
   ```python
   import os
   DATABASE_URL = os.environ.get('DATABASE_URL')
   if DATABASE_URL:
       app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
   ```

3. **Add PostgreSQL in Render**
   - Create PostgreSQL instance in Render
   - Add DATABASE_URL to environment variables

### Security

- Add environment variables for sensitive data
- Use HTTPS (Render provides SSL automatically)
- Implement user authentication if needed

## Support

For issues or questions, please contact the development team.

## License

This software is proprietary and confidential.
