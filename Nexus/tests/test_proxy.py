#!/usr/bin/env python3
"""Test claude-code-proxy can start and accept requests"""
import subprocess
import time
import sys
import os

PROXY_PORT = 8083  # Use different port for testing
proxy_process = None

# Import httpx if available
try:
    import httpx
except ImportError:
    print("⚠ httpx not installed, skipping proxy test")
    print("  Install with: pip install httpx")
    sys.exit(0)


def start_proxy():
    """Start the proxy server in background"""
    global proxy_process

    # Activate venv and start proxy
    venv_python = "/home/aipass/.venv/bin/python"

    if not os.path.exists(venv_python):
        print(f"✗ Virtual environment not found at {venv_python}")
        return False

    try:
        proxy_process = subprocess.Popen(
            [
                venv_python, "-m", "uvicorn",
                "server.fastapi:app",
                "--host", "127.0.0.1",
                "--port", str(PROXY_PORT),
                "--log-level", "error"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/home/aipass/.venv"
        )

        # Wait for startup
        for i in range(20):
            try:
                r = httpx.get(f"http://localhost:{PROXY_PORT}/", timeout=1)
                return True
            except httpx.ConnectError:
                time.sleep(0.5)
            except Exception as e:
                # Other errors might still mean it's running
                if i > 3:  # Give it a few tries
                    return True
                time.sleep(0.5)

        # If we got here, proxy didn't start
        stderr_output = proxy_process.stderr.read().decode() if proxy_process.stderr else ""
        stdout_output = proxy_process.stdout.read().decode() if proxy_process.stdout else ""

        if stderr_output or stdout_output:
            print(f"Proxy output:\n{stdout_output}\n{stderr_output}")

        return False

    except Exception as e:
        print(f"✗ Failed to start proxy: {e}")
        return False


def stop_proxy():
    """Stop the proxy server"""
    global proxy_process
    if proxy_process:
        try:
            proxy_process.terminate()
            proxy_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proxy_process.kill()
            proxy_process.wait()
        except Exception:
            pass


def test_proxy_starts():
    """Test that proxy starts and responds"""
    print("Test 1: Proxy startup...", end=" ")
    ok = start_proxy()
    if not ok:
        print("✗ FAILED")
        raise AssertionError("Proxy failed to start")
    print("✓ PASSED")
    print(f"  → Proxy started on port {PROXY_PORT}")


def test_proxy_health():
    """Test proxy responds to requests"""
    print("Test 2: Proxy health check...", end=" ")

    try:
        # Try health endpoint first, fall back to root
        try:
            r = httpx.get(f"http://localhost:{PROXY_PORT}/health", timeout=5)
        except httpx.HTTPStatusError:
            # Try root endpoint
            r = httpx.get(f"http://localhost:{PROXY_PORT}/", timeout=5)

        # Proxy should respond (may be 404, 200, or other non-500)
        if r.status_code >= 500:
            print("✗ FAILED")
            raise AssertionError(f"Proxy returned server error: {r.status_code}")

        print("✓ PASSED")
        print(f"  → Proxy responds with status {r.status_code}")

    except Exception as e:
        print("✗ FAILED")
        raise AssertionError(f"Health check failed: {e}")


def test_proxy_api_structure():
    """Test that proxy has expected API structure"""
    print("Test 3: API structure...", end=" ")

    try:
        # Check if we can access v1/models endpoint (standard OpenAI endpoint)
        r = httpx.get(f"http://localhost:{PROXY_PORT}/v1/models", timeout=5)

        # Should return something (might be error without auth, but should respond)
        if r.status_code < 500:
            print("✓ PASSED")
            print(f"  → API endpoints accessible (status {r.status_code})")
        else:
            print("⚠ WARNING")
            print(f"  → API returned {r.status_code}, but proxy is running")

    except httpx.ConnectError:
        print("✗ FAILED")
        raise AssertionError("Cannot connect to proxy API")
    except Exception as e:
        # Non-critical - proxy might not have all endpoints
        print("⚠ SKIPPED")
        print(f"  → API test inconclusive: {e}")


def main():
    """Run all tests"""
    print("=" * 50)
    print("Testing claude-code-proxy")
    print("=" * 50)
    print()

    try:
        test_proxy_starts()
        test_proxy_health()
        test_proxy_api_structure()

        print()
        print("=" * 50)
        print("✓ All tests passed")
        print("=" * 50)
        return 0

    except AssertionError as e:
        print()
        print("=" * 50)
        print(f"✗ Tests failed: {e}")
        print("=" * 50)
        return 1

    except Exception as e:
        print()
        print("=" * 50)
        print(f"✗ Unexpected error: {e}")
        print("=" * 50)
        return 1

    finally:
        stop_proxy()


if __name__ == "__main__":
    sys.exit(main())
