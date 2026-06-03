--
-- PostgreSQL database dump
--

\restrict 8AsgUXuvgS6pJAGyRVh6oqx2FDO3t07gkhFvvrTwuzBZaVEDGL7aTr2yzW0tE1g

-- Dumped from database version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ai_responses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ai_responses (
    id integer NOT NULL,
    session_id integer,
    tool_used character varying,
    ai_response text,
    response_time double precision,
    was_helpful boolean,
    was_accurate boolean,
    prompt_used text,
    response_text text,
    model_used character varying
);


--
-- Name: ai_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.ai_responses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ai_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.ai_responses_id_seq OWNED BY public.ai_responses.id;


--
-- Name: chat_conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_conversations (
    id integer NOT NULL,
    student_record_id integer,
    session_id integer,
    created_at timestamp without time zone,
    last_message timestamp without time zone,
    topic character varying,
    is_active boolean,
    user_id integer
);


--
-- Name: chat_conversations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chat_conversations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chat_conversations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chat_conversations_id_seq OWNED BY public.chat_conversations.id;


--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_messages (
    id integer NOT NULL,
    conversation_id integer,
    role character varying,
    message text,
    "timestamp" timestamp without time zone,
    emotion_state json,
    llm_model character varying(20)
);


--
-- Name: chat_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.chat_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: chat_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.chat_messages_id_seq OWNED BY public.chat_messages.id;


