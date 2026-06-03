from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from .config import Base
import datetime

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True)
    neurodivergent_type = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    sessions = relationship("LearningSession", back_populates="student")
    conversations = relationship("ChatConversation", back_populates="student")

class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(Integer, primary_key=True)
    student_record_id = Column(Integer, ForeignKey("students.id"))
    session_start = Column(DateTime, default=datetime.datetime.utcnow)
    session_end = Column(DateTime)
    code_submitted = Column(Text)
    mood_input = Column(String)
    stress_level = Column(Float)
    emotional_state = Column(JSON)

    student = relationship("Student", back_populates="sessions")
    responses = relationship("AIResponse", back_populates="session")
    conversations = relationship("ChatConversation", back_populates="session")

class AIResponse(Base):
    __tablename__ = "ai_responses"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("learning_sessions.id"))
    prompt_used = Column(Text)
    response_text = Column(Text)
    model_used = Column(String)
    tool_used = Column(String)
    ai_response = Column(Text)
    response_time = Column(Float)
    was_helpful = Column(Boolean)
    was_accurate = Column(Boolean)

    session = relationship("LearningSession", back_populates="responses")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    student_record_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    user_id = Column(Integer, nullable=True, index=True)  # auth users.id (cookie synapse_user) — joins to user_progress
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    most_helpful = Column(Text, nullable=True)
    improvements = Column(Text, nullable=True)
    background = Column(String, nullable=True)
    overall_rating = Column(Integer, nullable=True)
    ai_helpfulness = Column(Integer, nullable=True)
    accessibility_rating = Column(Integer, nullable=True)
    recommend = Column(Integer, nullable=True)
    features_used = Column(Text, nullable=True)  # JSON array of feature keys
    consent = Column(Boolean, nullable=True)     # opt-in to use responses for research

