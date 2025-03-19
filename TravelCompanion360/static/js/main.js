// Travel Companion - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Navigation Toggle
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarMenu = document.querySelector('.navbar-menu');
    
    if (navbarToggle && navbarMenu) {
        navbarToggle.addEventListener('click', function() {
            navbarMenu.classList.toggle('active');
        });
    }
    
    // Fade in elements
    const fadeElements = document.querySelectorAll('.fade-in');
    if (fadeElements.length > 0) {
        setTimeout(() => {
            fadeElements.forEach(el => {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            });
        }, 100);
    }
    
    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.alert');
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            // Don't auto-dismiss important warning messages about passwords
            if (!message.classList.contains('alert-warning')) {
                setTimeout(() => {
                    message.style.opacity = '0';
                    setTimeout(() => {
                        message.style.display = 'none';
                    }, 500);
                }, 5000);
            }
        });
    }
    
    // Car type selection in car rental form
    const carTypes = document.querySelectorAll('.car-type');
    const carTypeInput = document.getElementById('car_type');
    
    if (carTypes.length > 0 && carTypeInput) {
        carTypes.forEach(type => {
            type.addEventListener('click', function() {
                // Remove active class from all
                carTypes.forEach(t => t.classList.remove('active'));
                
                // Add active class to the clicked one
                this.classList.add('active');
                
                // Set the value in the hidden input
                const carTypeValue = this.getAttribute('data-value');
                carTypeInput.value = carTypeValue;
            });
        });
    }
    
    // Hotel booking form submission
    const hotelBookingForms = document.querySelectorAll('.hotel-booking-form');
    
    if (hotelBookingForms.length > 0) {
        hotelBookingForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const hotelId = this.getAttribute('data-hotel-id');
                const hotelName = this.getAttribute('data-hotel-name');
                
                // Show confirmation before submitting
                if (confirm(`Are you sure you want to book ${hotelName}?`)) {
                    this.submit();
                }
            });
        });
    }
    
    // Initialize date pickers if available
    const dateInputs = document.querySelectorAll('input[type="date"]');
    if (dateInputs.length > 0) {
        // Set min date to today for all date inputs
        const today = new Date().toISOString().split('T')[0];
        dateInputs.forEach(input => {
            input.setAttribute('min', today);
        });
    }
    
    // Hotel search form validation
    const hotelSearchForm = document.getElementById('hotel-search-form');
    if (hotelSearchForm) {
        hotelSearchForm.addEventListener('submit', function(e) {
            const destinationInput = document.getElementById('destination');
            const budgetInput = document.getElementById('budget');
            
            let isValid = true;
            
            if (!destinationInput.value.trim()) {
                showInputError(destinationInput, 'Please enter a destination');
                isValid = false;
            } else {
                hideInputError(destinationInput);
            }
            
            if (!budgetInput.value || budgetInput.value <= 0) {
                showInputError(budgetInput, 'Please enter a valid budget amount');
                isValid = false;
            } else {
                hideInputError(budgetInput);
            }
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
    
    // Functions to show/hide input validation errors
    function showInputError(inputElement, message) {
        // Remove any existing error message
        hideInputError(inputElement);
        
        // Add error class to input
        inputElement.classList.add('is-invalid');
        
        // Create and append error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        inputElement.parentNode.appendChild(errorDiv);
    }
    
    function hideInputError(inputElement) {
        // Remove error class
        inputElement.classList.remove('is-invalid');
        
        // Remove any existing error message
        const existingError = inputElement.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }
    }
    
    // Password visibility toggle
    const passwordToggle = document.querySelector('.password-toggle');
    if (passwordToggle) {
        passwordToggle.addEventListener('click', function() {
            const passwordInput = document.getElementById('password');
            const icon = this.querySelector('i');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    }
});
