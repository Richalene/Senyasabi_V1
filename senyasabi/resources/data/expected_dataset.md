# Expected Datasets / Lesson Plan
These are the datasets we need to compile for the prototype version of SenyaSabi. These categories and signs are derived from the field tested Filipino Sign Language Video Tutorials disseminated under Regional Memorandum No. 969, s. 2024.

Lessons should ideally be broken up into smaller parts that can be done in ~5 mins. I've grouped these up in a way that I think wouldn't be too overwhelming to learn. 

## Lesson 1: The Manual Alphabet
A, B, C, D, E, F
G, H, I, Y, K, L
M, N, O, P, Q, R
S, T, U, V, W, X
J, Z    ~note: separate cuz these signs need hand movement~

## Lesson 2: Numbers
### One to Five
1, 2, 3, 4, 5
### Six to Ten
6, 7, 8, 9, 10
### Double Digits Pt. 1
11, 12, 13, 14, 15 
### Double Digits Pt. 2
16, 17, 18, 19, 20
### Multiples of 10
30, 40, 50, 60, 70, 80, 90 
### Hundreds 
100, 200, 300, 400, 500, 600, 700, 800, 900, 1000[^1]


## Lesson 3: Family Members
### Family Overview
family, parents, husband, wife
### Immediate Family
father, mother, brother, sister
### Children & Young Family
son, daughter, child, children, baby
### Older Generation
grandfather, grandmother, uncle, auntie
### Same / Younger Generation
cousin, nephew, niece

## Lesson 4: Basic Communication 
### Daily Greetings & Farewells
Good morning, Good afternoon, Good evening, Good night, Goodbye
### Holidays & Celebrations
Happy birthday, Happy anniversary, Happy Valentine's Day, Merry Christmas, Happy New Year, Happy Easter
### Courtesy
Sorry, Please, Excuse Me, Okay, Thank you, Welcome
### Responses & Requests
Yes, No, Maybe, Wait
### Introductions & Small Talk
What is your name?, Nice to meet you, How are you?, I'm fine
### Personal Info Questions
How old are you?, Where do you live?, Where do you study?

## Lesson 5: Days of the Week
Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday

## Lesson 6: Months of the Year
### January to April
January, February, March, April
### May to August
May, June, July, August
### September to December
September, October, November, December

## Lesson 7: Action Words 
### Daily Living
cook, eat, drink, clean, pray, sleep
### Communication
read, write, draw, listen, talk
### Leisure
play, dance, sing, 
### Outdoors & Errands
run, drive, buy, pay, walk, plant

[^1]: only one sign to denote hundred or thousand so I grouped all these numbers in one lesson since it expects the user to already know 1-9 and this just teaches them to add hundred/thousand to the end. could even add 1-9 thousand here.


lessons
db.create_lesson(title, description, parent_module, lesson_order)
db.get_lesson(lesson_id)
db.list_lessons_by_module(module_id)
db.update_lesson(lesson_id, **fields)
db.deactivate_lesson(lesson_id)
db.delete_lesson(lesson_id)

signs
db.create_sign(lesson_id, media_id, sign_translation)
db.get_sign(sign_id)
db.list_signs_by_lesson(lesson_id)
db.update_sign(sign_id, **fields)
db.delete_sign(sign_id)

quizzes
db.create_quiz(module_id, title, passing_score, time_limit_seconds)
db.get_quiz(quiz_id)
db.list_quizzes_by_module(module_id)
db.update_quiz(quiz_id, **fields)
db.delete_quiz(quiz_id)

minigames
db.create_minigame(lesson_id, game_name, game_type, description)
db.get_minigame(minigame_id)
db.list_minigames_by_lesson(lesson_id)
db.update_minigame(minigame_id, **fields)
db.delete_minigame(minigame_id)

module_progress
db.create_module_progress(user_id, module_id)
db.get_module_progress(user_id, module_id)
db.list_module_progress_by_user(user_id)
db.update_module_progress(user_id, module_id, completion_percentage=None, status=None)
db.mark_module_completed(user_id, module_id)
db.delete_module_progress(progress_id)

user_statistics
db.create_user_statistics(user_id)
db.get_user_statistics(user_id)
db.increment_user_statistics(user_id, **deltas)
db.update_user_statistics(user_id, **fields)
db.delete_user_statistics(user_id)

streaks
db.create_streak(user_id)
db.get_streak(user_id)
db.update_streak(user_id, current_streak, longest_streak, last_activity_date)
db.reset_streak(user_id)
db.delete_streak(user_id)

leaderboard
db.create_leaderboard_entry(user_id)
db.get_leaderboard_entry(user_id)
db.list_leaderboard(limit=100)
db.update_leaderboard_entry(user_id, **fields)
db.recalculate_rankings()
db.delete_leaderboard_entry(user_id)

quiz_attempts
db.start_quiz_attempt(user_id, quiz_id)
db.get_quiz_attempt(attempt_id)
db.list_quiz_attempts_by_user(user_id, quiz_id=None)
db.finish_quiz_attempt(attempt_id, score, max_score, percentage, passed)
db.delete_quiz_attempt(attempt_id)

question_responses
db.record_question_response(attempt_id, question_number, user_answer, correct_answer, is_correct, response_time_ms)
db.get_question_responses(attempt_id)
db.delete_question_response(response_id)

minigame_attempts
db.start_minigame_attempt(user_id, minigame_id)
db.get_minigame_attempt(game_attempt_id)
db.list_minigame_attempts_by_user(user_id, minigame_id=None)
db.finish_minigame_attempt(game_attempt_id, score, duration_seconds, accuracy)
db.delete_minigame_attempt(game_attempt_id)

scores
db.record_score(user_id, activity_type, activity_id, score)
db.get_scores_by_user(user_id, activity_type=None)
db.delete_score(score_id)