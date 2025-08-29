import os
import signal
import sys

import coverage
import eventlet


COVERAGE_DIR = os.path.join(os.getcwd(), "coverage_data")
if not os.path.exists(COVERAGE_DIR):
    os.makedirs(COVERAGE_DIR)


class CoverageMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Start coverage for the current request
        cov = coverage.Coverage(
            data_file=os.path.join(
                COVERAGE_DIR, f"coverage.{os.getpid()}.{os.urandom(4).hex()}"
            ),
            auto_data=True,  # Automatically save data on exit
            branch=True,  # Include branch coverage
        )
        cov.start()

        try:
            # Pass control to the Flask application
            response = self.app(environ, start_response)
        finally:
            # Stop coverage for the current request
            cov.stop()
            cov.save()  # Save coverage data

        return response


if __name__ == "__main__":
    #cov_main = coverage.Coverage(data_file=os.path.join(os.getcwd(), ".coverage"))
    cov_main = coverage.Coverage(data_file=os.path.join(COVERAGE_DIR, "coverage_base" ), branch=True)
    cov_main.start()
    def stop_coverage_and_exit(signum, frame):
        if(signum == -1):
            print("program exits ")
        else:
            # ... (rest of your signal handler code - no changes needed here) ...
            print(f"\n[Coverage Runner] Signal {signum} received. Attempting to stop coverage and save data...")
        try:
            #¯if cov_main.is_started():
            cov_main.stop()
            cov_main.save()

            print("[Coverage Runner] Main process coverage data saved to '.coverage'.")
            eventlet.sleep(0.5)
        except Exception as e:
            print(f"[Coverage Runner] ERROR during coverage save: {e}", file=sys.stderr)
        os._exit(0)


    signal.signal(signal.SIGINT, stop_coverage_and_exit)
    signal.signal(signal.SIGTERM, stop_coverage_and_exit)
    try:
        from src.celery_app import CeleryTasks
        from src.app_factory import create_app
        from src.config import ConfigClass

        app = create_app(ConfigClass)
        CeleryTasks.init_celery(app)
        from werkzeug.serving import run_simple

        app.wsgi_app = CoverageMiddleware(app.wsgi_app)
        print("Running Flask app with coverage middleware. Interact with the server.")
        print(f"Coverage data will be stored in: {COVERAGE_DIR}")
        run_simple(
            "127.0.0.1", 5001, app, use_reloader=False
        )  # use_reloader=False is important for coverage
    except Exception:
        pass
    finally:
        stop_coverage_and_exit(-1)
    # app.run(host=ConfigClass.HOST_ADDR, port=ConfigClass.HOST_PORT, debug=True, threaded=True, use_reloader = ConfigClass.USE_RELOADER)
