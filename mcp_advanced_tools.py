"""
MCP Advanced Tools for Educational AI Tutor - COMPLETE PROFESSIONAL EDITION
===========================================================================

🎓 DESIGNED FOR:
- Schools and academies
- Neurodivergent learners (ADHD, Autism, Dyslexia)
- Professional programming education
- Competitive educational market

✨ UNIQUE FEATURES:
- Professional-grade data visualization (Excel-like)
- Complete cryptography suite (RSA, SHA-256, Digital Signatures)
- Interactive step-by-step tutorials
- Real-world security education
- Neurodivergent-optimized learning

🏆 MARKET ADVANTAGES:
- Only platform with RSA/modern crypto education
- Publication-quality charts (300 DPI)
- Industry-standard tools (not toy examples)
"""

import os
import json
import base64
import hashlib
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import io

# Cryptography imports
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  Warning: cryptography library not installed. Install with: pip install cryptography")


# ============================================================================
# PROFESSIONAL DATA VISUALIZATION - EXCEL-LIKE FEATURES
# ============================================================================

class AdvancedDataVisualization:
    """
    COMPETITIVE ADVANTAGE: Excel-like data visualization
    - Professional charts with trend lines
    - Statistical analysis
    - Publication-quality output (300 DPI)
    - Multiple chart styles
    - Neurodivergent-friendly colors and layouts
    """
    
    def __init__(self):
        # Neurodivergent-friendly color palettes
        self.color_schemes = {
            'default': ['#667eea', '#4facfe', '#f093fb', '#764ba2'],
            'high_contrast': ['#000000', '#FFFFFF', '#FF0000', '#00FF00'],
            'colorblind_safe': ['#0173B2', '#DE8F05', '#029E73', '#CC78BC'],
            'calm': ['#B4C7E7', '#C5E0B4', '#F4B183', '#E6B8AF'],
            'vibrant': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        }
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def create_professional_chart(
        self,
        chart_type: str,
        x_data: List,
        y_data: List,
        title: str = "Professional Chart",
        x_label: str = "X Axis",
        y_label: str = "Y Axis",
        style: str = 'professional',
        color_scheme: str = 'default',
        show_statistics: bool = True,
        show_trendline: bool = True,
        export_dpi: int = 300
    ) -> Dict[str, Any]:
        """Create publication-quality charts with professional features"""
        
        try:
            fig, ax = plt.subplots(figsize=(12, 7))
            colors = self.color_schemes.get(color_scheme, self.color_schemes['default'])
            
            # Apply professional styling
            if style == 'professional':
                ax.set_facecolor('#f8f9fa')
                fig.patch.set_facecolor('white')
            elif style == 'dark':
                ax.set_facecolor('#1e1e1e')
                fig.patch.set_facecolor('#2d2d2d')
                ax.tick_params(colors='white')
                ax.xaxis.label.set_color('white')
                ax.yaxis.label.set_color('white')
                ax.title.set_color('white')
            
            # Create the chart based on type
            if chart_type == 'line':
                ax.plot(x_data, y_data, marker='o', linewidth=2.5, 
                       markersize=8, color=colors[0], label='Data Points')
                
                # Add trend line
                if show_trendline and len(x_data) > 2:
                    try:
                        z = np.polyfit(range(len(x_data)), y_data, 1)
                        p = np.poly1d(z)
                        trend_y = p(range(len(x_data)))
                        ax.plot(x_data, trend_y, "--", color='#f59e0b', 
                               linewidth=2, label='Trend Line', alpha=0.7)
                        
                        slope = z[0]
                        trend_direction = "↗ Increasing" if slope > 0 else "↘ Decreasing"
                        ax.text(0.02, 0.02, f'Trend: {trend_direction}', 
                               transform=ax.transAxes,
                               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
                    except:
                        pass
            
            elif chart_type == 'bar':
                bars = ax.bar(x_data, y_data, color=colors[0], alpha=0.8, 
                             edgecolor=colors[1], linewidth=2)
                
                # Add value labels on bars
                if show_statistics:
                    for bar in bars:
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height,
                               f'{height:.1f}',
                               ha='center', va='bottom', fontweight='bold',
                               fontsize=10)
            
            elif chart_type == 'scatter':
                scatter = ax.scatter(x_data, y_data, s=100, c=y_data, 
                                   cmap='viridis', alpha=0.6, edgecolors='black')
                plt.colorbar(scatter, ax=ax, label='Value Intensity')
                
            elif chart_type == 'area':
                ax.fill_between(x_data, y_data, alpha=0.3, color=colors[0])
                ax.plot(x_data, y_data, linewidth=2, color=colors[0])
            
            elif chart_type == 'histogram':
                n, bins, patches = ax.hist(y_data, bins=20, color=colors[0], 
                                          alpha=0.7, edgecolor='black')
                
                cm = plt.cm.get_cmap('viridis')
                bin_centers = 0.5 * (bins[:-1] + bins[1:])
                col = bin_centers - min(bin_centers)
                col /= max(col)
                for c, p in zip(col, patches):
                    plt.setp(p, 'facecolor', cm(c))
            
            elif chart_type == 'box':
                bp = ax.boxplot([y_data], vert=True, patch_artist=True)
                for patch in bp['boxes']:
                    patch.set_facecolor(colors[0])
                ax.set_xticklabels(['Data'])
            
            # Professional formatting
            ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
            ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3, linestyle='--')
            
            if chart_type in ['line', 'area'] and show_trendline:
                ax.legend(loc='best', framealpha=0.9, fontsize=10)
            
            # Add statistics annotation
            if show_statistics and len(y_data) > 0:
                stats_text = (
                    f'Mean: {np.mean(y_data):.2f}\n'
                    f'Median: {np.median(y_data):.2f}\n'
                    f'Std Dev: {np.std(y_data):.2f}\n'
                    f'Range: {np.max(y_data) - np.min(y_data):.2f}'
                )
                ax.text(0.98, 0.98, stats_text, transform=ax.transAxes,
                       verticalalignment='top', horizontalalignment='right',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                       fontsize=9, family='monospace')
            
            # Export at high DPI
            buffer = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', dpi=export_dpi, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            # Calculate comprehensive statistics
            stats = {
                'count': len(y_data),
                'mean': float(np.mean(y_data)),
                'median': float(np.median(y_data)),
                'std': float(np.std(y_data)),
                'min': float(np.min(y_data)),
                'max': float(np.max(y_data)),
                'range': float(np.max(y_data) - np.min(y_data)),
                'q1': float(np.percentile(y_data, 25)),
                'q3': float(np.percentile(y_data, 75))
            }
            
            return {
                'success': True,
                'image': f'data:image/png;base64,{image_base64}',
                'stats': stats,
                'chart_type': chart_type,
                'dpi': export_dpi
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'suggestion': 'Check data format and try again'
            }


