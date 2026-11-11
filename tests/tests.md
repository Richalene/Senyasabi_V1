Based on the technical testing report, the system undergoes several categories of tests. Here is the list of test categories along with their details:

### 1. Functional Test Cases (Section 8)

Evaluates whether individual features and user flows operate according to specifications.

* **TC-F-001 (Login):** Tests login with valid credentials.


* **TC-F-002 (Login):** Tests login with an invalid password.


* **TC-F-003 (Registration):** Tests valid account registration.


* **TC-F-004 (Dashboard):** Tests loading of the main dashboard and its areas.


* **TC-F-005 (Lessons):** Tests selecting a lesson by difficulty level.


* **TC-F-006 (Lesson Demonstrator):** Tests playing a sign demonstration via the virtual avatar.


* **TC-F-007 (Sign Recognition):** Tests performing a correct sign to ensure accuracy scoring and positive feedback.


* **TC-F-008 (Sign Recognition):** Tests performing an incorrect sign to ensure appropriate feedback.


* **TC-F-009 (Sign Recognition):** Tests behavior when no hand is in the camera view.


* **TC-F-010 to TC-F-012 (Minigames):** Tests playing full rounds of *SignSprint*, *FingerSpell Quest*, and *Sign Detective*.


* **TC-F-013 (Progress Tracking):** Tests completing a lesson to verify that progress saves and unlocks the next lesson.


* **TC-F-014 (User Statistics):** Tests opening the statistics page to match learner data.


* **TC-F-015 (In-app Store):** Tests spending earned points on cosmetics (marked as not yet implemented).


* **TC-F-016 (Database):** Tests saving and retrieving completed activity records.



### 2. Input Validation Testing (Section 9)

Checks how input fields handle empty, edge-case, and malformed data.

* **IV-001:** Username field left blank on sign-up.


* **IV-002:** Email with invalid formats (e.g., missing parts or symbols).


* **IV-003:** Password with insufficient length.


* **IV-004:** Duplicate entry for username or email.


* **IV-005:** Blank required fields on login or sign-up.


* **IV-006:** Whitespace-only input for username/password.


* **IV-007:** Excessively long passwords (256+ characters).


* **IV-008:** Confirm password mismatch.



### 3. Database Testing (Section 10)

Verifies database operations, structural integrity, and data persistence.

* **DB-001 (INSERT):** Adding records.


* **DB-002 (SELECT):** Retrieving records.


* **DB-003 (UPDATE):** Modifying records.


* **DB-004 (DELETE):** Removing records.


* **DB-005 (Validation):** Preventing duplicate data.


* **DB-006 (Integrity):** Inserting progress records with a non-existent user ID (checking foreign key constraints).


* **DB-007 (Transaction):** Interrupting a save midway to verify data consistency and avoid corruption.


* **DB-008 (Persistence):** Logging out, restarting the app, and verifying saved progress/statistics retention.



### 4. API / External Service Testing (Section 11)

Tests local hardware integrations and libraries (OpenCV, MediaPipe, TensorFlow).

* **API-001:** OpenCV webcam access grant and video feed display.


* **API-002:** OpenCV handling of disconnected or unavailable cameras.


* **API-003:** MediaPipe extraction of 21 hand landmarks from frame.


* **API-004:** Recognition model returning predicted signs and confidence scores.


* **API-005:** Database connection failure handling.


* **API-006:** OpenCV camera permission denied or in-use by another app.


* **API-007:** MediaPipe handling of partial visibility or poor lighting.


* **API-008:** Recognition model handling of missing or unreadable model files.



### 5. Performance Testing (Section 12)

Evaluates system response times, resource consumption, and stability under load.

* **PT-001:** Application start-up time under normal load (Expected: $\le 10$ sec).


* **PT-002:** Recognition response time from frame to feedback (Expected: $\le 2$ sec).


* **PT-003:** Database query speed (Expected: $\le 1$ sec).


* **PT-004:** Concurrent users stability test (5 simultaneous user sessions).


* **PT-005:** Stress test via continuous use for 30 minutes.


* **PT-006:** Frame processing rate (FPS) during live webcam recognition (Expected: $\ge 15$ FPS).


* **PT-007:** CPU and RAM usage on minimum specifications.



### 6. Security Testing (Section 13)

Assesses authentication, authorization, session management, and data protection.

* **SEC-001:** Authentication behavior during invalid logins.


* **SEC-002:** Authorization controls preventing access to other users' data.


* **SEC-003:** Secure password storage checking.


* **SEC-004:** Session termination upon logout.


* **SEC-005:** Input sanitization against malicious input (e.g., SQL injection strings).


* **SEC-006:** Database credential exposure checks.


* **SEC-007:** Safety handling of repeated failed login attempts (lockouts or delays).


* **SEC-008:** Data transmission check for local/remote database connections.



### 7. Compatibility Testing (Section 14)

Evaluates performance across different Windows desktop/laptop device specifications and webcam resolutions (built-in vs. external USB webcams).

### 8. Usability and User Interface (UI) Testing (Section 15)

Evaluates interface layout and user experience criteria:

* **UI-001:** Navigation ease.


* **UI-002:** Text readability.


* **UI-003:** UI element consistency.


* **UI-004:** Clarity of system feedback on signs.


* **UI-005:** Clarity of error messages.


* **UI-006:** UI responsiveness and adaptation to screen sizes.


* **UI-007:** Visibility of the camera preview and hand tracking.



### 9. Regression Testing (Section 19)

Re-evaluates previously passed features after bug fixes and system adjustments:

* **REG-001:** Login.


* **REG-002:** Registration.


* **REG-003:** Database operations.


* **REG-004:** Sign recognition and feedback.


* **REG-005:** Minigames.


* **REG-006:** Progress tracking.