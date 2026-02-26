document.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signup-form');
    const loginForm = document.getElementById('login-form');
  
    // 🔹 SIGNUP VALIDATION
    if (signupForm) {
      signupForm.addEventListener('submit', function (e) {
        e.preventDefault();
  
        const name = document.getElementById('name').value.trim();
        const phone = document.getElementById('phone').value.trim();
        const password = document.getElementById('password').value.trim();
        const confirmPassword = document.getElementById('confirm-password').value.trim();
        const message = document.getElementById('generated-id');
  
        const passwordRegex =
          /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,15}$/;
  
        if (!passwordRegex.test(password)) {
          alert(
            "Password must be 8–15 chars long, with uppercase, lowercase, number, and special character."
          );
          return;
        }
  
        if (password !== confirmPassword) {
          alert("Passwords do not match!");
          return;
        }
  
        // Generate Unique ID
        const uniqueId = Math.random().toString(36).substring(2, 8).toUpperCase();
        message.textContent = `✅ Your Unique ID: ${uniqueId}`;
  
        // Send Data to Flask
        fetch('/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, phone, password, unique_id: uniqueId })
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            alert("Account created! Your Unique ID: " + uniqueId);
            window.location.href = '/login';
          } else {
            alert(data.message || "Signup failed");
          }
        });
      });
    }
  
    // 🔹 LOGIN VALIDATION
    if (loginForm) {
      loginForm.addEventListener('submit', function (e) {
        e.preventDefault();
  
        const unique_id = document.getElementById('unique-id').value.trim();
        const password = document.getElementById('login-password').value.trim();
  
        fetch('/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ unique_id, password })
        })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            window.location.href = '/dashboard';
          } else {
            alert(data.message || "Invalid credentials");
          }
        });
      });
    }
  });
  