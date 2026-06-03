"""
Replace calculate_task_effectiveness with full paper replication
"""

new_calculate = '''
    def calculate_task_effectiveness(self):
        """
        Calculate Task Effectiveness following Jing et al. (2024) methodology
        Replicates Tables 2-8 from the paper
        """
        print(f"\\n📊 Calculating Task Effectiveness (Jing et al. 2024 replication)...")
        
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
        # Group by python_experience
        group_a = [p for p in self.participants if p.get('python_experience') == 'beginner']
        group_b = [p for p in self.participants if p.get('python_experience') in ['intermediate', 'advanced']]
        group_c = [p for p in self.participants if p.get('python_experience') == 'none']
        
        python_stats = {
            'group_a': self.calculate_group_stats(group_a),
            'group_b': self.calculate_group_stats(group_b),
            'group_c': self.calculate_group_stats(group_c),
            'anova': self.one_way_anova(group_a, group_b, group_c)
        }
        
        # TABLE 5: Matplotlib Knowledge Impact
        print(f"   📋 Table 5: Matplotlib Knowledge...")
        no_matplotlib = [p for p in self.participants if p.get('matplotlib_score', 0) <= 2]
        weak_matplotlib = [p for p in self.participants if 3 <= p.get('matplotlib_score', 0) <= 4]
        good_matplotlib = [p for p in self.participants if p.get('matplotlib_score', 0) == 5]
        
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
        pre_scores = [p.get('usage_intention_pre') for p in self.participants if p.get('usage_intention_pre') is not None]
        post_scores = [p.get('usage_intention_post') for p in self.participants if p.get('usage_intention_post') is not None]
        intention_paired = self.paired_t_test(pre_scores, post_scores)
        
        # Store all results
        self.raw_data['task_effectiveness'] = {
            'table_2_ai_literacy': {
                'low': low_ai_stats,
                'high': high_ai_stats,
                'statistics': ai_ttest
            },
            'table_3_dimensions': dim_results,
            'table_4_python': python_stats,
            'table_5_matplotlib': matplotlib_stats,
            'table_6_cognitive': {
                'low': low_cog_stats,
                'high': high_cog_stats,
                'statistics': cog_ttest
            },
            'table_7_intention': {
                'low': low_intent_stats,
                'high': high_intent_stats,
                'statistics': intent_ttest
            },
            'table_8_pre_post': {
                'pre': {'mean': round(statistics.mean(pre_scores), 3), 'sd': round(statistics.stdev(pre_scores), 3), 'n': len(pre_scores)},
                'post': {'mean': round(statistics.mean(post_scores), 3), 'sd': round(statistics.stdev(post_scores), 3), 'n': len(post_scores)},
                'statistics': intention_paired
            }
        }
        
        print(f"   ✅ All tables calculated (Jing et al. 2024 replication complete)")
'''

with open('research_data_parser.py', 'r') as f:
    content = f.read()

# Find and replace the old calculate_task_effectiveness
import re
old_pattern = r'    def calculate_task_effectiveness\(self\):.*?(?=\n    def |\nclass |\Z)'
content = re.sub(old_pattern, new_calculate, content, flags=re.DOTALL)

with open('research_data_parser.py', 'w') as f:
    f.write(content)

print("✅ Replaced calculate_task_effectiveness with full paper replication!")
