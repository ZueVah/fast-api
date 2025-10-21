# main.py for FastAPI application
# This file contains the main application logic, including models, schemas, and routes.
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import Session as DBSession
from typing import Literal, Optional, List
from datetime import datetime, date
from db import Base, engine, SessionLocal
from passlib.context import CryptContext

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# CORS origins - allow all for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- MODELS ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    name = Column(Text, nullable=False)
    surname = Column(Text, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Text, nullable=False)
    nationality = Column(Text, nullable=False)
    id_number = Column(Text, unique=True, nullable=False)
    contact_number = Column(Text, nullable=False)
    physical_address = Column(Text, nullable=False)
    race = Column(Text, nullable=False)

class InstructorProfile(Base):
    __tablename__ = "instructor_profile"
    user_id = Column(Integer, ForeignKey("user_profiles.user_id", ondelete="CASCADE"), primary_key=True)
    inf_nr = Column(Text, unique=True, nullable=False)
    station_id = Column(Integer, ForeignKey("station.station_id"), nullable=False)

class LearnerProfile(Base):
    __tablename__ = "learner_profiles"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    test_booking_date = Column(Date, nullable=True)
    learner_status = Column(Text, default="pending", nullable=False)
    registered_on = Column(DateTime, default=datetime.utcnow, nullable=False)
    license_code = Column(Text, nullable=True)

class LearnerTestBooking(Base):
    __tablename__ = "learner_test_bookings"
    booking_id = Column(Integer, primary_key=True, autoincrement=True)
    learner_id = Column(Integer, ForeignKey("learner_profiles.user_id", ondelete="CASCADE"), nullable=False)
    instructor_id = Column(Integer, ForeignKey("instructor_profile.user_id"), nullable=False)
    station_id = Column(Integer, ForeignKey("station.station_id"), nullable=False)
    test_date = Column(Date, nullable=False)
    result = Column(Text, default="pending", nullable=False)  # 'passed', 'failed', 'absent', 'pending'
    booking_date = Column(DateTime, default=datetime.utcnow)
    license_code = Column(Text, nullable=True)
    registered_on = Column(DateTime, default=datetime.utcnow, nullable=False)

class SecurityQuestion(Base):
    __tablename__ = "security_questions"
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)

class UserSecurityAnswer(Base):
    __tablename__ = "user_security_answers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("security_questions.id"), nullable=False)
    answer_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="unique_question_per_user"),)

class Station(Base):
    __tablename__ = "station"
    station_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    num_grounds = Column(Integer, nullable=False)

# Create all tables after defining all models
Base.metadata.create_all(bind=engine)

# ---------- SCHEMAS ----------
class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    role: Literal["learner", "instructor", "admin", "super_admin"]
    is_active: bool = True

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str

class InstructorProfileSchema(BaseModel):
    user_id: int
    inf_nr: str
    station_id: int

class UserProfileSchema(BaseModel):
    user_id: int
    name: str
    surname: str
    date_of_birth: date
    gender: str
    nationality: str
    id_number: str
    contact_number: str
    physical_address: str
    race: str

class LearnerProfileSchema(BaseModel):
    user_id: int
    learner_status: Optional[str] = "pending"
    test_booking_date: Optional[date] = None
    registered_on: Optional[datetime] = datetime.utcnow()
    license_code: Optional[str] = None

class LearnerTestBookingSchema(BaseModel):
    booking_id: Optional[int] = None
    learner_id: int
    instructor_id: int
    station_id: int
    test_date: date
    result: Optional[Literal['passed', 'failed', 'absent', 'pending']] = "pending"
    booking_date: Optional[datetime] = datetime.utcnow()
    license_code: Optional[str] = None
    registered_on: Optional[datetime] = datetime.utcnow()

class SecurityAnswerCreate(BaseModel):
    user_id: int
    question_id: int
    answer: str


class StationSchema(BaseModel):
    station_id: Optional[int] = None
    name: str
    num_grounds: int

class UserUpdateIsActive(BaseModel):
    is_active: bool

class ResultUpdateSchema(BaseModel):
    result: Literal['passed', 'failed', 'absent', 'pending']

