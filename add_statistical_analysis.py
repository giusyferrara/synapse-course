"""
Add statistical analysis functions to research_data_parser.py
to replicate Jing et al. (2024) methodology
"""

def add_statistical_functions():
    with open('research_data_parser.py', 'r') as f:
        content = f.read()
    
    # Trova dove inserire le nuove funzioni (dopo gli import)
    import_section = "import statistics"
    
    # Aggiungi import scipy se non c'è
    if "from scipy import stats" not in content:
        content = content.replace(import_section, import_section + "\nfrom scipy import stats")
    
    # Trova la classe ResearchDataParser
    class_position = content.find("class ResearchDataParser:")
    
    # Aggiungi le nuove funzioni PRIMA di calculate_task_effectiveness
    new_methods = '''
    def median_split(self, group, variable_name):
        """
        Split group into Low/High based on median value
        Replicates the methodology from Jing et al. (2024)
        """
        values = []
        valid_participants = []
        
        for p in group:
            val = p.get(variable_name)
            if val is not None and val > 0:
                values.append(val)
                valid_participants.append(p)
        
        if len(values) < 2:
            return {'low': [], 'high': []}
        
        median_value = statistics.median(values)
        
        low_group = [p for p in valid_participants if p.get(variable_name, 0) < median_value]
        high_group = [p for p in valid_participants if p.get(variable_name, 0) >= median_value]
        
        return {
            'low': low_group,
            'high': high_group,
            'median': median_value
        }
    
    def calculate_group_stats(self, group, score_variable='score_total'):
        """Calculate statistics for a group"""
        scores = [p.get(score_variable) for p in group if p.get(score_variable) is not None]
        
        if len(scores) == 0:
            return {'n': 0, 'mean': 0, 'sd': 0}
        
        return {
            'n': len(scores),
            'mean': round(statistics.mean(scores), 3),
            'sd': round(statistics.stdev(scores), 3) if len(scores) > 1 else 0.0,
            'scores': scores
        }
    
    def independent_t_test(self, group1_stats, group2_stats):
        """
        Perform independent samples t-test
        Replicates Table 2, 3, 6, 7 from paper
        """
        if group1_stats['n'] < 2 or group2_stats['n'] < 2:
            return {'t': 'NaN', 'df': 0, 'p': '> 0.05'}
        
        try:
            t_stat, p_value = stats.ttest_ind(
                group1_stats['scores'],
                group2_stats['scores']
            )
            
            df = group1_stats['n'] + group2_stats['n'] - 2
            
            return {
                't': round(t_stat, 3),
                'df': df,
                'p': f"< 0.05" if p_value < 0.05 else f"> 0.05",
                'p_value': round(p_value, 3)
            }
        except:
            return {'t': 'NaN', 'df': 0, 'p': '> 0.05'}
    
    def one_way_anova(self, *groups):
        """
        Perform one-way ANOVA
        Replicates Table 4, 5 from paper
        """
        group_scores = []
        for g in groups:
            scores = [p.get('score_total') for p in g if p.get('score_total') is not None]
            if scores:
                group_scores.append(scores)
        
        if len(group_scores) < 2:
            return {'F': 'NaN', 'p': '> 0.05'}
        
        try:
            f_stat, p_value = stats.f_oneway(*group_scores)
            return {
                'F': round(f_stat, 3),
                'p': f"< 0.05" if p_value < 0.05 else f"> 0.05",
                'p_value': round(p_value, 3)
            }
        except:
            return {'F': 'NaN', 'p': '> 0.05'}
    
    def paired_t_test(self, pre_scores, post_scores):
        """
        Perform paired samples t-test
        Replicates Table 8 from paper
        """
        if len(pre_scores) < 2 or len(post_scores) < 2:
            return {'t': 'NaN', 'df': 0, 'p': '> 0.05'}
        
        try:
            t_stat, p_value = stats.ttest_rel(pre_scores, post_scores)
            df = len(pre_scores) - 1
            
            return {
                't': round(t_stat, 3),
                'df': df,
                'p': f"< 0.05" if p_value < 0.05 else f"> 0.05",
                'p_value': round(p_value, 3)
            }
        except:
            return {'t': 'NaN', 'df': 0, 'p': '> 0.05'}
'''
    
    # Inserisci le nuove funzioni prima di calculate_task_effectiveness
    old_function = "    def calculate_task_effectiveness(self):"
    content = content.replace(old_function, new_methods + "\n" + old_function)
    
    with open('research_data_parser.py', 'w') as f:
        f.write(content)
    
    print("✅ Added statistical analysis functions!")
    print("   - median_split()")
    print("   - calculate_group_stats()")
    print("   - independent_t_test()")
    print("   - one_way_anova()")
    print("   - paired_t_test()")

if __name__ == "__main__":
    add_statistical_functions()