# Chat-related tables
class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True)
    student_record_id = Column(Integer, ForeignKey("students.id"))
    session_id = Column(Integer, ForeignKey("learning_sessions.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_message = Column(DateTime, default=datetime.datetime.utcnow)
    topic = Column(String)
    is_active = Column(Boolean, default=True)
    user_id = Column(Integer)

    student = relationship("Student", back_populates="conversations")
    session = relationship("LearningSession", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", order_by="ChatMessage.timestamp")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"))
    role = Column(String)  # 'user' or 'assistant'
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    emotion_state = Column(JSON)
    llm_model = Column(String(20))  # Store emotion analysis as JSON

    conversation = relationship("ChatConversation", back_populates="messages")

class CourseProgress(Base):
    """Track user progress through course topics"""
    __tablename__ = 'course_progress'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(100), nullable=False, index=True)
    topic_id = Column(String(100), nullable=False, index=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<CourseProgress(student={self.student_id}, topic={self.topic_id}, completed={self.completed})>"


# ============================================================================
# RESEARCH PARTICIPANT MODEL — ShopSecure Vulnerability Assessment Study
# ============================================================================
# Experimental Design: 2x2 Factorial (Group A/B x ND/NT)
# References:
#   - Kestin et al. (2025) Harvard RCT methodology
#   - Bloom (1984) 2 Sigma Problem
#   - Hart & Staveland (1988) NASA-TLX
#   - Brooke (1996) System Usability Scale
#   - Anderson & Krathwohl (2001) Bloom's Taxonomy
#   - Hake (1998) Normalised Learning Gain
#   - Graesser et al. (2014) AutoTutor interaction logging
# ============================================================================

class ResearchParticipant(Base):
    """
    Research study participant — Web Vulnerability Assessment with AI Tutoring
    Each participant is assigned to Group A (AI Tutored) or Group B (Self-Directed)
    """
    __tablename__ = 'research_participants'

    # ── Primary Key & Identity ──────────────────────────────────────────
    id = Column(Integer, primary_key=True, autoincrement=True)
    participant_code = Column(String(20), unique=True, nullable=False, index=True)
    nickname = Column(String(100), unique=True, index=True)
    email = Column(String(255))

    # ── Group Assignment (IV1) ──────────────────────────────────────────
    # 'A' = AI Tutored (Socratic AI chat visible)
    # 'B' = Self-Directed (static OWASP reference materials only)
    group_assignment = Column(String(1))  # 'A' or 'B'

    # ── Demographics (Phase 1) ──────────────────────────────────────────
    age = Column(String(20))          # '18-21', '22-25', '26-30', '30+'
    gender = Column(String(50))
    study_program = Column(String(100))

    # ── Neurodivergent Status (IV2) ─────────────────────────────────────
    # Voluntary self-disclosure (Tsai et al. 2020)
    neurodivergence_type = Column(String(200))   # CSV: 'adhd,dyslexia' or 'no' or 'prefer_not_to_say'
    neurodivergence_details = Column(Text)       # Free text for 'other'
    nd_formal_diagnosis = Column(String(50))     # 'yes', 'no', 'prefer_not_to_say'
    # Computed: True if any ND selected (not 'no'/'prefer_not_to_say')
    is_neurodivergent = Column(Boolean)

    # ── Experience Levels ───────────────────────────────────────────────
    programming_experience = Column(String(50))   # 'none', 'beginner', 'intermediate', 'advanced'
    security_experience = Column(String(50))      # 'none', 'basic', 'intermediate', 'advanced'
    ai_chatbot_experience = Column(String(50))    # 'never', 'occasionally', 'frequently'

    # ── New Pre-Survey Fields (2026) ────────────────────────────────────
    chosen_path = Column(String(20))              # 'beginner' or 'experienced'
    ai_for_learning = Column(String(50))          # 'never', 'tried_unhelpful', 'tried_helpful', 'regularly'
    platforms_used = Column(String(50))           # 'never', 'tried_incomplete', 'completed', 'regular'
    when_stuck = Column(Text)                     # JSON array of strategies
    learning_style = Column(Text)                 # JSON array of preferences
    self_confidence_pre = Column(Integer)         # 1-5 Likert

    # ── Pre-Test: Web Security Knowledge (Phase 2) ──────────────────────
    # 15-20 MC items mapped to Bloom's Taxonomy levels
    # (Remember, Understand, Apply, Analyse)
    # Anderson & Krathwohl (2001)
    pre_test_answers = Column(JSON)     # {"q1": "b", "q2": "c", ...}
    pre_test_score = Column(Integer)    # Raw score (0-20)
    pre_test_max = Column(Integer)      # Maximum possible score
    pre_test_bloom_remember = Column(Integer)    # Score on Remember-level items
    pre_test_bloom_understand = Column(Integer)  # Score on Understand-level items
    pre_test_bloom_apply = Column(Integer)       # Score on Apply-level items
    pre_test_bloom_analyse = Column(Integer)     # Score on Analyse-level items

    # ── Task Data (Phase 3) ─────────────────────────────────────────────
    # ShopSecure vulnerability discovery — 75 minutes
    task_start_time = Column(DateTime)
    task_end_time = Column(DateTime)
    task_elapsed_time = Column(Integer)     # seconds actually spent
    task_time_remaining = Column(Integer)   # seconds left when submitted
    task_completed = Column(Boolean, default=False)
    task_submission_time = Column(DateTime)

    # Vulnerability Findings — the core DV
    # JSON array: [{
    #   "finding_id": 1,
    #   "timestamp": "2026-03-15T14:23:00Z",
    #   "description": "SQL injection in login form",
    #   "exploitation": "admin' OR 1=1-- in username field",
    #   "impact": "Full database access - Confidentiality breach",
    #   "owasp_category": "A03:2021 Injection",
    #   "score_identification": 2,   (0-2, scored later)
    #   "score_exploitation": 3,     (0-3, scored later)
    #   "score_impact": 2,           (0-2, scored later)
    #   "score_owasp": 1,            (0-1, scored later)
    #   "score_total": 8             (0-8 per finding)
    # }]
    vulnerability_findings = Column(JSON)
    vuln_count = Column(Integer, default=0)           # Total findings submitted
    vuln_unique_count = Column(Integer)                # Unique vulns (deduped)
    vuln_total_score = Column(Integer)                 # Sum of all finding scores
    vuln_avg_quality = Column(Float)                   # Average score per finding
    vuln_owasp_categories_found = Column(JSON)         # List of distinct OWASP cats
    vuln_scored_by = Column(String(100))               # 'AUTO' or researcher name
    vuln_scored_at = Column(DateTime)

    # ── AI Interaction Logs (Phase 3, Group A only) ─────────────────────
    # Graesser et al. (2014) AutoTutor interaction patterns
    # JSON array: [{
    #   "timestamp": "2026-03-15T14:25:00Z",
    #   "role": "user" | "assistant" | "system",
    #   "message": "...",
    #   "type": "question" | "hint_request" | "encouragement" | "explanation" | "nudge"
    # }]
    interaction_logs = Column(JSON)
    ai_messages_count = Column(Integer, default=0)     # Total AI messages sent
    ai_hints_requested = Column(Integer, default=0)    # Times student asked for help
    ai_encouragements_sent = Column(Integer, default=0)  # 40s/90s/180s interventions
    ai_idle_triggers = Column(JSON)    # Timestamps of idle interventions
    ai_avg_response_time = Column(Float)  # Avg seconds between student msg and AI reply

    # ── Post-Test: Web Security Knowledge (Phase 4) ─────────────────────
    # Parallel form of pre-test (same difficulty, different questions)
    # Hake (1998) normalised gain: G = (post - pre) / (max - pre)
    post_test_answers = Column(JSON)
    post_test_score = Column(Integer)
    post_test_max = Column(Integer)
    post_test_bloom_remember = Column(Integer)
    post_test_bloom_understand = Column(Integer)
    post_test_bloom_apply = Column(Integer)
    post_test_bloom_analyse = Column(Integer)
    normalised_gain = Column(Float)  # G = (post - pre) / (max - pre)

    # ── NASA-TLX Raw (Phase 5) ──────────────────────────────────────────
    # Hart & Staveland (1988) — 5 subscales, 0-100 each
    # Physical Demand omitted (not relevant for educational technology)
    nasa_mental_demand = Column(Integer)     # 0-100
    nasa_temporal_demand = Column(Integer)   # 0-100
    nasa_performance = Column(Integer)       # 0-100 (self-assessed, inverted)
    nasa_effort = Column(Integer)            # 0-100
    nasa_frustration = Column(Integer)       # 0-100
    nasa_tlx_avg = Column(Float)             # Average of 5 subscales

    # ── System Usability Scale (Phase 6, Group A only) ──────────────────
    # Brooke (1996) — 10 items, 1-5 Likert scale
    # SUS Score formula: ((sum of odd items - 5) + (25 - sum of even items)) * 2.5
    # Score range: 0-100. Above 68 = above average.
    sus_q1 = Column(Integer)   # I would like to use this system frequently
    sus_q2 = Column(Integer)   # I found the system unnecessarily complex
    sus_q3 = Column(Integer)   # I thought the system was easy to use
    sus_q4 = Column(Integer)   # I would need tech support to use this
    sus_q5 = Column(Integer)   # I found the functions well integrated
    sus_q6 = Column(Integer)   # I thought there was too much inconsistency
    sus_q7 = Column(Integer)   # Most people would learn to use this quickly
    sus_q8 = Column(Integer)   # I found the system very awkward to use
    sus_q9 = Column(Integer)   # I felt very confident using the system
    sus_q10 = Column(Integer)  # I needed to learn a lot before I could use it
    sus_total = Column(Float)  # Computed SUS score (0-100)

    # ── Perception Questionnaire (Phase 7) ──────────────────────────────
    # Custom 5-point Likert items (1=Strongly Disagree, 5=Strongly Agree)
    # Items vary slightly between Group A and Group B
    perception_q1 = Column(Integer)   # I felt supported during the task
    perception_q2 = Column(Integer)   # The explanations helped me understand vulnerabilities
    perception_q3 = Column(Integer)   # The difficulty level was appropriate
    perception_q4 = Column(Integer)   # I felt engaged throughout the session
    perception_q5 = Column(Integer)   # I would use this platform again
    perception_q6 = Column(Integer)   # I learned something new about web security
    perception_q7 = Column(Integer)   # The hints were useful (A) / Resources were adequate (B)
    perception_q8 = Column(Integer)   # I felt motivated to keep trying
    perception_q9 = Column(Integer)   # The instructions were clear
    perception_q10 = Column(Integer)  # I feel more confident about finding vulnerabilities
    perception_q11 = Column(Integer)  # The pace of learning was comfortable
    perception_q12 = Column(Integer)  # I would recommend this to a friend
    perception_avg = Column(Float)    # Average of all perception items

    # ── Qualitative Reflection (Phase 8) ────────────────────────────────
    qual_easiest_vuln = Column(Text)        # What was easiest to find and why
    qual_hardest_vuln = Column(Text)        # What was hardest and why
    qual_strategy = Column(Text)            # Strategy used to look for vulns
    qual_different_next = Column(Text)      # What would you do differently
    qual_confidence_rating = Column(Integer)  # 1-5 self-assessed
    # Group A specific
    qual_ai_helpfulness = Column(Integer)   # 1-5 how helpful was AI tutor
    qual_ai_moment = Column(Text)           # Moment where AI encouragement helped
    qual_ai_understand_why = Column(Text)   # Did AI help understand WHY not just THAT
    # Group B specific
    qual_resources_adequate = Column(Integer)  # 1-5 were resources enough
    qual_stuck_moment = Column(Text)           # Moment felt stuck, wished for more guidance

    # ── Consent & Timestamps ────────────────────────────────────────────
    consent_given = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # ── Accessibility Preferences (logged automatically) ────────────────
    accessibility_dark_mode = Column(Boolean, default=False)
    accessibility_dyslexia_font = Column(Boolean, default=False)
    accessibility_tts = Column(Boolean, default=False)
    accessibility_reading_pointer = Column(Boolean, default=False)

    def __repr__(self):
        return f"<ResearchParticipant(code={self.participant_code}, group={self.group_assignment}, nd={self.is_neurodivergent})>"

    def compute_normalised_gain(self):
        """Hake (1998): G = (post - pre) / (max - pre)"""
        if self.pre_test_score is not None and self.post_test_score is not None and self.pre_test_max:
            denominator = self.pre_test_max - self.pre_test_score
            if denominator > 0:
                self.normalised_gain = round(
                    (self.post_test_score - self.pre_test_score) / denominator, 4
                )
            elif self.post_test_score == self.pre_test_max:
                self.normalised_gain = 1.0  # Perfect pre AND post
            else:
                self.normalised_gain = 0.0

    def compute_sus_score(self):
        """Brooke (1996): SUS = ((sum_odd - 5) + (25 - sum_even)) * 2.5"""
        odd = [self.sus_q1, self.sus_q3, self.sus_q5, self.sus_q7, self.sus_q9]
        even = [self.sus_q2, self.sus_q4, self.sus_q6, self.sus_q8, self.sus_q10]
        if all(v is not None for v in odd + even):
            sum_odd = sum(v - 1 for v in odd)      # Subtract 1 from odd items
            sum_even = sum(5 - v for v in even)     # 5 minus even items
            self.sus_total = round((sum_odd + sum_even) * 2.5, 2)

    def compute_nasa_tlx_avg(self):
        """Hart & Staveland (1988): Raw TLX average of available subscales.
        Survey collects 3 items (mental_demand, effort, frustration).
        Computes average over whichever scales have data."""
        scales = [
            self.nasa_mental_demand, self.nasa_temporal_demand,
            self.nasa_performance, self.nasa_effort, self.nasa_frustration
        ]
        available = [v for v in scales if v is not None]
        if available:
            self.nasa_tlx_avg = round(sum(available) / len(available), 2)

    def compute_vuln_scores(self):
        """Score vulnerability findings based on correctness of each field.
        Each finding scored 0-4: cwe_code(1) + exploitation(1) + impact_cia(1) + mitigation(1)
        Correct mitigations end with '_correct', correct CIA is non-empty."""
        import json
        findings = self.vulnerability_findings
        if not findings:
            return
        if isinstance(findings, str):
            findings = json.loads(findings)
        if not isinstance(findings, list) or len(findings) == 0:
            return

        total_score = 0
        unique_cwes = set()
        for f in findings:
            score = 0
            cwe = f.get('cwe_code', '')
            if cwe and cwe.startswith('CWE-'):
                score += 1
                unique_cwes.add(cwe)
            exploitation = f.get('exploitation', '')
            if exploitation:
                score += 1
            impact_cia = f.get('impact_cia', '')
            if impact_cia:
                score += 1
            mitigation = f.get('mitigation', '')
            if mitigation and '_correct' in mitigation:
                score += 1
            total_score += score

        self.vuln_count = len(findings)
        self.vuln_unique_count = len(unique_cwes)
        self.vuln_total_score = total_score
        self.vuln_avg_quality = round(total_score / len(findings), 2) if findings else 0


# ============================================================================
# ADAPTIVE QUIZ TELEMETRY — ordinary app usage data (like CourseProgress).
# DELIBERATELY SEPARATE from ResearchParticipant: keyed by the normal app
# student_id, NOT by participant_code, and never written to research exports.
# ============================================================================

class QuizAttempt(Base):
    """One graded answer. Append-only telemetry for adaptive selection + stats."""
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(100), nullable=False, index=True)
    question_id = Column(String(120), nullable=False, index=True)
    template_id = Column(String(120), nullable=True)   # null if hand-authored
    skill_tag = Column(String(40), nullable=False, index=True)
    category = Column(String(20), nullable=False)
    severity = Column(String(10), nullable=True)
    chosen_option = Column(String(4))
    is_correct = Column(Boolean, nullable=False)
    time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    def __repr__(self):
        return f"<QuizAttempt(student={self.student_id}, q={self.question_id}, correct={self.is_correct})>"


class QuizReview(Base):
    """Per-(student, question) spaced-repetition state (SM-2 lite)."""
    __tablename__ = "quiz_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(100), nullable=False, index=True)
    question_id = Column(String(120), nullable=False, index=True)
    skill_tag = Column(String(40), nullable=False, index=True)
    consecutive_correct = Column(Integer, default=0)
    ease = Column(Float, default=2.5)
    interval_days = Column(Float, default=0.0)
    next_due_at = Column(DateTime, index=True)
    last_result = Column(Boolean)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("student_id", "question_id", name="uq_quiz_review_student_question"),
    )

    def __repr__(self):
        return f"<QuizReview(student={self.student_id}, q={self.question_id}, due={self.next_due_at})>"


from .london_transport_models import TubeLineModel, TransportStop, TransportArrival, TfLAPIRequest, LondonTransportExercise
