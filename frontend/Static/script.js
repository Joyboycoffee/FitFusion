window.addEventListener("load", () => {
    const container = document.getElementById("container");
    if (container) {
        container.classList.add("active"); // Ensure signup is shown initially
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const container = document.getElementById("container");
    const registerBtn = document.getElementById("register");
    const loginBtn = document.getElementById("login");

    if (registerBtn && loginBtn && container) {
        registerBtn.addEventListener("click", () => container.classList.add("active"));
        loginBtn.addEventListener("click", () => container.classList.remove("active"));
    }

    const signupForm = document.getElementById("signup-form");
    const loginForm = document.getElementById("login-form");

    // ✅ Improved Signup Handling
    if (signupForm) {
        signupForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            
            const name = document.getElementById("signup-name").value.trim();
            const email = document.getElementById("signup-email").value.trim();
            const password = document.getElementById("signup-password").value.trim();
            const signupButton = document.getElementById("signup-button");

            // Basic Validation
            if (!name || !email || !password) {
                alert("Please fill in all fields.");
                return;
            }

            signupButton.disabled = true; // Disable button to prevent multiple clicks
            
            try {
                const response = await fetch("http://127.0.0.1:5000/signup", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, email, password })
                });

                const data = await response.json();
                alert(data.message || data.error); // Show response message
            } catch (error) {
                console.error("Signup Error:", error);
                alert("An error occurred while signing up. Please try again.");
            } finally {
                signupButton.disabled = false; // Re-enable button
            }
        });
    }

    // ✅ Improved Login Handling
    if (loginForm) {
        loginForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            
            const email = document.getElementById("login-email").value.trim();
            const password = document.getElementById("login-password").value.trim();
            const loginButton = document.getElementById("login-button");

            // Basic Validation
            if (!email || !password) {
                alert("Please enter your email and password.");
                return;
            }

            loginButton.disabled = true; // Disable button to prevent multiple clicks
            
            try {
                const response = await fetch("http://127.0.0.1:5000/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();
                if (data.success) {
                    window.location.href = "/dashboard"; // Redirect on success
                } else {
                    alert(data.message || "Login failed. Please check your credentials.");
                }
            } catch (error) {
                console.error("Login Error:", error);
                alert("An error occurred while logging in. Please try again.");
            } finally {
                loginButton.disabled = false; // Re-enable button
            }
        });
    }
});