--
-- Name: course_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.course_progress (
    id integer NOT NULL,
    student_id character varying(100) NOT NULL,
    topic_id character varying(100) NOT NULL,
    completed boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: course_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.course_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: course_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.course_progress_id_seq OWNED BY public.course_progress.id;


--
-- Name: feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback (
    id integer NOT NULL,
    student_record_id integer,
    "timestamp" timestamp without time zone,
    most_helpful text,
    improvements text,
    background character varying,
    user_id integer,
    overall_rating integer,
    ai_helpfulness integer,
    accessibility_rating integer,
    recommend integer,
    features_used text,
    consent boolean
);


--
-- Name: feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.feedback_id_seq OWNED BY public.feedback.id;


--
-- Name: lab_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lab_sessions (
    id integer NOT NULL,
    user_id integer,
    participant_code character varying(20),
    lab_type character varying(50) DEFAULT 'shopsecure'::character varying NOT NULL,
    session_token character varying(64) NOT NULL,
    container_id character varying(64),
    container_name character varying(100),
    container_port integer,
    status character varying(20) DEFAULT 'starting'::character varying NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    last_activity_at timestamp without time zone DEFAULT now() NOT NULL,
    terminated_at timestamp without time zone,
    extensions_count integer DEFAULT 0 NOT NULL,
    max_extensions integer DEFAULT 3 NOT NULL,
    error_message text,
    CONSTRAINT lab_sessions_owner_check CHECK (((user_id IS NOT NULL) OR (participant_code IS NOT NULL))),
    CONSTRAINT lab_sessions_status_check CHECK (((status)::text = ANY ((ARRAY['starting'::character varying, 'ready'::character varying, 'expired'::character varying, 'terminated'::character varying, 'error'::character varying])::text[])))
);


--
-- Name: lab_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lab_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lab_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lab_sessions_id_seq OWNED BY public.lab_sessions.id;


--
-- Name: learning_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning_sessions (
    id integer NOT NULL,
    student_record_id integer,
    session_start timestamp without time zone,
    session_end timestamp without time zone,
    code_submitted text,
    mood_input character varying,
    stress_level double precision,
    emotional_state json
);


--
-- Name: learning_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.learning_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: learning_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.learning_sessions_id_seq OWNED BY public.learning_sessions.id;


--
-- Name: lesson_content; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lesson_content (
    id integer NOT NULL,
    topic_id character varying(100) NOT NULL,
    topic_name character varying(255) NOT NULL,
    level character varying(50) NOT NULL,
    introduction text NOT NULL,
    explanation text NOT NULL,
    key_points jsonb NOT NULL,
    misconceptions jsonb,
    applications jsonb,
    duration character varying(50),
    difficulty integer DEFAULT 1,
    prerequisites jsonb,
    learning_outcomes jsonb,
    source_book character varying(255),
    source_chapter character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: lesson_content_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lesson_content_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lesson_content_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lesson_content_id_seq OWNED BY public.lesson_content.id;


--
-- Name: lesson_examples; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lesson_examples (
    id integer NOT NULL,
    topic_id character varying(100),
    title character varying(255) NOT NULL,
    description text,
    code text NOT NULL,
    explanation text,
    expected_output text,
    difficulty integer DEFAULT 1,
    order_index integer DEFAULT 0
);


--
-- Name: lesson_examples_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lesson_examples_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lesson_examples_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lesson_examples_id_seq OWNED BY public.lesson_examples.id;


--
-- Name: lesson_exercises; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lesson_exercises (
    id integer NOT NULL,
    topic_id character varying(100),
    title character varying(255) NOT NULL,
    description text NOT NULL,
    difficulty character varying(20) NOT NULL,
    starter_code text,
    solution_code text,
    expected_output text,
    hints jsonb,
    test_cases jsonb,
    order_index integer DEFAULT 0
);


--
-- Name: lesson_exercises_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lesson_exercises_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lesson_exercises_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lesson_exercises_id_seq OWNED BY public.lesson_exercises.id;


--
-- Name: london_transport_exercises; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.london_transport_exercises (
    id integer NOT NULL,
    student_record_id integer,
    exercise_id character varying(50),
    completed boolean,
    attempts integer,
    code_submitted text,
    api_response json,
    score double precision,
    completed_at timestamp without time zone,
    created_at timestamp without time zone
);


--
-- Name: london_transport_exercises_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.london_transport_exercises_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: london_transport_exercises_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.london_transport_exercises_id_seq OWNED BY public.london_transport_exercises.id;


--
-- Name: password_reset_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.password_reset_tokens (
    id integer NOT NULL,
    user_id integer NOT NULL,
    token_hash character varying(128) NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    used_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    ip_address character varying(45)
);


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.password_reset_tokens_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: password_reset_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.password_reset_tokens_id_seq OWNED BY public.password_reset_tokens.id;


--
-- Name: quiz_attempts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quiz_attempts (
    id integer NOT NULL,
    student_id character varying(100) NOT NULL,
    question_id character varying(120) NOT NULL,
    template_id character varying(120),
    skill_tag character varying(40) NOT NULL,
    category character varying(20) NOT NULL,
    severity character varying(10),
    chosen_option character varying(4),
    is_correct boolean NOT NULL,
    time_ms integer,
    created_at timestamp without time zone
);


--
-- Name: quiz_attempts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quiz_attempts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quiz_attempts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quiz_attempts_id_seq OWNED BY public.quiz_attempts.id;


--
-- Name: quiz_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.quiz_reviews (
    id integer NOT NULL,
    student_id character varying(100) NOT NULL,
    question_id character varying(120) NOT NULL,
    skill_tag character varying(40) NOT NULL,
    consecutive_correct integer,
    ease double precision,
    interval_days double precision,
    next_due_at timestamp without time zone,
    last_result boolean,
    updated_at timestamp without time zone
);


--
-- Name: quiz_reviews_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.quiz_reviews_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: quiz_reviews_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.quiz_reviews_id_seq OWNED BY public.quiz_reviews.id;


--
-- Name: research_participants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.research_participants (
    id integer NOT NULL,
    participant_code character varying(20) NOT NULL,
    age character varying,
    gender character varying(50),
    study_program character varying(100),
    email character varying(255),
    neurodivergence_type character varying(50),
    neurodivergence_details text,
    programming_experience character varying(50),
    task_elapsed_time integer,
    task_time_remaining integer,
    task_submission_time timestamp without time zone,
    task_completed boolean DEFAULT false,
    consent_given boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now(),
    task_start_time timestamp without time zone,
    task_end_time timestamp without time zone,
    nickname character varying(100),
    group_assignment character varying(1),
    nd_formal_diagnosis character varying(50),
    is_neurodivergent boolean,
    security_experience character varying(50),
    ai_chatbot_experience character varying(50),
    pre_test_answers json,
    pre_test_score integer,
    pre_test_max integer,
    pre_test_bloom_remember integer,
    pre_test_bloom_understand integer,
    pre_test_bloom_apply integer,
    pre_test_bloom_analyse integer,
    vulnerability_findings json,
    vuln_count integer DEFAULT 0,
    vuln_unique_count integer,
    vuln_total_score integer,
    vuln_avg_quality double precision,
    vuln_owasp_categories_found json,
    vuln_scored_by character varying(100),
    vuln_scored_at timestamp without time zone,
    interaction_logs json,
    ai_messages_count integer DEFAULT 0,
    ai_hints_requested integer DEFAULT 0,
    ai_encouragements_sent integer DEFAULT 0,
    ai_idle_triggers json,
    ai_avg_response_time double precision,
    post_test_answers json,
    post_test_score integer,
    post_test_max integer,
    post_test_bloom_remember integer,
    post_test_bloom_understand integer,
    post_test_bloom_apply integer,
    post_test_bloom_analyse integer,
    normalised_gain double precision,
    nasa_mental_demand integer,
    nasa_temporal_demand integer,
    nasa_performance integer,
    nasa_effort integer,
    nasa_frustration integer,
    nasa_tlx_avg double precision,
    sus_q1 integer,
    sus_q2 integer,
    sus_q3 integer,
    sus_q4 integer,
    sus_q5 integer,
    sus_q6 integer,
    sus_q7 integer,
    sus_q8 integer,
    sus_q9 integer,
    sus_q10 integer,
    sus_total double precision,
    perception_q1 integer,
    perception_q2 integer,
    perception_q3 integer,
    perception_q4 integer,
    perception_q5 integer,
    perception_q6 integer,
    perception_q7 integer,
    perception_q8 integer,
    perception_q9 integer,
    perception_q10 integer,
    perception_q11 integer,
    perception_q12 integer,
    perception_avg double precision,
    qual_easiest_vuln text,
    qual_hardest_vuln text,
    qual_strategy text,
    qual_different_next text,
    qual_confidence_rating integer,
    qual_ai_helpfulness integer,
    qual_ai_moment text,
    qual_ai_understand_why text,
    qual_resources_adequate integer,
    qual_stuck_moment text,
    accessibility_dark_mode boolean DEFAULT false,
    accessibility_dyslexia_font boolean DEFAULT false,
    accessibility_tts boolean DEFAULT false,
    accessibility_reading_pointer boolean DEFAULT false,
    chosen_path character varying(20),
    ai_for_learning character varying(50),
    platforms_used character varying(50),
    when_stuck text,
    learning_style text,
    self_confidence_pre integer
);


--
-- Name: research_participants_backup_python_study; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.research_participants_backup_python_study (
    id integer,
    participant_code character varying(20),
    age character varying,
    gender character varying(50),
    study_program character varying(100),
    email character varying(255),
    neurodivergence_type character varying(50),
    neurodivergence_details text,
    python_experience character varying(50),
    programming_experience character varying(50),
    matplotlib_q1 character varying(100),
    matplotlib_q2 character varying(100),
    matplotlib_q3 character varying(100),
    matplotlib_q4 character varying(100),
    matplotlib_q5 character varying(100),
    matplotlib_score integer,
    matplotlib_level character varying(20),
    ai_awareness_1 integer,
    ai_awareness_2 integer,
    ai_awareness_3 integer,
    ai_awareness_total integer,
    ai_usage_1 integer,
    ai_usage_2 integer,
    ai_usage_3 integer,
    ai_usage_total integer,
    ai_evaluation_1 integer,
    ai_evaluation_2 integer,
    ai_evaluation_3 integer,
    ai_evaluation_total integer,
    ai_ethics_1 integer,
    ai_ethics_2 integer,
    ai_ethics_3 integer,
    ai_ethics_total integer,
    ai_literacy_total integer,
    chatgpt_cognitive_1 integer,
    chatgpt_cognitive_2 integer,
    chatgpt_cognitive_3 integer,
    chatgpt_cognitive_total integer,
    usage_intention_pre_1 integer,
    usage_intention_pre_2 integer,
    usage_intention_pre_3 integer,
    usage_intention_pre_avg double precision,
    task_code text,
    task_elapsed_time integer,
    task_time_remaining integer,
    task_submission_time timestamp without time zone,
    task_completed boolean,
    post_test_q1 integer,
    post_test_q2 integer,
    post_test_q3 integer,
    post_test_intention_avg double precision,
    score_coordinates integer,
    score_legends integer,
    score_colors integer,
    score_coherence integer,
    score_numerical integer,
    score_titles integer,
    score_stacking integer,
    score_total integer,
    scored_by character varying(100),
    scored_at timestamp without time zone,
    consent_given boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    python_code text,
    task_start_time timestamp without time zone,
    task_end_time timestamp without time zone,
    task_elapsed_seconds integer,
    task_submission_timestamp timestamp without time zone,
    nickname character varying(100),
    ai_awareness numeric(4,2),
    ai_usage numeric(4,2),
    ai_evaluation numeric(4,2),
    ai_ethics numeric(4,2),
    motivation text
);


--
-- Name: research_participants_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.research_participants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: research_participants_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.research_participants_id_seq OWNED BY public.research_participants.id;


--
-- Name: students; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.students (
    id integer NOT NULL,
    student_id character varying,
    neurodivergent_type character varying,
    created_at timestamp without time zone
);


--
-- Name: students_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.students_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: students_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.students_id_seq OWNED BY public.students.id;


--
-- Name: tfl_api_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tfl_api_requests (
    id integer NOT NULL,
    student_record_id integer,
    request_type character varying(50),
    request_params json,
    response_code integer,
    response_time double precision,
    success boolean,
    error_message text,
    "timestamp" timestamp without time zone
);


--
-- Name: tfl_api_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tfl_api_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tfl_api_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tfl_api_requests_id_seq OWNED BY public.tfl_api_requests.id;


--
-- Name: transport_arrivals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transport_arrivals (
    id integer NOT NULL,
    line_id integer,
    stop_id integer,
    destination character varying(200),
    platform_name character varying(100),
    time_to_station integer,
    expected_arrival timestamp without time zone,
    current_location character varying(200),
    prediction_timestamp timestamp without time zone
);


--
-- Name: transport_arrivals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transport_arrivals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transport_arrivals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transport_arrivals_id_seq OWNED BY public.transport_arrivals.id;


--
-- Name: transport_stops; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transport_stops (
    id integer NOT NULL,
    stop_id character varying(50),
    stop_name character varying(200),
    line_id integer,
    latitude double precision,
    longitude double precision,
    zone character varying(10),
    modes json,
    created_at timestamp without time zone
);


--
-- Name: transport_stops_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transport_stops_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transport_stops_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transport_stops_id_seq OWNED BY public.transport_stops.id;


--
-- Name: tube_lines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tube_lines (
    id integer NOT NULL,
    line_id character varying(50),
    line_name character varying(100),
    mode_name character varying(50),
    created_at timestamp without time zone
);


--
-- Name: tube_lines_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tube_lines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tube_lines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tube_lines_id_seq OWNED BY public.tube_lines.id;


--
-- Name: user_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_progress (
    id integer NOT NULL,
    user_id integer,
    course_id character varying(100) NOT NULL,
    topic_id character varying(100) NOT NULL,
    exercise_id character varying(100),
    completed boolean DEFAULT false,
    score integer DEFAULT 0,
    attempts integer DEFAULT 0,
    completed_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: user_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_progress_id_seq OWNED BY public.user_progress.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) DEFAULT NULL::character varying,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    display_name character varying(100),
    is_neurodivergent boolean DEFAULT false,
    nd_type character varying(50),
    created_at timestamp without time zone DEFAULT now(),
    last_login timestamp without time zone,
    is_active boolean DEFAULT true,
    subscription_tier character varying(20) DEFAULT 'free'::character varying
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: ai_responses id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_responses ALTER COLUMN id SET DEFAULT nextval('public.ai_responses_id_seq'::regclass);


--
-- Name: chat_conversations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_conversations ALTER COLUMN id SET DEFAULT nextval('public.chat_conversations_id_seq'::regclass);


--
-- Name: chat_messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages ALTER COLUMN id SET DEFAULT nextval('public.chat_messages_id_seq'::regclass);


--
-- Name: course_progress id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course_progress ALTER COLUMN id SET DEFAULT nextval('public.course_progress_id_seq'::regclass);


--
-- Name: feedback id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback ALTER COLUMN id SET DEFAULT nextval('public.feedback_id_seq'::regclass);


--
-- Name: lab_sessions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_sessions ALTER COLUMN id SET DEFAULT nextval('public.lab_sessions_id_seq'::regclass);


--
-- Name: learning_sessions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_sessions ALTER COLUMN id SET DEFAULT nextval('public.learning_sessions_id_seq'::regclass);


--
-- Name: lesson_content id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lesson_content ALTER COLUMN id SET DEFAULT nextval('public.lesson_content_id_seq'::regclass);


--
-- Name: lesson_examples id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lesson_examples ALTER COLUMN id SET DEFAULT nextval('public.lesson_examples_id_seq'::regclass);


--
-- Name: lesson_exercises id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lesson_exercises ALTER COLUMN id SET DEFAULT nextval('public.lesson_exercises_id_seq'::regclass);


--
-- Name: london_transport_exercises id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.london_transport_exercises ALTER COLUMN id SET DEFAULT nextval('public.london_transport_exercises_id_seq'::regclass);


--
-- Name: password_reset_tokens id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset_tokens ALTER COLUMN id SET DEFAULT nextval('public.password_reset_tokens_id_seq'::regclass);


--
-- Name: quiz_attempts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_attempts ALTER COLUMN id SET DEFAULT nextval('public.quiz_attempts_id_seq'::regclass);


--
-- Name: quiz_reviews id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_reviews ALTER COLUMN id SET DEFAULT nextval('public.quiz_reviews_id_seq'::regclass);


--
-- Name: research_participants id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.research_participants ALTER COLUMN id SET DEFAULT nextval('public.research_participants_id_seq'::regclass);


--
-- Name: students id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students ALTER COLUMN id SET DEFAULT nextval('public.students_id_seq'::regclass);


--
-- Name: tfl_api_requests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tfl_api_requests ALTER COLUMN id SET DEFAULT nextval('public.tfl_api_requests_id_seq'::regclass);


--
-- Name: transport_arrivals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transport_arrivals ALTER COLUMN id SET DEFAULT nextval('public.transport_arrivals_id_seq'::regclass);


--
-- Name: transport_stops id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transport_stops ALTER COLUMN id SET DEFAULT nextval('public.transport_stops_id_seq'::regclass);


--
-- Name: tube_lines id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tube_lines ALTER COLUMN id SET DEFAULT nextval('public.tube_lines_id_seq'::regclass);


--
-- Name: user_progress id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_progress ALTER COLUMN id SET DEFAULT nextval('public.user_progress_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: ai_responses ai_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_responses
    ADD CONSTRAINT ai_responses_pkey PRIMARY KEY (id);


--
-- Name: chat_conversations chat_conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_conversations
    ADD CONSTRAINT chat_conversations_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: course_progress course_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.course_progress
    ADD CONSTRAINT course_progress_pkey PRIMARY KEY (id);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


--
-- Name: lab_sessions lab_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_sessions
    ADD CONSTRAINT lab_sessions_pkey PRIMARY KEY (id);


--
-- Name: lab_sessions lab_sessions_session_token_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_sessions
    ADD CONSTRAINT lab_sessions_session_token_key UNIQUE (session_token);


--
-- Name: learning_sessions learning_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_sessions
    ADD CONSTRAINT learning_sessions_pkey PRIMARY KEY (id);


--
-- Name: lesson_content lesson_content_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lesson_content
    ADD CONSTRAINT lesson_content_pkey PRIMARY KEY (id);


--
-- Name: lesson_content lesson_content_topic_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lesson_content
    ADD CONSTRAINT lesson_content_topic_id_key UNIQUE (topic_id);


--
-- Name: lesson_examples lesson_examples_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lesson_examples
    ADD CONSTRAINT lesson_examples_pkey PRIMARY KEY (id);


--
-- Name: lesson_exercises lesson_exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lesson_exercises
    ADD CONSTRAINT lesson_exercises_pkey PRIMARY KEY (id);


--
-- Name: london_transport_exercises london_transport_exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.london_transport_exercises
    ADD CONSTRAINT london_transport_exercises_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_pkey PRIMARY KEY (id);


--
-- Name: password_reset_tokens password_reset_tokens_token_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_token_hash_key UNIQUE (token_hash);


--
-- Name: quiz_attempts quiz_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_attempts
    ADD CONSTRAINT quiz_attempts_pkey PRIMARY KEY (id);


--
-- Name: quiz_reviews quiz_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_reviews
    ADD CONSTRAINT quiz_reviews_pkey PRIMARY KEY (id);


--
-- Name: research_participants research_participants_nickname_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.research_participants
    ADD CONSTRAINT research_participants_nickname_key UNIQUE (nickname);


--
-- Name: research_participants research_participants_participant_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.research_participants
    ADD CONSTRAINT research_participants_participant_code_key UNIQUE (participant_code);


--
-- Name: research_participants research_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.research_participants
    ADD CONSTRAINT research_participants_pkey PRIMARY KEY (id);


--
-- Name: students students_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_pkey PRIMARY KEY (id);


--
-- Name: tfl_api_requests tfl_api_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tfl_api_requests
    ADD CONSTRAINT tfl_api_requests_pkey PRIMARY KEY (id);


--
-- Name: transport_arrivals transport_arrivals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transport_arrivals
    ADD CONSTRAINT transport_arrivals_pkey PRIMARY KEY (id);


--
-- Name: transport_stops transport_stops_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transport_stops
    ADD CONSTRAINT transport_stops_pkey PRIMARY KEY (id);


--
-- Name: tube_lines tube_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tube_lines
    ADD CONSTRAINT tube_lines_pkey PRIMARY KEY (id);


--
-- Name: quiz_reviews uq_quiz_review_student_question; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.quiz_reviews
    ADD CONSTRAINT uq_quiz_review_student_question UNIQUE (student_id, question_id);


--
-- Name: user_progress user_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_progress
    ADD CONSTRAINT user_progress_pkey PRIMARY KEY (id);


--
-- Name: user_progress user_progress_user_id_course_id_topic_id_exercise_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_progress
    ADD CONSTRAINT user_progress_user_id_course_id_topic_id_exercise_id_key UNIQUE (user_id, course_id, topic_id, exercise_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_lab_sessions_container; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lab_sessions_container ON public.lab_sessions USING btree (container_id) WHERE ((status)::text <> ALL ((ARRAY['terminated'::character varying, 'expired'::character varying])::text[]));


--
-- Name: idx_lab_sessions_expires_ready; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lab_sessions_expires_ready ON public.lab_sessions USING btree (expires_at) WHERE ((status)::text = ANY ((ARRAY['starting'::character varying, 'ready'::character varying])::text[]));


--
-- Name: idx_lab_sessions_participant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lab_sessions_participant ON public.lab_sessions USING btree (participant_code, status) WHERE (participant_code IS NOT NULL);


--
-- Name: idx_lab_sessions_token; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lab_sessions_token ON public.lab_sessions USING btree (session_token);


--
-- Name: idx_lab_sessions_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_lab_sessions_user ON public.lab_sessions USING btree (user_id, status) WHERE (user_id IS NOT NULL);


--
-- Name: idx_nickname; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nickname ON public.research_participants USING btree (nickname);


--
-- Name: idx_participant_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_participant_code ON public.research_participants USING btree (participant_code);


--
-- Name: idx_prt_token_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prt_token_hash ON public.password_reset_tokens USING btree (token_hash);


--
-- Name: idx_prt_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_prt_user_id ON public.password_reset_tokens USING btree (user_id);


--
-- Name: idx_topic_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_topic_id ON public.lesson_content USING btree (topic_id);


--
-- Name: idx_topic_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_topic_level ON public.lesson_content USING btree (level);


--
-- Name: ix_course_progress_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_course_progress_student_id ON public.course_progress USING btree (student_id);


--
-- Name: ix_course_progress_topic_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_course_progress_topic_id ON public.course_progress USING btree (topic_id);


--
-- Name: ix_feedback_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feedback_id ON public.feedback USING btree (id);


--
-- Name: ix_feedback_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_feedback_user_id ON public.feedback USING btree (user_id);


--
-- Name: ix_quiz_attempts_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_attempts_created_at ON public.quiz_attempts USING btree (created_at);


--
-- Name: ix_quiz_attempts_question_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_attempts_question_id ON public.quiz_attempts USING btree (question_id);


--
-- Name: ix_quiz_attempts_skill_tag; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_attempts_skill_tag ON public.quiz_attempts USING btree (skill_tag);


--
-- Name: ix_quiz_attempts_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_attempts_student_id ON public.quiz_attempts USING btree (student_id);


--
-- Name: ix_quiz_reviews_next_due_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_reviews_next_due_at ON public.quiz_reviews USING btree (next_due_at);


--
-- Name: ix_quiz_reviews_question_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_reviews_question_id ON public.quiz_reviews USING btree (question_id);


--
-- Name: ix_quiz_reviews_skill_tag; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_reviews_skill_tag ON public.quiz_reviews USING btree (skill_tag);


--
-- Name: ix_quiz_reviews_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_quiz_reviews_student_id ON public.quiz_reviews USING btree (student_id);


--
-- Name: ix_students_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_students_id ON public.students USING btree (id);


--
-- Name: ix_students_student_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_students_student_id ON public.students USING btree (student_id);


--
-- Name: ix_transport_stops_stop_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_transport_stops_stop_id ON public.transport_stops USING btree (stop_id);


--
-- Name: ix_tube_lines_line_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_tube_lines_line_id ON public.tube_lines USING btree (line_id);


--
-- Name: ai_responses ai_responses_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ai_responses
    ADD CONSTRAINT ai_responses_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.learning_sessions(id);


--
-- Name: chat_conversations chat_conversations_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_conversations
    ADD CONSTRAINT chat_conversations_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.learning_sessions(id);


--
-- Name: chat_conversations chat_conversations_student_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_conversations
    ADD CONSTRAINT chat_conversations_student_record_id_fkey FOREIGN KEY (student_record_id) REFERENCES public.students(id);


--
-- Name: chat_conversations chat_conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_conversations
    ADD CONSTRAINT chat_conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: chat_messages chat_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.chat_conversations(id);


--
-- Name: feedback feedback_student_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_student_record_id_fkey FOREIGN KEY (student_record_id) REFERENCES public.students(id);


--
-- Name: lab_sessions lab_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lab_sessions
    ADD CONSTRAINT lab_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: learning_sessions learning_sessions_student_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_sessions
    ADD CONSTRAINT learning_sessions_student_record_id_fkey FOREIGN KEY (student_record_id) REFERENCES public.students(id);


--
-- Name: lesson_examples lesson_examples_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lesson_examples
    ADD CONSTRAINT lesson_examples_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.lesson_content(topic_id);


--
-- Name: lesson_exercises lesson_exercises_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lesson_exercises
    ADD CONSTRAINT lesson_exercises_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.lesson_content(topic_id);


--
-- Name: london_transport_exercises london_transport_exercises_student_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.london_transport_exercises
    ADD CONSTRAINT london_transport_exercises_student_record_id_fkey FOREIGN KEY (student_record_id) REFERENCES public.students(id);


--
-- Name: password_reset_tokens password_reset_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.password_reset_tokens
    ADD CONSTRAINT password_reset_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: tfl_api_requests tfl_api_requests_student_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tfl_api_requests
    ADD CONSTRAINT tfl_api_requests_student_record_id_fkey FOREIGN KEY (student_record_id) REFERENCES public.students(id);


--
-- Name: transport_arrivals transport_arrivals_line_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transport_arrivals
    ADD CONSTRAINT transport_arrivals_line_id_fkey FOREIGN KEY (line_id) REFERENCES public.tube_lines(id);


--
-- Name: transport_arrivals transport_arrivals_stop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transport_arrivals
    ADD CONSTRAINT transport_arrivals_stop_id_fkey FOREIGN KEY (stop_id) REFERENCES public.transport_stops(id);


--
-- Name: transport_stops transport_stops_line_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transport_stops
    ADD CONSTRAINT transport_stops_line_id_fkey FOREIGN KEY (line_id) REFERENCES public.tube_lines(id);


--
-- Name: user_progress user_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_progress
    ADD CONSTRAINT user_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict 8AsgUXuvgS6pJAGyRVh6oqx2FDO3t07gkhFvvrTwuzBZaVEDGL7aTr2yzW0tE1g

