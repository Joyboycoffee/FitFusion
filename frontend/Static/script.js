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

            if (!name || !email || !password) {
                alert("Please fill in all fields.");
                return;
            }

            signupButton.disabled = true;
            
            try {
                const response = await fetch("/signup", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, email, password })
                });

                if (!response.ok) {
                    throw new Error("Signup failed. Please try again.");
                }
                
                const data = await response.json();
                alert(data.message || "Signup successful!");
                signupForm.reset();
            } catch (error) {
                console.error("Signup Error:", error);
                alert(error.message);
            } finally {
                signupButton.disabled = false;
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

            if (!email || !password) {
                alert("Please enter your email and password.");
                return;
            }

            loginButton.disabled = true;
            
            try {
                const response = await fetch("/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });

                if (!response.ok) {
                    throw new Error(`Login failed. Status: ${response.status}`);
                }

                const data = await response.json();
                
                if (data.redirect) {
                    window.location.href = data.redirect; // ✅ Redirect to dashboard
                } else {
                    alert(data.message || "Invalid response from server.");
                }
            } catch (error) {
                console.error("Login Error:", error);
                alert(error.message);
            } finally {
                loginButton.disabled = false;
            }
        });
    }
});