# ---------- UTILS ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# ---------- ROUTES ----------
@app.get("/")
def read_root():
    return {"message": "FastAPI backend is running!"}


@app.post("/login")
def login(req: LoginRequest, db: DBSession = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == req.username).first()
        if not user or not verify_password(req.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if str(user.role) not in ["instructor", "admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only instructors, admins, and super admins can access this application")
        if not bool(user.is_active):
            raise HTTPException(status_code=403, detail="User inactive")

        return {
            "userid": user.id,
            "username": user.username,
            "role": user.role,
            "email": user.email
        }

    except HTTPException:
        # Re-raise HTTPExceptions as they are (don't convert to 500)
        raise
    except Exception as e:
        import traceback
        print("Login Error:", traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/users/")
def create_user(user: UserCreate, db: DBSession = Depends(get_db)):
    if db.query(User).filter((User.username == user.username) | (User.email == user.email)).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    hashed_password = get_password_hash(user.password)
    user_data = user.dict()
    user_data["password"] = hashed_password

    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/id/{user_id}")
def get_user_by_id(user_id: int, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/id/{user_id}")
def update_user(user_id: int, user: UserCreate, db: DBSession = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == user_id).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Exclude current user from uniqueness check
    if db.query(User).filter(
        ((User.username == user.username) | (User.email == user.email)) & (User.id != user_id)
    ).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")

    hashed_password = get_password_hash(user.password)
    user_data = user.dict()
    user_data["password"] = hashed_password

    for field, value in user_data.items():
        setattr(existing_user, field, value)
    
    db.commit()
    return existing_user

@app.get("/users/{username}")
def get_user_by_username(username: str, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/user-profiles/")
def create_user_profile(profile: UserProfileSchema, db: DBSession = Depends(get_db)):
    db.add(UserProfile(**profile.dict()))
    db.commit()
    return profile

@app.get("/user-profiles/")
def get_all_user_profiles(db: DBSession = Depends(get_db)):
    return db.query(UserProfile).all()

@app.get("/user-profiles/{user_id}")
def get_user_profile(user_id: int, db: DBSession = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.put("/user-profiles/{user_id}")
def update_user_profile(user_id: int, profile: UserProfileSchema, db: DBSession = Depends(get_db)):
    existing = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in profile.dict().items():
        setattr(existing, field, value)
    db.commit()
    return existing

@app.delete("/user-profiles/{user_id}")
def delete_user_profile(user_id: int, db: DBSession = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(profile)
    db.commit()
    return {"detail": "Deleted"}

@app.post("/instructor-profiles/")
def create_instructor_profile(profile: InstructorProfileSchema, db: DBSession = Depends(get_db)):
    # Check if user profile exists
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == profile.user_id).first()
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Check if station exists
    station = db.query(Station).filter(Station.station_id == profile.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Selected station does not exist")
    
    # Prevent duplicate instructor profiles
    if db.query(InstructorProfile).filter(InstructorProfile.user_id == profile.user_id).first():
        raise HTTPException(status_code=400, detail="Instructor profile already exists")
    
    if db.query(InstructorProfile).filter(InstructorProfile.inf_nr == profile.inf_nr).first():
        raise HTTPException(status_code=400, detail="Instructor number already exists")

    db.add(InstructorProfile(**profile.dict()))
    db.commit()
    return profile

@app.put("/users/{user_id}/is_active")
def update_user_is_active(
    user_id: int,
    user_update: UserUpdateIsActive,
    db: DBSession = Depends(get_db)
):
    existing_user = db.query(User).filter(User.id == user_id).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    setattr(existing_user, "is_active", user_update.is_active)
    db.commit()
    db.refresh(existing_user)

    return {"id": existing_user.id, "is_active": existing_user.is_active}

@app.get("/users/{user_id}/is_active")
def get_user_is_active(user_id: int, db: DBSession = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == user_id).first()
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"id": existing_user.id, "is_active": existing_user.is_active}

@app.get("/instructor-profiles/")
def get_all_instructor_profiles(db: DBSession = Depends(get_db)):
    return db.query(InstructorProfile).all()


@app.get("/instructor-profiles/{user_id}")
def get_instructor_profile(user_id: int, db: DBSession = Depends(get_db)):
    profile = db.query(InstructorProfile).filter(InstructorProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Instructor profile not found")
    return profile


@app.put("/instructor-profiles/{user_id}")
def update_instructor_profile(user_id: int, profile: InstructorProfileSchema, db: DBSession = Depends(get_db)):
    existing = db.query(InstructorProfile).filter(InstructorProfile.user_id == user_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Instructor profile not found")
    setattr(existing, "inf_nr", profile.inf_nr)
    db.commit()
    return existing


@app.delete("/instructor-profiles/{user_id}")
def delete_instructor_profile(user_id: int, db: DBSession = Depends(get_db)):
    profile = db.query(InstructorProfile).filter(InstructorProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Instructor profile not found")
    db.delete(profile)
    db.commit()
    return {"detail": "Deleted"}

@app.post("/learner-profiles/")
def create_learner_profile(profile: LearnerProfileSchema, db: DBSession = Depends(get_db)):
    db.add(LearnerProfile(**profile.dict()))
    db.commit()
    return profile

@app.get("/learner-profiles/")
def get_all_learner_profiles(db: DBSession = Depends(get_db)):
    return db.query(LearnerProfile).all()

@app.get("/learner-profiles/{user_id}")
def get_learner_profile(user_id: int, db: DBSession = Depends(get_db)):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.put("/learner-profiles/{user_id}")
def update_learner_profile(user_id: int, profile: LearnerProfileSchema, db: DBSession = Depends(get_db)):
    existing = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in profile.dict().items():
        setattr(existing, field, value)
    db.commit()
    return existing

@app.delete("/learner-profiles/{user_id}")
def delete_learner_profile(user_id: int, db: DBSession = Depends(get_db)):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(profile)
    db.commit()
    return {"detail": "Deleted"}

@app.post("/learner-test-bookings/")
def create_test_booking(booking: LearnerTestBookingSchema, db: DBSession = Depends(get_db)):
    db.add(LearnerTestBooking(**booking.dict(exclude_unset=True)))
    db.commit()
    return booking

@app.get("/learner-test-bookings/")
def get_all_test_bookings(db: DBSession = Depends(get_db)):
    return db.query(LearnerTestBooking).all()

@app.put("/learner-test-bookings/{booking_id}/result")
def update_test_result(booking_id: int, result_update: ResultUpdateSchema, db: DBSession = Depends(get_db)):
    """Update the result of a test booking"""
    booking = db.query(LearnerTestBooking).filter(LearnerTestBooking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.result = result_update.result
    db.commit()
    return {"message": f"Test result updated to {result_update.result}", "booking_id": booking_id, "result": result_update.result}

@app.get("/learner-test-bookings/{booking_id}")
def get_test_booking(booking_id: int, db: DBSession = Depends(get_db)):
    booking = db.query(LearnerTestBooking).filter(LearnerTestBooking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@app.get("/learner-test-bookings/learner/{learner_id}")
def get_bookings_by_learner(learner_id: int, db: DBSession = Depends(get_db)):
    bookings = db.query(LearnerTestBooking).filter(LearnerTestBooking.learner_id == learner_id).all()
    if not bookings:
        raise HTTPException(status_code=404, detail="No bookings found for this learner")
    return bookings

@app.get("/learner-test-bookings/pending/{date}")
def get_pending_learners(date: str, db: DBSession = Depends(get_db)):
    """Get all pending learners for a specific date"""
    pending_bookings = db.query(LearnerTestBooking).filter(
        LearnerTestBooking.test_date == date,
        LearnerTestBooking.result == 'pending'
    ).all()
    return pending_bookings

@app.get("/learner-test-bookings/completed/{date}")
def get_completed_learners(date: str, db: DBSession = Depends(get_db)):
    """Get all completed learners for a specific date"""
    completed_bookings = db.query(LearnerTestBooking).filter(
        LearnerTestBooking.test_date == date,
        LearnerTestBooking.result != 'pending'
    ).all()
    return completed_bookings

@app.get("/learner-test-bookings/results/{date}")
def get_all_results_by_date(date: str, db: DBSession = Depends(get_db)):
    """Get all test results (pending, passed, failed, absent) for a specific date"""
    all_bookings = db.query(LearnerTestBooking).filter(
        LearnerTestBooking.test_date == date
    ).all()
    
    # Group results by status
    results_summary = {
        "pending": [],
        "passed": [],
        "failed": [],
        "absent": []
    }
    
    for booking in all_bookings:
        result_status = booking.result
        if result_status in results_summary:
            results_summary[result_status].append({
                "booking_id": booking.booking_id,
                "learner_id": booking.learner_id,
                "instructor_id": booking.instructor_id,
                "result": booking.result,
                "license_code": booking.license_code,
                "test_date": booking.test_date,
                "booking_date": booking.booking_date
            })
    
    return {
        "date": date,
        "total_bookings": len(all_bookings),
        "results": results_summary,
        "summary": {
            "pending": len(results_summary["pending"]),
            "passed": len(results_summary["passed"]),
            "failed": len(results_summary["failed"]),
            "absent": len(results_summary["absent"])
        }
    }

@app.put("/learner-test-bookings/{booking_id}")
def update_test_booking(booking_id: int, booking: LearnerTestBookingSchema, db: DBSession = Depends(get_db)):
    existing = db.query(LearnerTestBooking).filter(LearnerTestBooking.booking_id == booking_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Booking not found")
    for field, value in booking.dict(exclude_unset=True).items():
        setattr(existing, field, value)
    db.commit()
    return existing

@app.delete("/learner-test-bookings/{booking_id}")
def delete_test_booking(booking_id: int, db: DBSession = Depends(get_db)):
    booking = db.query(LearnerTestBooking).filter(LearnerTestBooking.booking_id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    db.delete(booking)
    db.commit()
    return {"detail": "Deleted"}

@app.get("/security-questions/")
def get_all_questions(db: DBSession = Depends(get_db)):
    return db.query(SecurityQuestion).all()

@app.get("/security-questions/id/{question_id}")
def get_question_by_id(question_id: int, db: DBSession = Depends(get_db)):
    question = db.query(SecurityQuestion).filter(SecurityQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@app.post("/user-security-answers/")
def create_security_answer(answer: SecurityAnswerCreate, db: DBSession = Depends(get_db)):
    hashed = get_password_hash(answer.answer)
    db_answer = UserSecurityAnswer(
        user_id=answer.user_id,
        question_id=answer.question_id,
        answer_hash=hashed
    )
    db.add(db_answer)
    db.commit()
    return {"message": "Answer saved"}

@app.get("/user-security-answers/id/{user_id}")
def get_security_answers_by_user(user_id: int, db: DBSession = Depends(get_db)):
    answers = db.query(UserSecurityAnswer).filter(UserSecurityAnswer.user_id == user_id).all()
    if not answers:
        raise HTTPException(status_code=404, detail="Answers not found")
    return answers

@app.on_event("startup")
def insert_default_questions():
    default_qs = [
        "What is the name of your first pet?",
        "What was the model of your first car?",
        "In what city were you born?",
        "What is your mother's maiden name?",
        "What is the name of the street you grew up?",
        "What is the name of your primary school?"
    ]
    db = SessionLocal()
    for q in default_qs:
        if not db.query(SecurityQuestion).filter(SecurityQuestion.question == q).first():
            db.add(SecurityQuestion(question=q))
    db.commit()
    db.close()

@app.post("/stations/")
def create_station(station: StationSchema, db: DBSession = Depends(get_db)):
    db_station = Station(**station.dict(exclude_unset=True))
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station

@app.get("/stations/")
def get_all_stations(db: DBSession = Depends(get_db)):
    return db.query(Station).all()

@app.get("/stations/{station_id}")
def get_station_by_id(station_id: int, db: DBSession = Depends(get_db)):
    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return station

@app.put("/stations/{station_id}")
def update_station(station_id: int, station: StationSchema, db: DBSession = Depends(get_db)):
    existing = db.query(Station).filter(Station.station_id == station_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Station not found")
    for field, value in station.dict(exclude_unset=True).items():
        setattr(existing, field, value)
    db.commit()
    return existing

@app.delete("/stations/{station_id}")
def delete_station(station_id: int, db: DBSession = Depends(get_db)):
    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    db.delete(station)
    db.commit()
    return {"detail": "Deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
