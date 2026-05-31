document.addEventListener('DOMContentLoaded', function() {
    // Handle rating button interactions
    document.querySelectorAll('.rating-group').forEach(group => {
        const field = group.dataset.field;
        const buttons = group.querySelectorAll('.rating-btn');
        
        buttons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove selected class from all buttons in this group
                buttons.forEach(btn => btn.classList.remove('selected'));
                
                // Add selected class to clicked button
                this.classList.add('selected');
                
                // Store the value for form submission
                group.dataset.selectedValue = this.dataset.value;
            });
        });
    });

    // Handle form submission
    document.getElementById('feedbackForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Collect form data
        const formData = new FormData(this);
        const feedback = Object.fromEntries(formData);
        
        // Add rating values
        document.querySelectorAll('.rating-group').forEach(group => {
            const field = group.dataset.field;
            const selectedValue = group.dataset.selectedValue;
            if (selectedValue) {
                feedback[field] = selectedValue;
            }
        });
        
        // Add checkbox values
        const features = [];
        document.querySelectorAll('input[name="features"]:checked').forEach(checkbox => {
            features.push(checkbox.value);
        });
        feedback.features = features;
        
        // Add metadata
        feedback.timestamp = new Date().toISOString();
        feedback.student_id = 'feedback_user_' + Date.now();
        
        // Validate required fields
        if (!feedback.background) {
            alert('Please select your learning background level.');
            return;
        }
        
        // Submit feedback
        fetch('/submit_feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(feedback)
        })
        .then(response => {
            if (response.ok) {
                alert('Thank you for your feedback! Your input helps improve the learning experience.');
                window.location.href = '/';
            } else {
                alert('Sorry, there was an error submitting your feedback. Please try again.');
            }
        })
        .catch(error => {
            console.error('Feedback submission error:', error);
            alert('A network error occurred. Please try again later.');
        });
    });
});
