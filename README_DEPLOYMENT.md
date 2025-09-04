# Smart License API - Render Deployment Guide

This guide will help you deploy your FastAPI application to Render.

## 🚀 Quick Deployment Steps

### 1. Prepare Your Repository

Make sure your FastApi folder contains these files:
- ✅ `main.py` - Your FastAPI application
- ✅ `db.py` - Database configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `render.yaml` - Render configuration
- ✅ `init_db.py` - Database initialization script

### 2. Deploy to Render

#### Option A: Using Render Dashboard (Recommended)

1. **Go to [Render Dashboard](https://dashboard.render.com/)**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Configure the service:**
   - **Name**: `smart-license-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or choose paid plan)

5. **Add Environment Variables:**
   - Go to "Environment" tab
   - Add: `DATABASE_URL` with your Supabase connection string:
     ```
     postgresql://postgres.gnkbepunywvseltrlopm:ZooVah%401997@aws-1-us-east-2.pooler.supabase.com:6543/postgres
     ```

6. **No Database Setup Needed:**
   - You're using Supabase, so no need to create a Render database
   - Your Supabase database will be used directly

#### Option B: Using render.yaml (Infrastructure as Code)

1. **Push your code to GitHub** with the `render.yaml` file
2. **Go to [Render Dashboard](https://dashboard.render.com/)**
3. **Click "New +" → "Blueprint"**
4. **Connect your GitHub repository**
5. **Render will automatically detect and deploy using render.yaml**

### 3. Initialize Database

After deployment, you need to initialize the database:

1. **Go to your web service dashboard**
2. **Click on "Shell" tab**
3. **Run the initialization script:**
   ```bash
   python init_db.py
   ```

### 4. Update CORS Settings

After deployment, update the CORS origins in `main.py`:

```python
origins = [
    "http://localhost:54321",
    "http://localhost:8000", 
    "http://localhost",
    "http://127.0.0.1",
    "https://your-actual-app-url.onrender.com",  # Replace with your actual URLs
    "https://your-admin-app-url.onrender.com",
]
```

### 5. Test Your API

Your API will be available at: `https://your-service-name.onrender.com`

Test endpoints:
- **Health Check**: `GET https://your-service-name.onrender.com/`
- **Stations**: `GET https://your-service-name.onrender.com/stations/`
- **Login**: `POST https://your-service-name.onrender.com/login`

## 🔧 Configuration Details

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:port/db` |
| `PORT` | Port for the web service | `10000` (set by Render) |

### Database Schema

The application will automatically create these tables:
- `users` - User accounts
- `user_profiles` - User profile information
- `instructor_profile` - Instructor details
- `learner_profiles` - Learner information
- `learner_test_bookings` - Test bookings
- `security_questions` - Security questions
- `user_security_answers` - User security answers
- `station` - Testing stations

### Default Data

The initialization script creates:
- **5 default stations** (Main, North, South, East, West)
- **6 security questions** for password recovery

## 🐛 Troubleshooting

### Common Issues

1. **Build Fails**
   - Check `requirements.txt` has all dependencies
   - Ensure Python version is compatible

2. **Database Connection Issues**
   - Verify `DATABASE_URL` is set correctly
   - Check database is running and accessible

3. **CORS Issues**
   - Update CORS origins with your actual frontend URLs
   - Ensure HTTPS URLs are used for production

4. **App Crashes on Startup**
   - Check logs in Render dashboard
   - Verify all environment variables are set
   - Run `python init_db.py` to initialize database

### Logs and Monitoring

- **View logs**: Go to your service → "Logs" tab
- **Monitor performance**: Use Render's built-in monitoring
- **Debug issues**: Use the "Shell" tab to run commands

## 🔄 Updating Your Deployment

1. **Push changes to GitHub**
2. **Render will automatically redeploy**
3. **Check logs for any issues**
4. **Test your endpoints**

## 📱 Frontend Integration

After deployment, update your Flutter apps to use the new API URL:

```dart
// In your API service files
static const String baseUrl = 'https://your-service-name.onrender.com';
```

## 🎉 You're Done!

Your FastAPI application is now deployed on Render and ready to serve your Flutter applications!
