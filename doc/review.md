# Media Repo Code Review

This document provides a review of the Media Repo application, highlighting architectural, design, and implementation issues.

## Architectural Issues

1.  **Monolithic Structure:** The application follows a monolithic architecture, where all components are tightly coupled. This can make it difficult to scale, maintain, and deploy individual components independently. Consider a microservices architecture for better separation of concerns.

2.  **Lack of a Service Layer:** The business logic is scattered between the resource classes (endpoints) and the models. This violates the principle of separation of concerns and makes the code harder to test and maintain. Introduce a service layer to encapsulate the business logic.

3.  **Direct Database Access in Endpoints:** Some endpoints directly access the database, which is not a good practice. All database interactions should be handled by the service layer or a dedicated data access layer.

4.  **Synchronous Operations in Requests:** Some operations, like generating previews, are performed synchronously within the request-response cycle. This can lead to long response times and a poor user experience. Offload such tasks to a background worker like Celery.

## Design Issues

1.  **Inconsistent Naming Conventions:** The naming of files, classes, and functions is inconsistent. For example, some files use snake_case (`create_resources.py`) while others use PascalCase (`EntityModel.py`). Adhering to a consistent naming convention (e.g., PEP 8 for Python) improves code readability.

2.  **Fat Models:** The `EntityModel` class is a "fat model" that contains a lot of business logic. This makes the model difficult to test and reuse. Move the business logic to a service layer.

3.  **Poor Error Handling:** The error handling is inconsistent. Some methods raise exceptions, while others return error messages in the response. A consistent error handling strategy should be implemented, possibly using a custom exception hierarchy and a centralized error handler.

4.  **Lack of Dependency Injection:** The application does not use dependency injection, which makes it harder to test and swap out components. Using a dependency injection framework would improve the modularity of the code.

## Implementation Issues

1.  **Hardcoded Configuration:** Some configuration values are hardcoded in the `config.py` file. These should be externalized to environment variables or a configuration file.

2.  **Security Vulnerabilities:**
    *   **SQL Injection:** The use of raw SQL queries in some places could be vulnerable to SQL injection attacks. Use parameterized queries or an ORM to prevent this.
    *   **Cross-Site Scripting (XSS):** The application does not seem to have any protection against XSS attacks. Sanitize all user input before rendering it in the browser.
    *   **Insecure File Uploads:** The application does not validate the content of uploaded files, which could lead to security vulnerabilities.

3.  **Lack of Unit Tests:** The project lacks a comprehensive suite of unit tests. This makes it difficult to refactor the code and ensure that new changes do not break existing functionality.

4.  **Inefficient Database Queries:** Some database queries are inefficient and could be optimized. For example, fetching all entities at once can be slow if the database is large. Use pagination to fetch data in smaller chunks.

## Celery Usage Review

The Celery implementation has the following issues:

1.  **Incorrect Task State Handling:** In `BackgroundTaskModel.update_status`, the code checks for task states like "PENDING", "SUCCESS", etc. However, it doesn't handle all possible states, and the `else` condition that sets the status to "inprogress" is a catch-all that might not be accurate. The code should handle all possible Celery task states explicitly.

2.  **Blocking Call in Request:** In `EntityModel.get_stream_folder`, the code calls `self.wait_for_m3u8`, which is a blocking call that polls for the existence of a file. This is done within a request, which will block the request until the file is created or the timeout is reached. This is a bad practice and can lead to long request times and server timeouts. The client should poll an endpoint to check the status of the background task.

3.  **Hardcoded Task Name:** The task name `generate_stream_lq` is hardcoded in `BackgroundTaskModel.start_task`. This makes it difficult to add new tasks. The task name should be passed as an argument.

4.  **Lack of Error Handling in Tasks:** The Celery task `exec_generate_stream_lq` does not have any error handling. If the task fails, the client will not be notified, and the task status will not be updated correctly.

## Recommendations

1.  **Refactor to a Service Layer:** Create a service layer to encapsulate the business logic.
2.  **Improve Error Handling:** Implement a consistent error handling strategy.
3.  **Add Unit Tests:** Write a comprehensive suite of unit tests.
4.  **Address Security Vulnerabilities:** Sanitize user input, use parameterized queries, and validate file uploads.
5.  **Improve Celery Integration:** Fix the issues with the Celery implementation, including the blocking calls and error handling.
6.  **Adopt a Consistent Coding Style:** Follow PEP 8 guidelines for Python code.
7.  **Externalize Configuration:** Move all configuration values to environment variables or a configuration file.
8.  **Implement Pagination:** Use pagination for all endpoints that return a list of items.