# ============================================================================
# PROFESSIONAL CRYPTOGRAPHY SUITE
# ============================================================================

class ProfessionalCryptographyTools:
    """
    COMPETITIVE ADVANTAGE: Complete cryptography education
    - RSA public-key cryptography (HTTPS/SSH)
    - SHA-256 cryptographic hashing (passwords)
    - Digital signatures (blockchain)
    - Fernet symmetric encryption (AES-128)
    """
    
    def __init__(self):
        self.algorithms = {
            'caesar': 'Educational - Ancient cipher',
            'fernet': 'Production - Symmetric encryption (AES-128)',
            'rsa': 'Production - Public-key cryptography',
            'sha256': 'Production - Cryptographic hashing',
            'digital_signature': 'Production - Authentication'
        }
        self.crypto_available = CRYPTO_AVAILABLE
    
    def caesar_cipher(self, text: str, shift: int, decrypt: bool = False) -> Dict[str, Any]:
        """Educational Caesar cipher with step-by-step explanations"""
        
        if decrypt:
            shift = -shift
        
        result = ""
        step_by_step = []
        
        for i, char in enumerate(text):
            if char.isalpha():
                start = ord('A') if char.isupper() else ord('a')
                shifted = (ord(char) - start + shift) % 26
                new_char = chr(start + shifted)
                result += new_char
                
                step_by_step.append({
                    'position': i,
                    'original': char,
                    'shifted': new_char,
                    'explanation': f'{char} + {shift} = {new_char}'
                })
            else:
                result += char
                step_by_step.append({
                    'position': i,
                    'original': char,
                    'shifted': char,
                    'explanation': f'Keep {char} (not a letter)'
                })
        
        return {
            'original': text,
            'result': result,
            'method': 'Caesar Cipher',
            'shift': abs(shift),
            'direction': 'decrypt' if decrypt else 'encrypt',
            'security_level': '🎓 Educational Only - NOT SECURE!',
            'why_insecure': 'Only 25 possible keys - can be broken in seconds',
            'step_by_step': step_by_step[:10],  # Limit to first 10 for readability
            'neurodivergent_tip': '💡 Think of it like a rotating alphabet wheel!'
        }
    
    def fernet_encryption(self, text: str, key: bytes = None, decrypt: bool = False) -> Dict[str, Any]:
        """Production-grade Fernet (AES-128) symmetric encryption"""
        
        if not self.crypto_available:
            return {'error': 'Cryptography library not installed. Run: pip install cryptography'}
        
        try:
            if key is None:
                key = Fernet.generate_key()
            
            fernet = Fernet(key)
            
            if decrypt:
                decrypted = fernet.decrypt(text.encode()).decode()
                return {
                    'result': decrypted,
                    'method': 'Fernet (AES-128)',
                    'security_level': '�� HIGH - Industry Standard',
                    'key_used': key.decode()
                }
            else:
                encrypted = fernet.encrypt(text.encode()).decode()
                return {
                    'original': text,
                    'result': encrypted,
                    'method': 'Fernet (AES-128)',
                    'security_level': '🔒 HIGH - Industry Standard',
                    'key': key.decode(),
                    'how_it_works': 'Uses AES-128 in CBC mode with HMAC authentication',
                    'real_world_use': 'Password managers, secure messaging, file encryption',
                    'important_notes': [
                        '⚠️ Never share the key publicly',
                        '�� Store key in environment variables',
                        '💾 If you lose the key, data is lost forever'
                    ]
                }
        except Exception as e:
            return {'error': str(e)}
    
    def rsa_demonstration(self, message: str) -> Dict[str, Any]:
        """RSA-2048 public-key cryptography demonstration"""
        
        if not self.crypto_available:
            return {'error': 'Cryptography library not installed. Run: pip install cryptography'}
        
        try:
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            
            # Encrypt with public key
            encrypted = public_key.encrypt(
                message.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Decrypt with private key
            decrypted = private_key.decrypt(
                encrypted,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            return {
                'success': True,
                'original': message,
                'encrypted': base64.b64encode(encrypted).decode()[:100] + '...',
                'decrypted': decrypted.decode(),
                'method': 'RSA-2048 (Public-Key Cryptography)',
                'security_level': '🔐 VERY HIGH - Used by HTTPS',
                'key_size': '2048 bits',
                'real_world_use': [
                    '🌐 HTTPS (green padlock in browser)',
                    '🔐 SSH (secure server access)',
                    '₿ Bitcoin/cryptocurrency wallets',
                    '📧 Email encryption (PGP/GPG)'
                ],
                'how_it_works': [
                    '1. Generate key pair: Public + Private',
                    '2. Anyone can encrypt with public key',
                    '3. Only YOU can decrypt with private key',
                    '4. Based on factoring large prime numbers'
                ]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cryptographic_hashing(self, text: str, algorithm: str = 'sha256') -> Dict[str, Any]:
        """SHA-256 cryptographic hashing - how websites store passwords"""
        
        hash_functions = {
            'sha256': (hashlib.sha256, 'SHA-256 (Bitcoin, SSL certificates)'),
            'sha512': (hashlib.sha512, 'SHA-512 (More secure, slower)'),
            'md5': (hashlib.md5, 'MD5 (BROKEN - Educational only!)')
        }
        
        if algorithm not in hash_functions:
            return {'error': f'Algorithm {algorithm} not supported'}
        
        hash_func, description = hash_functions[algorithm]
        hash_obj = hash_func(text.encode())
        hash_hex = hash_obj.hexdigest()
        
        return {
            'original': text,
            'hash': hash_hex,
            'algorithm': algorithm.upper(),
            'length': len(hash_hex),
            'security_level': '🔐 HIGH' if algorithm != 'md5' else '⚠️ BROKEN',
            'description': description,
            'how_it_works': [
                '1. Takes any input (password, file, message)',
                '2. Produces fixed-length output (hash)',
                '3. IMPOSSIBLE to reverse (one-way)',
                '4. Tiny change in input = completely different hash'
            ],
            'real_world_use': [
                '🔐 Password storage',
                '📁 File integrity checks',
                '₿ Bitcoin mining',
                '�� Digital signatures'
            ]
        }
    
    def digital_signature_demo(self, message: str) -> Dict[str, Any]:
        """Digital signatures - how software proves authenticity"""
        
        if not self.crypto_available:
            return {'error': 'Cryptography library not installed. Run: pip install cryptography'}
        
        try:
            # Generate key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            
            # Sign message with private key
            signature = private_key.sign(
                message.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Verify signature with public key
            try:
                public_key.verify(
                    signature,
                    message.encode(),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                verified = True
            except:
                verified = False
            
            return {
                'success': True,
                'message': message,
                'signature': base64.b64encode(signature).decode()[:100] + '...',
                'verified': verified,
                'method': 'RSA Digital Signature',
                'security_level': '🔐 VERY HIGH',
                'how_it_works': [
                    '1. Sender uses PRIVATE key to create signature',
                    '2. Anyone uses PUBLIC key to verify signature',
                    '3. Proves message really from sender',
                    '4. Proves message wasn\'t tampered with'
                ],
                'real_world_use': [
                    '💻 Software updates (Windows, macOS)',
                    '₿ Bitcoin transactions',
                    '📧 Email authentication',
                    '📄 PDF signatures'
                ]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def caesar_cipher_tutorial(self) -> Dict[str, Any]:
        """Complete tutorial for Caesar cipher"""
        return {
            'title': '🎓 Caesar Cipher - Ancient Encryption',
            'difficulty': 'Beginner',
            'time': '10 minutes',
            'explanation': '''
The Caesar cipher is a simple substitution cipher where each letter is shifted by a fixed number.

Example with shift of 3:
A → D, B → E, C → F, ..., X → A, Y → B, Z → C

HELLO → KHOOR

Why it's called "Caesar":
Julius Caesar used this cipher to communicate with his generals in 50 BC!

Why it's NOT secure:
- Only 25 possible keys (shift 1-25)
- Can be broken in seconds by trying all possibilities
- Pattern analysis makes it even easier

Modern use:
- Educational tool only
- ROT13 (shift of 13) used in online forums to hide spoilers
            ''',
            'practice': 'Try encrypting your name with shift 5!'
        }
    
    def create_encryption_demo(self, text: str, method: str, key: Any) -> Dict[str, Any]:
        """Create interactive encryption demonstration"""
        
        if method == 'caesar':
            return self.caesar_cipher(text, int(key))
        elif method == 'fernet' and self.crypto_available:
            return self.fernet_encryption(text)
        elif method == 'rsa' and self.crypto_available:
            return self.rsa_demonstration(text)
        elif method == 'hash':
            return self.cryptographic_hashing(text, 'sha256')
        else:
            return {'error': f'Method {method} not available or crypto library not installed'}


# ============================================================================
# GRAPH TEACHING TOOLS
# ============================================================================

class GraphTeachingTools:
    """Enhanced graph teaching with neurodivergent-friendly features"""
    
    def __init__(self):
        self.colors = ['#4facfe', '#667eea', '#f093fb', '#764ba2']
    
    def create_simple_graph(self, data: Dict[str, Any]) -> str:
        """Create educational graph"""
        
        try:
            graph_type = data.get('type', 'line')
            x_data = data.get('x', list(range(10)))
            y_data = data.get('y', list(range(10)))
            title = data.get('title', 'Educational Graph')

            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor('#f8fafc')
            ax.set_facecolor('#ffffff')

            if graph_type == 'line':
                ax.plot(x_data, y_data, color=self.colors[0], linewidth=2, marker='o', markersize=8)
            elif graph_type == 'bar':
                ax.bar(x_data, y_data, color=self.colors[1], alpha=0.8, edgecolor='black')
            elif graph_type == 'scatter':
                ax.scatter(x_data, y_data, color=self.colors[2], s=100, alpha=0.6, edgecolors='black')
            elif graph_type == 'pie':
                labels = data.get('labels', [f'Slice {i+1}' for i in range(len(y_data))])
                ax.pie(y_data, labels=labels, colors=self.colors, autopct='%1.1f%%', startangle=90)

            if graph_type != 'pie':
                ax.set_xlabel('X Axis', fontsize=11, fontweight='bold')
                ax.set_ylabel('Y Axis', fontsize=11, fontweight='bold')
                ax.grid(True, alpha=0.3, linestyle='--')
            
            ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

            buffer = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()

            return f"data:image/png;base64,{image_base64}"

        except Exception as e:
            return f"Error creating graph: {str(e)}"
    
    def generate_graph_tutorial(self, graph_type: str) -> Dict[str, Any]:
        """Generate interactive tutorial for graph types"""
        
        tutorials = {
            'line': {
                'title': '📈 Line Graphs - Showing Trends Over Time',
                'explanation': '''Line graphs are perfect for showing how data changes over time!

🎯 When to Use:
- Temperature changes throughout the day
- Stock prices over months
- Student progress over time
- Website traffic trends

📊 Key Components:
- X-axis: Usually time (hours, days, months)
- Y-axis: The value being measured
- Line: Connects data points to show trend

💡 Tip: Look for patterns - going up, down, or staying flat?''',
                'code_example': '''import matplotlib.pyplot as plt

weeks = [1, 2, 3, 4, 5]
scores = [65, 70, 75, 85, 90]

plt.plot(weeks, scores, marker='o')
plt.xlabel('Week')
plt.ylabel('Score')
plt.title('Student Progress')
plt.show()''',
                'practice': 'Try creating a line graph of your daily mood for a week!'
            },
            'bar': {
                'title': '📊 Bar Charts - Comparing Categories',
                'explanation': '''Bar charts are great for comparing different categories!

🎯 When to Use:
- Comparing sales across products
- Survey results by age group
- Scores of different students
- Monthly expenses by category

📊 Key Components:
- X-axis: Categories being compared
- Y-axis: Values/amounts
- Bars: Height shows the value

💡 Tip: Taller bars = higher values, easy to spot differences!''',
                'code_example': '''import matplotlib.pyplot as plt

subjects = ['Math', 'Science', 'English', 'History']
scores = [85, 92, 78, 88]

plt.bar(subjects, scores, color='skyblue')
plt.xlabel('Subject')
plt.ylabel('Score')
plt.title('Test Scores by Subject')
plt.show()''',
                'practice': 'Create a bar chart of your favorite foods and ratings!'
            }
        }
        
        return tutorials.get(graph_type, {
            'error': f'Tutorial for {graph_type} not found',
            'available': list(tutorials.keys())
        })


# ============================================================================
# DALL-E IMAGE GENERATOR
# ============================================================================

class DALLEImageGenerator:
    """DALL-E integration for visual learning"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1/images/generations"
    
    def generate_educational_image(self, concept: str, style: str = 'cartoon') -> Dict[str, Any]:
        """Generate educational images for visual learning"""
        
        if not self.api_key:
            return {
                'error': 'OpenAI API key not set',
                'suggestion': 'Set OPENAI_API_KEY environment variable'
            }
        
        try:
            style_prompts = {
                'cartoon': 'friendly cartoon style, educational, colorful',
                'diagram': 'clean technical diagram, labeled, educational',
                'realistic': 'realistic style, clear, educational',
                'comic': 'comic book style, fun, educational'
            }
            
            prompt = f"{concept}, {style_prompts.get(style, style_prompts['cartoon'])}"
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'prompt': prompt,
                'n': 1,
                'size': '1024x1024'
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'image_url': result['data'][0]['url'],
                    'prompt': prompt,
                    'style': style
                }
            else:
                return {
                    'success': False,
                    'error': f'API error: {response.status_code}',
                    'details': response.text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'suggestion': 'Check API key and internet connection'
            }


# ============================================================================
# PYTHON DOCUMENTATION INTEGRATION
# ============================================================================

class PythonDocsIntegration:
    """Python documentation integration for learning"""
    
    def __init__(self):
        self.python_docs_base = "https://docs.python.org/3/"
        self.common_functions = {
            'print': 'Prints output to console',
            'len': 'Returns length of object',
            'range': 'Creates sequence of numbers',
            'input': 'Gets user input',
            'int': 'Converts to integer',
            'str': 'Converts to string',
            'list': 'Creates a list',
            'dict': 'Creates a dictionary',
            'open': 'Opens a file',
            'type': 'Returns type of object'
        }
    
    def get_function_documentation(self, function_name: str) -> Dict[str, Any]:
        """Get Python function documentation"""
        
        # Check if it's a common function
        if function_name in self.common_functions:
            return {
                'function': function_name,
                'description': self.common_functions[function_name],
                'docs_url': f'{self.python_docs_base}library/functions.html#{function_name}',
                'example': self._get_example(function_name),
                'tips': self._get_tips(function_name)
            }
        
        return {
            'function': function_name,
            'description': f'Documentation for {function_name}',
            'docs_url': f'{self.python_docs_base}search.html?q={function_name}',
            'suggestion': 'Visit docs.python.org for complete documentation'
        }
    
    def _get_example(self, function_name: str) -> str:
        """Get example code for function"""
        
        examples = {
            'print': 'print("Hello, World!")',
            'len': 'len([1, 2, 3])  # Returns: 3',
            'range': 'for i in range(5): print(i)',
            'input': 'name = input("Enter your name: ")',
            'int': 'num = int("123")  # Converts string to int',
            'str': 'text = str(123)  # Converts to string',
            'list': 'my_list = list([1, 2, 3])',
            'dict': 'my_dict = dict(name="Alice", age=25)',
            'open': 'with open("file.txt", "r") as f: content = f.read()',
            'type': 'type(123)  # Returns: <class \'int\'>'
        }
        
        return examples.get(function_name, f'{function_name}()')
    
    def _get_tips(self, function_name: str) -> List[str]:
        """Get tips for using function"""
        
        tips = {
            'print': ['Use end="" to print without newline', 'Use sep="" to change separator'],
            'len': ['Works with lists, strings, dicts, and more', 'Returns integer count'],
            'range': ['range(5) gives 0,1,2,3,4 (not 5!)', 'Use range(start, stop, step)'],
            'input': ['Always returns a string', 'Convert with int() or float() if needed'],
            'int': ['Will raise error if string is not numeric', 'Use try/except for safety'],
            'str': ['Converts almost anything to string', 'Useful for concatenation']
        }
        
        return tips.get(function_name, ['Check official docs for more info'])


# ============================================================================
# MAIN EXPORTS
# ============================================================================

def get_all_tools():
    """Get all available tools for MCP integration"""
    return {
        'professional_viz': AdvancedDataVisualization(),
        'professional_crypto': ProfessionalCryptographyTools(),
        'graph_teaching': GraphTeachingTools(),
        'dalle_generator': DALLEImageGenerator(),
        'python_docs': PythonDocsIntegration()
    }


if __name__ == '__main__':
    print("=" * 70)
    print("🚀 MCP ADVANCED TOOLS - COMPLETE EDITION")
    print("=" * 70)
    print("\n✨ LOADED FEATURES:")
    print("   📊 Professional Data Visualization")
    print("   🔐 Complete Cryptography Suite")
    if CRYPTO_AVAILABLE:
        print("   ✅ Cryptography library: AVAILABLE")
    else:
        print("   ⚠️  Cryptography library: NOT INSTALLED")
        print("      Install with: pip install cryptography")
    print("   📈 Graph Teaching Tools")
    print("   🎨 DALL-E Integration")
    print("   �� Python Documentation")
    print("\n🏆 ALL TOOLS READY!")
    print("=" * 70)
