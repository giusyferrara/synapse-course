"""
London Transport Database Models
=================================
Database models for storing TfL transport data
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from database.config import Base
import datetime


class TubeLineModel(Base):
    """Store London Underground lines"""
    __tablename__ = "tube_lines"
    
    id = Column(Integer, primary_key=True)
    line_id = Column(String(50), unique=True, index=True)
    line_name = Column(String(100))
    mode_name = Column(String(50))  # tube, bus, dlr, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    stops = relationship("TransportStop", back_populates="line")
    arrivals = relationship("TransportArrival", back_populates="line")


class TransportStop(Base):
    """Store transport stops (tube stations, bus stops)"""
    __tablename__ = "transport_stops"
    
    id = Column(Integer, primary_key=True)
    stop_id = Column(String(50), unique=True, index=True)
    stop_name = Column(String(200))
    line_id = Column(Integer, ForeignKey("tube_lines.id"), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    zone = Column(String(10), nullable=True)
    modes = Column(JSON)  # ['tube', 'bus', 'dlr']
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    line = relationship("TubeLineModel", back_populates="stops")
    arrivals = relationship("TransportArrival", back_populates="stop")


class TransportArrival(Base):
    """Store real-time arrival predictions"""
    __tablename__ = "transport_arrivals"
    
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey("tube_lines.id"))
    stop_id = Column(Integer, ForeignKey("transport_stops.id"))
    destination = Column(String(200))
    platform_name = Column(String(100), nullable=True)
    time_to_station = Column(Integer)  # seconds
    expected_arrival = Column(DateTime)
    current_location = Column(String(200), nullable=True)
    prediction_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    line = relationship("TubeLineModel", back_populates="arrivals")
    stop = relationship("TransportStop", back_populates="arrivals")


class TfLAPIRequest(Base):
    """Track TfL API requests for learning analytics"""
    __tablename__ = "tfl_api_requests"
    
    id = Column(Integer, primary_key=True)
    student_record_id = Column(Integer, ForeignKey("students.id"))
    request_type = Column(String(50))  # 'lines', 'stops', 'arrivals'
    request_params = Column(JSON)
    response_code = Column(Integer)
    response_time = Column(Float)  # in seconds
    success = Column(Boolean)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    student = relationship("Student")


class LondonTransportExercise(Base):
    """Track student progress through London Transport exercises"""
    __tablename__ = "london_transport_exercises"
    
    id = Column(Integer, primary_key=True)
    student_record_id = Column(Integer, ForeignKey("students.id"))
    exercise_id = Column(String(50))  # e.g., "lesson_1_first_api_call"
    completed = Column(Boolean, default=False)
    attempts = Column(Integer, default=0)
    code_submitted = Column(Text)
    api_response = Column(JSON)
    score = Column(Float, nullable=True)  # 0-100
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    student = relationship("Student")
