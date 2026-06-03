"""
Synapse Research Data Parser - PostgreSQL Version (FIXED)
Follows methodology from Wang et al. (2022) / Jing et al. (2024)
Processes participant data for quasi-experimental research design
"""

import statistics
from collections import defaultdict
from datetime import datetime

# Try scipy - graceful fallback if not available
try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("⚠️  scipy not available - t-tests and ANOVA will return N/A")

# Database imports
from database.models import ResearchParticipant
from database.config import SessionLocal


def safe_str(val, default=''):
    """Safely convert to lowercase string, handling None"""
    if val is None:
        return default
    return str(val).lower()


def safe_mean(values):
    """Safe mean that handles empty lists"""
    if not values:
        return 0
    return round(statistics.mean(values), 2)


def safe_stdev(values):
    """Safe stdev that handles lists with < 2 items"""
    if len(values) < 2:
        return 0
    return round(statistics.stdev(values), 2)


class ResearchDataParser:
    def __init__(self):
        self.participants = []
        self.adhd_group = []
        self.neurotypical_group = []
        self.other_group = []

        self.raw_data = {
            'participants': [],
            'sessions': [],
            'groups': {},
            'demographics': {},
            'ai_literacy_analysis': {},
            'post_test_intention': {},
            'task_effectiveness': {},
            'group_comparisons': {},
            'total_stats': {}
        }

    def load_all_data(self):
        """Load all participant data from PostgreSQL"""
        # Reset lists to prevent duplicates
        self.participants = []
        self.adhd_group = []
        self.neurotypical_group = []
        self.other_group = []
        print(f"📊 Loading data from PostgreSQL...")

        db = SessionLocal()
        try:
            # Load participants
            self.load_participants(db)

            # Classify into groups
            self.classify_groups()

            # Calculate analytics
            self.calculate_demographics()
            self.calculate_ai_literacy_analysis()
            self.calculate_post_test_intention()
            self.calculate_task_effectiveness()
            self.calculate_group_comparisons()

            # Load session data from JSONL files
            self.load_sessions()

            print(f"✅ Loaded {len(self.participants)} participants, {len(self.raw_data['sessions'])} sessions")
            print(f"   📊 Groups: ADHD={len(self.adhd_group)}, Neurotypical={len(self.neurotypical_group)}, Other={len(self.other_group)}")

            return self.raw_data

        except Exception as e:
            print(f"❌ Error loading data: {e}")
            import traceback
            traceback.print_exc()
            return self.raw_data

        finally:
            db.close()

    def load_participants(self, db):
        """Load all participants from PostgreSQL"""
        participants_db = db.query(ResearchParticipant).all()

        print(f"📂 Found {len(participants_db)} participants in database")

        for p_db in participants_db:
            participant = {
                'code': p_db.participant_code,
                'age': p_db.age,
                'gender': p_db.gender,
                'study_program': p_db.study_program,
                'email': p_db.email,
                'neurodivergence_type': p_db.neurodivergence_type,
                'neurodivergence_details': p_db.neurodivergence_details,
                'python_experience': p_db.python_experience,
                'programming_experience': p_db.programming_experience,
                'motivation': getattr(p_db, 'motivation', None),

                # Matplotlib
                'matplotlib_score': p_db.matplotlib_score,
                'matplotlib_level': p_db.matplotlib_level,

                # AI Literacy
                'ai_literacy': {
                    'ai_awareness': p_db.ai_awareness_total or 0,
                    'ai_usage': p_db.ai_usage_total or 0,
                    'ai_evaluation': p_db.ai_evaluation_total or 0,
                    'ai_ethics': p_db.ai_ethics_total or 0,
                    'total': p_db.ai_literacy_total or 0
                },

                # ChatGPT Cognitive
                'chatgpt_cognitive_level': p_db.chatgpt_cognitive_total or 0,

                # Usage Intention
                'usage_intention_pre': p_db.usage_intention_pre_avg or 0,
                'usage_intention_post': p_db.post_test_intention_avg,

                # Task Data
                'task_completed': p_db.task_completed or False,
                'task_code': p_db.task_code,
                'task_elapsed_time': p_db.task_elapsed_time,
                'task_time_remaining': p_db.task_time_remaining,

                # Scores
                'score_total': p_db.score_total,
                'score_coordinates': p_db.score_coordinates,
                'score_legends': p_db.score_legends,
                'score_colors': p_db.score_colors,
                'score_coherence': p_db.score_coherence,
                'score_numerical': p_db.score_numerical,
                'score_titles': p_db.score_titles,
                'score_stacking': p_db.score_stacking,

                # Metadata
                'consent': p_db.consent_given,
                'signup_date': p_db.created_at.isoformat() if p_db.created_at else None,
                'group': None  # Will be set in classify_groups()
            }

            self.participants.append(participant)

        self.raw_data['participants'] = self.participants

    def load_sessions(self):
        """Load session data from JSONL files in research_data directory"""
        import json
        from pathlib import Path

        research_dir = Path(__file__).parent / "research_data"
        sessions = []

        if not research_dir.exists():
            print(f"⚠️  No research_data directory found")
            self.raw_data['sessions'] = []
            return

        for jsonl_file in sorted(research_dir.glob("session_*.jsonl")):
            try:
                with open(jsonl_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            session_data = json.loads(line)
                            sessions.append(session_data)
            except Exception as e:
                print(f"⚠️  Error reading {jsonl_file.name}: {e}")

        self.raw_data['sessions'] = sessions
        print(f"📂 Loaded {len(sessions)} session records from {len(list(research_dir.glob('session_*.jsonl')))} files")

    def classify_groups(self):
        """Classify participants into ADHD, Neurotypical, and Other groups"""
        print(f"\n📊 Classifying participants into groups...")

        for participant in self.participants:
            neuro_type = safe_str(participant.get('neurodivergence_type'))

            if 'adhd' in neuro_type:
                self.adhd_group.append(participant)
                participant['group'] = 'ADHD'
            elif 'neurotypical' in neuro_type:
                self.neurotypical_group.append(participant)
                participant['group'] = 'Neurotypical'
            elif not neuro_type:
                # Empty/None = unspecified, treat as neurotypical
                self.neurotypical_group.append(participant)
                participant['group'] = 'Neurotypical'
            else:
                self.other_group.append(participant)
                participant['group'] = 'Other'

        self.raw_data['groups'] = {
            'adhd': self.adhd_group,
            'neurotypical': self.neurotypical_group,
            'other': self.other_group
        }

        print(f"   ✓ ADHD: {len(self.adhd_group)} participants")
        print(f"   ✓ Neurotypical: {len(self.neurotypical_group)} participants")
        print(f"   ✓ Other: {len(self.other_group)} participants")

    def calculate_demographics(self):
        """Calculate demographic statistics - Table 1 in paper"""
        print(f"\n📊 Calculating demographics (Table 1)...")

        demographics = {
            'total_participants': len(self.participants),
            'adhd_count': len(self.adhd_group),
            'neurotypical_count': len(self.neurotypical_group),
            'other_count': len(self.other_group),
            'gender_distribution': self._calc_gender_distribution(),
            'age_distribution': self._calc_age_distribution(),
            'study_programs': self._calc_study_programs(),
            'python_experience': self._calc_python_experience(),
            'programming_experience': self._calc_programming_experience()
        }

        self.raw_data['demographics'] = demographics
        print(f"   ✓ Demographics calculated")

    def _calc_gender_distribution(self):
        """Gender distribution by group - None safe"""
        def count_gender(group):
            male = sum(1 for p in group if safe_str(p.get('gender')) == 'male')
            female = sum(1 for p in group if safe_str(p.get('gender')) == 'female')
            other = len(group) - male - female
            return {'male': male, 'female': female, 'other': other}

        return {
            'all': count_gender(self.participants),
            'adhd': count_gender(self.adhd_group),
            'neurotypical': count_gender(self.neurotypical_group),
            'other_group': count_gender(self.other_group)
        }

    def _calc_age_distribution(self):
        """Age distribution by group"""
        def age_stats(group):
            ages = []
            for p in group:
                try:
                    age = int(p.get('age', 0))
                    if age > 0:
                        ages.append(age)
                except (ValueError, TypeError):
                    continue
            if not ages:
                return {'mean': 0, 'min': 0, 'max': 0, 'count': 0}
            return {
                'mean': round(statistics.mean(ages), 1),
                'min': min(ages),
                'max': max(ages),
                'count': len(ages)
            }

        return {
            'all': age_stats(self.participants),
            'adhd': age_stats(self.adhd_group),
            'neurotypical': age_stats(self.neurotypical_group),
            'other_group': age_stats(self.other_group)
        }

    def _calc_study_programs(self):
        """Distribution of study programs"""
        programs = defaultdict(int)
        for p in self.participants:
            program = p.get('study_program') or 'Not specified'
            programs[program] += 1
        return dict(programs)

    def _calc_python_experience(self):
        """Python experience distribution by group"""
        def exp_distribution(group):
            dist = {'none': 0, 'beginner': 0, 'intermediate': 0, 'advanced': 0}
            for p in group:
                exp = safe_str(p.get('python_experience'), 'none')
                if exp in dist:
                    dist[exp] += 1
                else:
                    dist['none'] += 1
            return dist

        return {
            'all': exp_distribution(self.participants),
            'adhd': exp_distribution(self.adhd_group),
            'neurotypical': exp_distribution(self.neurotypical_group),
            'other_group': exp_distribution(self.other_group)
        }

    def _calc_programming_experience(self):
        """Overall programming experience distribution"""
        def exp_distribution(group):
            dist = {'none': 0, 'some': 0, 'moderate': 0, 'extensive': 0}
            for p in group:
                exp = safe_str(p.get('programming_experience'), 'none')
                if exp in dist:
                    dist[exp] += 1
                else:
                    dist['none'] += 1
            return dist

        return {
            'all': exp_distribution(self.participants),
            'adhd': exp_distribution(self.adhd_group),
            'neurotypical': exp_distribution(self.neurotypical_group),
            'other_group': exp_distribution(self.other_group)
        }

    def calculate_ai_literacy_analysis(self):
        """Calculate AI Literacy scores - Tables 2-3 in paper"""
        print(f"\n📊 Calculating AI Literacy analysis (Tables 2-3)...")

        def ai_literacy_stats(group):
            if not group:
                return {
                    'ai_awareness': {'mean': 0, 'sd': 0, 'min': 0, 'max': 0},
                    'ai_usage': {'mean': 0, 'sd': 0, 'min': 0, 'max': 0},
                    'ai_evaluation': {'mean': 0, 'sd': 0, 'min': 0, 'max': 0},
                    'ai_ethics': {'mean': 0, 'sd': 0, 'min': 0, 'max': 0},
                    'total': {'mean': 0, 'sd': 0, 'min': 0, 'max': 0},
                    'chatgpt_cognitive': {'mean': 0, 'sd': 0},
                    'usage_intention_pre': {'mean': 0, 'sd': 0}
                }

            dimensions = ['ai_awareness', 'ai_usage', 'ai_evaluation', 'ai_ethics', 'total']
            result = {}

            for dim in dimensions:
                values = [p['ai_literacy'].get(dim, 0) for p in group]
                values = [v for v in values if v is not None]
                result[dim] = {
                    'mean': safe_mean(values),
                    'sd': safe_stdev(values),
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0
                }

            # ChatGPT Cognitive (Table 6)
            chatgpt_vals = [p.get('chatgpt_cognitive_level', 0) or 0 for p in group]
            result['chatgpt_cognitive'] = {
                'mean': safe_mean(chatgpt_vals),
                'sd': safe_stdev(chatgpt_vals)
            }

            # Usage Intention Pre (Table 7)
            intention_vals = [p.get('usage_intention_pre', 0) or 0 for p in group]
            result['usage_intention_pre'] = {
                'mean': safe_mean(intention_vals),
                'sd': safe_stdev(intention_vals)
            }

            return result

        ai_literacy = {
            'all': ai_literacy_stats(self.participants),
            'adhd': ai_literacy_stats(self.adhd_group),
            'neurotypical': ai_literacy_stats(self.neurotypical_group),
            'other_group': ai_literacy_stats(self.other_group)
        }

        self.raw_data['ai_literacy_analysis'] = ai_literacy
        print(f"   ✓ AI Literacy analysis calculated")

    def calculate_post_test_intention(self):
        """Calculate Post-Test Usage Intention - Table 8 in Wang et al. (2022)"""
        print(f"\n📊 Calculating Post-Test Intention (Table 8)...")

        def intention_stats(group):
            completed = [p for p in group if p.get('task_completed') and p.get('usage_intention_post') is not None]

            if not completed:
                return {'n': 0, 'pre_mean': 0, 'pre_sd': 0, 'post_mean': 0, 'post_sd': 0, 'change': 0}

            pre_vals = [p.get('usage_intention_pre', 0) or 0 for p in completed]
            post_vals = [p.get('usage_intention_post', 0) or 0 for p in completed]

            pre_mean = safe_mean(pre_vals)
            post_mean = safe_mean(post_vals)

            return {
                'n': len(completed),
                'pre_mean': pre_mean,
                'pre_sd': safe_stdev(pre_vals),
                'post_mean': post_mean,
                'post_sd': safe_stdev(post_vals),
                'change': round(post_mean - pre_mean, 2)
            }

        post_test = {
            'all': intention_stats(self.participants),
            'adhd': intention_stats(self.adhd_group),
            'neurotypical': intention_stats(self.neurotypical_group)
        }

        self.raw_data['post_test_intention'] = post_test
        print(f"   ✓ Post-test intention calculated")

    def _get_participant_value(self, participant, variable_name):
        """Get a value from participant, handling nested ai_literacy fields"""
        if variable_name == 'ai_literacy_total':
            return participant.get('ai_literacy', {}).get('total')
        elif variable_name in ('ai_awareness', 'ai_usage', 'ai_evaluation', 'ai_ethics'):
            return participant.get('ai_literacy', {}).get(variable_name)
        else:
            return participant.get(variable_name)

    def median_split(self, group, variable_name):
        """Split group into Low/High based on median value (Jing et al. 2024)"""
        values = []
        valid_participants = []
        for p in group:
            val = self._get_participant_value(p, variable_name)
            if val is not None and isinstance(val, (int, float)) and val > 0:
                values.append(val)
                valid_participants.append(p)
        if len(values) < 2:
            return {'low': [], 'high': [], 'median': 0}
        median_value = statistics.median(values)
        low_group = [p for p, v in zip(valid_participants, values) if v < median_value]
        high_group = [p for p, v in zip(valid_participants, values) if v >= median_value]
        return {
            'low': low_group,
            'high': high_group,
            'median': median_value
        }

    def calculate_group_stats(self, group, score_variable='score_total'):
        """Calculate statistics for a group"""
        scores = [p.get(score_variable) for p in group if p.get(score_variable) is not None]

        if len(scores) == 0:
            return {'n': 0, 'mean': 0, 'sd': 0, 'scores': []}

        return {
            'n': len(scores),
            'mean': safe_mean(scores),
            'sd': safe_stdev(scores),
            'scores': scores
        }

    def independent_t_test(self, group1_stats, group2_stats):
        """Perform independent samples t-test (Tables 2, 3, 6, 7)"""
        if not HAS_SCIPY or group1_stats['n'] < 2 or group2_stats['n'] < 2:
            return {'t': 'N/A', 'df': 0, 'p': 'N/A', 'p_value': None}

        try:
            t_stat, p_value = scipy_stats.ttest_ind(
                group1_stats['scores'],
                group2_stats['scores']
            )
            df = group1_stats['n'] + group2_stats['n'] - 2
            return {
                't': round(t_stat, 3),
                'df': df,
                'p': "< 0.05" if p_value < 0.05 else "> 0.05",
                'p_value': round(p_value, 3)
            }
        except Exception:
            return {'t': 'N/A', 'df': 0, 'p': 'N/A', 'p_value': None}

    def one_way_anova(self, *groups):
        """Perform one-way ANOVA (Tables 4, 5)"""
        if not HAS_SCIPY:
            return {'F': 'N/A', 'p': 'N/A', 'p_value': None}

        group_scores = []
        for g in groups:
            scores = [p.get('score_total') for p in g if p.get('score_total') is not None]
            if scores:
                group_scores.append(scores)

        if len(group_scores) < 2:
            return {'F': 'N/A', 'p': 'N/A', 'p_value': None}

        try:
            f_stat, p_value = scipy_stats.f_oneway(*group_scores)
            if f_stat == float('inf') or f_stat != f_stat:
                return {'F': 'N/A', 'p': 'N/A', 'p_value': None}
            return {
                'F': round(f_stat, 3),
                'p': "< 0.05" if p_value < 0.05 else "> 0.05",
                'p_value': round(p_value, 3)
            }
        except Exception:
            return {'F': 'N/A', 'p': 'N/A', 'p_value': None}

    def paired_t_test(self, pre_scores, post_scores):
        """Perform paired samples t-test (Table 8)"""
        if not HAS_SCIPY or len(pre_scores) < 2 or len(post_scores) < 2:
            return {'t': 'N/A', 'df': 0, 'p': 'N/A', 'p_value': None}

        # Ensure equal lengths
        min_len = min(len(pre_scores), len(post_scores))
        pre_scores = pre_scores[:min_len]
        post_scores = post_scores[:min_len]

        try:
            t_stat, p_value = scipy_stats.ttest_rel(pre_scores, post_scores)
            df = len(pre_scores) - 1
            return {
                't': round(t_stat, 3),
                'df': df,
                'p': "< 0.05" if p_value < 0.05 else "> 0.05",
                'p_value': round(p_value, 3)
            }
        except Exception:
            return {'t': 'N/A', 'df': 0, 'p': 'N/A', 'p_value': None}

    def calculate_task_effectiveness(self):
        """Calculate Task Effectiveness following Jing et al. (2024) methodology"""
        print(f"\n📊 Calculating Task Effectiveness (Jing et al. 2024 replication)...")

        # TABLE 2: AI Literacy Impact on Task Effectiveness
        print(f"   📋 Table 2: AI Literacy Impact...")
        ai_split = self.median_split(self.participants, 'ai_literacy_total')
        low_ai_stats = self.calculate_group_stats(ai_split['low'])
        high_ai_stats = self.calculate_group_stats(ai_split['high'])
        ai_ttest = self.independent_t_test(low_ai_stats, high_ai_stats)

        # TABLE 3: AI Literacy Dimensions Impact
        print(f"   📋 Table 3: AI Literacy Dimensions...")
        dimensions = ['ai_awareness', 'ai_usage', 'ai_evaluation', 'ai_ethics']
        dim_results = {}
        for dim in dimensions:
            split = self.median_split(self.participants, dim)
            low_stats = self.calculate_group_stats(split['low'])
            high_stats = self.calculate_group_stats(split['high'])
            ttest = self.independent_t_test(low_stats, high_stats)
            dim_results[dim] = {
                'low': low_stats,
                'high': high_stats,
                'statistics': ttest
            }

        # TABLE 4: Python Knowledge Base Impact
        print(f"   📋 Table 4: Python Knowledge Impact...")
        group_a = [p for p in self.participants if safe_str(p.get('python_experience')) == 'beginner']
        group_b = [p for p in self.participants if safe_str(p.get('python_experience')) in ('intermediate', 'advanced')]
        group_c = [p for p in self.participants if safe_str(p.get('python_experience')) in ('none', '')]

        python_stats = {
            'group_a': self.calculate_group_stats(group_a),
            'group_b': self.calculate_group_stats(group_b),
            'group_c': self.calculate_group_stats(group_c),
            'anova': self.one_way_anova(group_a, group_b, group_c)
        }

        # TABLE 5: Matplotlib Knowledge Impact
        print(f"   📋 Table 5: Matplotlib Knowledge...")
        no_matplotlib = [p for p in self.participants if (p.get('matplotlib_score') or 0) <= 2]
        weak_matplotlib = [p for p in self.participants if 3 <= (p.get('matplotlib_score') or 0) <= 4]
        good_matplotlib = [p for p in self.participants if (p.get('matplotlib_score') or 0) == 5]

        matplotlib_stats = {
            'no_contact': self.calculate_group_stats(no_matplotlib),
            'weak': self.calculate_group_stats(weak_matplotlib),
            'good': self.calculate_group_stats(good_matplotlib),
            'anova': self.one_way_anova(no_matplotlib, weak_matplotlib, good_matplotlib)
        }

        # TABLE 6: ChatGPT Cognitive Level Impact
        print(f"   📋 Table 6: Cognitive Level...")
        cog_split = self.median_split(self.participants, 'chatgpt_cognitive_level')
        low_cog_stats = self.calculate_group_stats(cog_split['low'])
        high_cog_stats = self.calculate_group_stats(cog_split['high'])
        cog_ttest = self.independent_t_test(low_cog_stats, high_cog_stats)

        # TABLE 7: Usage Intention Impact
        print(f"   📋 Table 7: Usage Intention...")
        intent_split = self.median_split(self.participants, 'usage_intention_pre')
        low_intent_stats = self.calculate_group_stats(intent_split['low'])
        high_intent_stats = self.calculate_group_stats(intent_split['high'])
        intent_ttest = self.independent_t_test(low_intent_stats, high_intent_stats)

        # TABLE 8: Pre vs Post Usage Intention
        print(f"   📋 Table 8: Pre vs Post Intention...")
        completed = [p for p in self.participants
                     if p.get('task_completed') and p.get('usage_intention_post') is not None]
        pre_scores = [p.get('usage_intention_pre', 0) or 0 for p in completed]
        post_scores = [p.get('usage_intention_post', 0) or 0 for p in completed]
        intention_paired = self.paired_t_test(pre_scores, post_scores)

        # Store all results
        self.raw_data['task_effectiveness'] = {
            'table_2_ai_literacy': {
                'low': {k: v for k, v in low_ai_stats.items() if k != 'scores'},
                'high': {k: v for k, v in high_ai_stats.items() if k != 'scores'},
                'statistics': ai_ttest
            },
            'table_3_dimensions': {
                dim: {
                    'low': {k: v for k, v in r['low'].items() if k != 'scores'},
                    'high': {k: v for k, v in r['high'].items() if k != 'scores'},
                    'statistics': r['statistics']
                } for dim, r in dim_results.items()
            },
            'table_4_python': {
                'group_a': {k: v for k, v in python_stats['group_a'].items() if k != 'scores'},
                'group_b': {k: v for k, v in python_stats['group_b'].items() if k != 'scores'},
                'group_c': {k: v for k, v in python_stats['group_c'].items() if k != 'scores'},
                'anova': python_stats['anova']
            },
            'table_5_matplotlib': {
                'no_contact': {k: v for k, v in matplotlib_stats['no_contact'].items() if k != 'scores'},
                'weak': {k: v for k, v in matplotlib_stats['weak'].items() if k != 'scores'},
                'good': {k: v for k, v in matplotlib_stats['good'].items() if k != 'scores'},
                'anova': matplotlib_stats['anova']
            },
            'table_6_cognitive': {
                'low': {k: v for k, v in low_cog_stats.items() if k != 'scores'},
                'high': {k: v for k, v in high_cog_stats.items() if k != 'scores'},
                'statistics': cog_ttest
            },
            'table_7_intention': {
                'low': {k: v for k, v in low_intent_stats.items() if k != 'scores'},
                'high': {k: v for k, v in high_intent_stats.items() if k != 'scores'},
                'statistics': intent_ttest
            },
            'table_8_pre_post': {
                'pre': {'mean': safe_mean(pre_scores), 'sd': safe_stdev(pre_scores), 'n': len(pre_scores)},
                'post': {'mean': safe_mean(post_scores), 'sd': safe_stdev(post_scores), 'n': len(post_scores)},
                'statistics': intention_paired
            }
        }

        print(f"   ✅ All tables calculated (Jing et al. 2024 replication complete)")

    def calculate_group_comparisons(self):
        """Calculate group comparisons for statistical analysis"""
        print(f"\n📊 Calculating group comparisons...")

        comparisons = {
            'adhd_vs_neurotypical': self._compare_two_groups(self.adhd_group, self.neurotypical_group),
            'sample_sizes': {
                'adhd': len(self.adhd_group),
                'neurotypical': len(self.neurotypical_group),
                'other': len(self.other_group)
            }
        }

        self.raw_data['group_comparisons'] = comparisons
        print(f"   ✓ Group comparisons calculated")

    def _compare_two_groups(self, group1, group2):
        """Compare two groups on key variables"""
        if not group1 or not group2:
            return {}

        g1_ai = [p['ai_literacy']['total'] for p in group1]
        g2_ai = [p['ai_literacy']['total'] for p in group2]

        comparison = {
            'ai_literacy_total': {
                'group1_mean': safe_mean(g1_ai),
                'group2_mean': safe_mean(g2_ai),
                'difference': round(safe_mean(g1_ai) - safe_mean(g2_ai), 2)
            },
            'python_experience_score': {
                'group1_mean': self._python_exp_to_score(group1),
                'group2_mean': self._python_exp_to_score(group2),
                'difference': round(self._python_exp_to_score(group1) - self._python_exp_to_score(group2), 2)
            },
            'task_scores': {
                'group1': self.calculate_group_stats(group1),
                'group2': self.calculate_group_stats(group2)
            }
        }

        # Remove raw scores from JSON output
        for key in ('group1', 'group2'):
            if 'scores' in comparison['task_scores'].get(key, {}):
                del comparison['task_scores'][key]['scores']

        return comparison

    def _python_exp_to_score(self, group):
        """Convert Python experience to numeric score"""
        exp_scores = {'none': 0, 'beginner': 1, 'intermediate': 2, 'advanced': 3}
        scores = [exp_scores.get(safe_str(p.get('python_experience'), 'none'), 0) for p in group]
        return safe_mean(scores)

    def export_to_csv(self, output_file='research_export.csv'):
        """Export data to CSV for SPSS/R/Excel"""
        import csv

        print(f"\n📊 Exporting to CSV: {output_file}")

        rows = []
        for participant in self.participants:
            row = {
                'participant_code': participant['code'],
                'group': participant.get('group', 'Unknown'),
                'age': participant.get('age', ''),
                'gender': participant.get('gender', ''),
                'study_program': participant.get('study_program', ''),
                'neurodivergence_type': participant.get('neurodivergence_type', ''),
                'python_experience': participant.get('python_experience', ''),
                'programming_experience': participant.get('programming_experience', ''),
                'matplotlib_score': participant.get('matplotlib_score', ''),
                'matplotlib_level': participant.get('matplotlib_level', ''),
                'ai_awareness': participant['ai_literacy'].get('ai_awareness', 0),
                'ai_usage': participant['ai_literacy'].get('ai_usage', 0),
                'ai_evaluation': participant['ai_literacy'].get('ai_evaluation', 0),
                'ai_ethics': participant['ai_literacy'].get('ai_ethics', 0),
                'ai_literacy_total': participant['ai_literacy'].get('total', 0),
                'chatgpt_cognitive_level': participant.get('chatgpt_cognitive_level', 0),
                'usage_intention_pre': participant.get('usage_intention_pre', 0),
                'usage_intention_post': participant.get('usage_intention_post', ''),
                'task_completed': participant.get('task_completed', False),
                'task_elapsed_time': participant.get('task_elapsed_time', ''),
                'score_total': participant.get('score_total', ''),
                'score_coordinates': participant.get('score_coordinates', ''),
                'score_legends': participant.get('score_legends', ''),
                'score_colors': participant.get('score_colors', ''),
                'score_coherence': participant.get('score_coherence', ''),
                'score_numerical': participant.get('score_numerical', ''),
                'score_titles': participant.get('score_titles', ''),
                'score_stacking': participant.get('score_stacking', ''),
                'signup_date': participant.get('signup_date', '')
            }
            rows.append(row)

        if rows:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            print(f"✅ Exported {len(rows)} participants to {output_file}")
        else:
            print("⚠️  No data to export")

        return output_file


# Test the parser
if __name__ == '__main__':
    parser = ResearchDataParser()
    data = parser.load_all_data()

    print("\n" + "=" * 80)
    print("📊 SYNAPSE RESEARCH DATA SUMMARY (PostgreSQL)")
    print("=" * 80)

    print(f"\n👥 PARTICIPANTS: {data['demographics']['total_participants']}")
    print(f"   • ADHD: {data['demographics']['adhd_count']}")
    print(f"   • Neurotypical: {data['demographics']['neurotypical_count']}")
    print(f"   • Other: {data['demographics']['other_count']}")

    if data['demographics']['total_participants'] > 0:
        print(f"\n🧠 AI LITERACY (All Participants):")
        ai_lit = data['ai_literacy_analysis']['all']
        print(f"   • AI Awareness: {ai_lit['ai_awareness']['mean']:.2f} (SD={ai_lit['ai_awareness']['sd']:.2f})")
        print(f"   • AI Usage: {ai_lit['ai_usage']['mean']:.2f} (SD={ai_lit['ai_usage']['sd']:.2f})")
        print(f"   • AI Evaluation: {ai_lit['ai_evaluation']['mean']:.2f} (SD={ai_lit['ai_evaluation']['sd']:.2f})")
        print(f"   • AI Ethics: {ai_lit['ai_ethics']['mean']:.2f} (SD={ai_lit['ai_ethics']['sd']:.2f})")
        print(f"   • Total: {ai_lit['total']['mean']:.2f} (SD={ai_lit['total']['sd']:.2f})")

        print(f"\n📊 USAGE INTENTION (Wang et al. 2022 - Table 8):")
        intention = data['post_test_intention']['all']
        if intention['n'] > 0:
            print(f"   • Pre-test: {intention['pre_mean']:.2f} (SD={intention['pre_sd']:.2f})")
            print(f"   • Post-test: {intention['post_mean']:.2f} (SD={intention['post_sd']:.2f})")
            print(f"   • Change: {intention['change']:+.2f}")
        else:
            print(f"   ⏳ No completed tasks with post-test data yet")

        csv_file = parser.export_to_csv()
        print(f"\n✅ CSV export complete: {csv_file}")
    else:
        print("\n⚠️  No participants found in database.")

    print("=" * 80)
