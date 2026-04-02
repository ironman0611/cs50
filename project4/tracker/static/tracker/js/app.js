document.addEventListener('DOMContentLoaded', function() {
    
    // Countdown timer
    function updateCountdowns() {
        const countdownElements = document.querySelectorAll('.countdown');
        
        countdownElements.forEach(element => {
            const deadline = new Date(element.dataset.deadline);
            const now = new Date();
            const diff = deadline - now;
            
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            
            element.textContent = `${days} days, ${hours} hours`;
        });
    }
    
    // Update countdowns every minute
    updateCountdowns();
    setInterval(updateCountdowns, 60000);
    
    // Task toggle
    window.toggleTask = function(taskId) {
        fetch(`/api/task/${taskId}/toggle`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            const checkbox = document.querySelector(`#task-${taskId}`);
            if (checkbox) {
                checkbox.checked = data.completed;
            }
        })
        .catch(error => console.error('Error:', error));
    }
});
