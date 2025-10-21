#!/usr/bin/env python3
"""
Database initialization script for Smart License API
This script creates the database tables and inserts default data
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base, DATABASE_URL
from main import Station, SecurityQuestion
from passlib.context import CryptContext

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_database():
    """Initialize the database with tables and default data"""
    try:
        # Create engine and session with SSL configuration
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "connect_timeout": 10,
                "application_name": "smart_license_api_init"
            }
        )
        SessionLocal = sessionmaker(bind=engine)
        
        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Create session for data insertion
        db = SessionLocal()
        
        try:
            # Insert default stations if they don't exist
            print("Inserting default stations...")
            default_stations = [
                {"name": "Main Station", "num_grounds": 5},
                {"name": "North Station", "num_grounds": 3},
                {"name": "South Station", "num_grounds": 4},
                {"name": "East Station", "num_grounds": 2},
                {"name": "West Station", "num_grounds": 3},
            ]
            
            for station_data in default_stations:
                existing_station = db.query(Station).filter(Station.name == station_data["name"]).first()
                if not existing_station:
                    station = Station(**station_data)
                    db.add(station)
                    print(f"  ✅ Added station: {station_data['name']}")
                else:
                    print(f"  ⚠️  Station already exists: {station_data['name']}")
            
            # Insert default security questions if they don't exist
            print("Inserting default security questions...")
            default_questions = [
                "What is the name of your first pet?",
                "What was the model of your first car?",
                "In what city were you born?",
                "What is your mother's maiden name?",
                "What is the name of the street you grew up?",
                "What is the name of your primary school?"
            ]
            
            for question_text in default_questions:
                existing_question = db.query(SecurityQuestion).filter(SecurityQuestion.question == question_text).first()
                if not existing_question:
                    question = SecurityQuestion(question=question_text)
                    db.add(question)
                    print(f"  ✅ Added question: {question_text}")
                else:
                    print(f"  ⚠️  Question already exists: {question_text}")
            
            # Commit all changes
            db.commit()
            print("✅ Database initialization completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during data insertion: {e}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting database initialization...")
    init_database()
    print("🎉 Database initialization completed!")
