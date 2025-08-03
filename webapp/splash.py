SPLASH_HTML= r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UIL-DL</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            background-color: #121212;
            color: #ffffff;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            transition: opacity 0.5s ease-out;
        }
        
        .splash-container {
            text-align: center;
        }
        
        .logo {
            font-size: 3.5rem;
            font-weight: bold;
            letter-spacing: 2px;
            margin-bottom: 1rem;
        }
        
        .tagline {
            font-size: 1.2rem;
            color: #aaaaaa;
            margin-bottom: 3rem;
        }
        
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.2);
            border-left-color: #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }
        
        /* Fade-out animation */
        body.fade-out {
            opacity: 0;
        }

    </style>
</head>
<body>
    <div class="splash-container">
        <div class="logo">UIL-DL</div>
        <div class="tagline">by acemavrick</div>
        <div class="spinner"></div>
    </div>

    <script>
        // This function will be called from Python to trigger the fade-out
        function fadeOutSplash() {
            document.body.classList.add('fade-out');
        }
    </script>
</body>
</html>
"""