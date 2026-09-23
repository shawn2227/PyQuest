import subprocess
import sys
import tempfile
import os

def run_user_code_with_tests(user_code: str, test_code: str, timeout_seconds: float = 4.0):
    """
    Runs user code to capture raw output, then runs with tests to validate.
    Provides clean output like W3Schools.
    """
    # 1. Run user code alone to get clean stdout/stderr
    user_script = f"""# --- USER SUBMISSION ---
{user_code}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        user_temp_path = f.name
        f.write(user_script)

    user_stdout = ""
    user_stderr = ""
    user_success = False

    try:
        proc_user = subprocess.run(
            [sys.executable, user_temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        user_stdout = proc_user.stdout.strip()
        user_stderr = proc_user.stderr.strip()
        user_success = (proc_user.returncode == 0)
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"TimeoutError: Execution exceeded {timeout_seconds} seconds limit.",
            "message": "Code execution timed out. Watch out for infinite loops!"
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "message": "Internal runner error."
        }
    finally:
        if os.path.exists(user_temp_path):
            try: os.remove(user_temp_path)
            except: pass

    # If user code alone has syntax errors or runtime errors, return immediately
    if not user_success:
        cleaned_stderr = user_stderr.replace(user_temp_path, "main.py")
        return {
            "success": False,
            "stdout": user_stdout,
            "stderr": cleaned_stderr,
            "message": "Runtime error in your code."
        }

    # 2. User code ran successfully. Now run with tests to validate.
    full_script = f"""{user_code}
# --- TEST SUITE ---
{test_code}
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        test_temp_path = f.name
        f.write(full_script)

    try:
        proc_test = subprocess.run(
            [sys.executable, test_temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        
        if proc_test.returncode == 0:
            return {
                "success": True,
                "stdout": user_stdout,  # Only show user's stdout, not the test's "TEST_PASSED" prints!
                "stderr": "",
                "message": "All unit tests passed! XP and badges awarded. 🔥"
            }
        else:
            # Tests failed. Parse the assertion error for a clean message.
            test_stderr = proc_test.stderr.strip()
            
            # Extract the actual assertion message if present, otherwise just show standard error
            error_lines = test_stderr.split('\n')
            clean_err = "Test validation failed. Check your logic."
            for line in reversed(error_lines):
                if line.startswith("AssertionError"):
                    clean_err = line
                    break
                elif line.strip() and not line.startswith("  File") and not line.startswith("Traceback"):
                    clean_err = line
                    
            return {
                "success": False,
                "stdout": user_stdout,
                "stderr": f"Validation Error: {clean_err}",
                "message": "Your code ran, but it did not pass the mission requirements."
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": user_stdout,
            "stderr": "TimeoutError during validation.",
            "message": "Validation timed out."
        }
    finally:
        if os.path.exists(test_temp_path):
            try: os.remove(test_temp_path)
            except: pass
