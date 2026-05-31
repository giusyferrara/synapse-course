"""
Automatic Code Scoring System for Matplotlib Stacked Bar Charts
Based on Jing et al. (2024) methodology
Replicates the 7-category, 20-criteria scoring rubric
"""
import re
import ast

class MatplotlibScorer:
    """
    Score matplotlib stacked bar chart code
    7 categories, 100 points total
    """
    
    def __init__(self):
        self.max_scores = {
            'coordinates': 15,
            'legends': 15,
            'colors': 10,
            'coherence': 15,
            'numerical': 15,
            'titles': 15,
            'stacking': 15
        }
    
    def score_code(self, python_code):
        """
        Main scoring function
        Returns dict with all category scores and total
        """
        if not python_code or len(python_code) < 20:
            return {
                'coordinates': 0,
                'legends': 0,
                'colors': 0,
                'coherence': 0,
                'numerical': 0,
                'titles': 0,
                'stacking': 0,
                'total': 0
            }
        
        scores = {}
        code_lower = python_code.lower()
        
        try:
            # Score each category
            scores['coordinates'] = self._score_coordinates(code_lower)
            scores['legends'] = self._score_legends(code_lower)
            scores['colors'] = self._score_colors(code_lower)
            scores['coherence'] = self._score_coherence(code_lower, python_code)
            scores['numerical'] = self._score_numerical(python_code)
            scores['titles'] = self._score_titles(code_lower)
            scores['stacking'] = self._score_stacking(code_lower)
            
            # Calculate total
            scores['total'] = sum([v for k, v in scores.items()])
            
        except Exception as e:
            print(f"❌ Scoring error: {e}")
            scores = {k: 0 for k in self.max_scores.keys()}
            scores['total'] = 0
        
        return scores
    
    def _score_coordinates(self, code):
        """
        COORDINATES (15 points - 3 criteria × 5 points)
        Criterion 1: X-axis shows days (Mon-Fri)
        Criterion 2: Y-axis appropriate scale (0-15)
        Criterion 3: Tick labels correct
        """
        score = 0
        
        # Criterion 1: Days of week present (5 pts)
        days = ['mon', 'tue', 'wed', 'thu', 'fri']
        days_found = sum(1 for day in days if day in code)
        if days_found >= 4:
            score += 5
        elif days_found >= 2:
            score += 3
        
        # Criterion 2: Y-axis scale (5 pts)
        if 'ylim' in code or 'set_ylim' in code:
            score += 5
        elif any(f'range({i}' in code or f'range( {i}' in code for i in [10, 12, 15, 20]):
            score += 3
        
        # Criterion 3: Has axis data (5 pts)
        if re.search(r'\[\s*["\']?[a-z]+["\']?\s*,', code):
            score += 5
        
        return min(score, self.max_scores['coordinates'])
    
    def _score_legends(self, code):
        """
        LEGENDS (15 points - 3 criteria × 5 points)
        Criterion 1: Legend present
        Criterion 2: Legend labels correct (Dorm 301-305)
        Criterion 3: Legend positioning
        """
        score = 0
        
        # Criterion 1: Legend exists (5 pts)
        if 'legend' in code:
            score += 5
        
        # Criterion 2: Dorm labels (5 pts)
        dorms = ['301', '302', '303', '304', '305']
        dorms_found = sum(1 for d in dorms if d in code)
        if dorms_found >= 5:
            score += 5
        elif dorms_found >= 3:
            score += 3
        
        # Criterion 3: Legend config (5 pts)
        if 'legend' in code:
            if 'loc=' in code or 'bbox_to_anchor' in code:
                score += 5
            else:
                score += 3
        
        return min(score, self.max_scores['legends'])
    
    def _score_colors(self, code):
        """
        COLORS (10 points - 2 criteria × 5 points)
        Criterion 1: Multiple distinct colors
        Criterion 2: Appropriate color palette
        """
        score = 0
        
        # Criterion 1: Has colors defined (5 pts)
        color_indicators = ['color=', 'colors=', 'c=', '#', 'rgb']
        if any(ind in code for ind in color_indicators):
            score += 5
        
        # Criterion 2: Good color choices (5 pts)
        good_colors = ['red', 'blue', 'green', 'orange', 'purple', 
                       'yellow', 'cyan', 'magenta', 'tab10', 'viridis', 
                       'plasma', 'cmap']
        if sum(1 for c in good_colors if c in code) >= 2:
            score += 5
        elif any(c in code for c in good_colors):
            score += 3
        
        return min(score, self.max_scores['colors'])
    
    def _score_coherence(self, code_lower, code_original):
        """
        COHERENCE (15 points - 3 criteria × 5 points)
        Criterion 1: Represents required data
        Criterion 2: Professional layout
        Criterion 3: No visual errors
        """
        score = 0
        
        # Criterion 1: Bar chart + relevant data (5 pts)
        if 'bar' in code_lower and ('dorm' in code_lower or '301' in code_lower):
            score += 5
        elif 'bar' in code_lower:
            score += 3
        
        # Criterion 2: Layout quality (5 pts)
        layout_features = ['tight_layout', 'figsize', 'subplots_adjust', 'figure(']
        if any(feat in code_lower for feat in layout_features):
            score += 5
        elif 'show()' in code_lower or 'savefig' in code_lower:
            score += 3
        
        # Criterion 3: Code quality (5 pts)
        if len(code_original) > 150:  # Substantial effort
            score += 5
        elif len(code_original) > 80:
            score += 3
        
        return min(score, self.max_scores['coherence'])
    
    def _score_numerical(self, code):
        """
        NUMERICAL (15 points - 3 criteria × 5 points)
        Criterion 1: Correct data values
        Criterion 2: Accurate bar heights
        Criterion 3: Correct totals
        """
        score = 0
        
        # Extract all arrays/lists from code
        arrays = re.findall(r'\[\s*[\d,\s]+\]', code)
        
        # Criterion 1: Has data arrays (5 pts)
        if len(arrays) >= 5:
            score += 5
        elif len(arrays) >= 3:
            score += 3
        
        # Criterion 2: Expected numbers present (5 pts)
        expected = ['0', '1', '2', '3', '4']
        numbers = re.findall(r'\b[0-4]\b', code)
        if len(numbers) >= 15:  # Multiple data points
            score += 5
        elif len(numbers) >= 8:
            score += 3
        
        # Criterion 3: Calculations present (5 pts)
        if 'sum(' in code or 'np.sum' in code or '+' in code:
            score += 5
        elif len(arrays) >= 2:
            score += 3
        
        return min(score, self.max_scores['numerical'])
    
    def _score_titles(self, code):
        """
        TITLES (15 points - 3 criteria × 5 points)
        Criterion 1: Chart title
        Criterion 2: X-axis label
        Criterion 3: Y-axis label
        """
        score = 0
        
        # Criterion 1: Main title (5 pts)
        if 'title(' in code or 'set_title' in code:
            score += 5
        
        # Criterion 2: X-axis label (5 pts)
        if 'xlabel(' in code or 'set_xlabel' in code:
            score += 5
        
        # Criterion 3: Y-axis label (5 pts)
        if 'ylabel(' in code or 'set_ylabel' in code:
            score += 5
        
        return min(score, self.max_scores['titles'])
    
    def _score_stacking(self, code):
        """
        STACKING (15 points - 3 criteria × 5 points)
        Criterion 1: Uses plt.bar with bottom parameter
        Criterion 2: Stacking order correct
        Criterion 3: Bars aligned properly
        """
        score = 0
        
        # Criterion 1: Has bottom parameter (5 pts)
        if 'bottom=' in code or 'bottom =' in code:
            score += 5
        elif 'bar' in code:
            score += 2
        
        # Criterion 2: Multiple bar calls (stacking) (5 pts)
        bar_count = code.count('bar(')
        if bar_count >= 5:
            score += 5
        elif bar_count >= 3:
            score += 3
        elif bar_count >= 1:
            score += 2
        
        # Criterion 3: Cumulative calculation (5 pts)
        if 'bottom' in code and ('+=' in code or 'cumsum' in code or 'sum(' in code):
            score += 5
        elif 'bottom' in code:
            score += 3
        
        return min(score, self.max_scores['stacking'])


def score_participant_code(code):
    """
    Convenience function for scoring
    """
    scorer = MatplotlibScorer()
    return scorer.score_code(code)
