import os
import json
import fitz
import sqlite3
import time
import random

from flask import Flask, render_template, request,redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from google import genai
from datetime import datetime
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HISTORY_FILE = "history.json"


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "development-secret-key"
)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True) 

client = genai.Client(api_key=GEMINI_API_KEY)
def init_db():

    conn = sqlite3.connect("users.db")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()

    conn.close()
init_db()


def extract_resume_text(file):
    pdf = fitz.open(
        stream=file.read(),
        filetype="pdf"
    )

    text = ""

    for page in pdf:
        text += page.get_text("text") + "\n"

    pdf.close()

    return text.strip()

      
def analyze_resume(resume_text):
    resume_text = resume_text[:12000]

    prompt = f"""
Analyze this resume and return ONLY JSON.

Fields:
score
missing_technical_skills
strengthen
strengths
recommended_roles

Rules:
- score: 0-100
- maximum 5 missing skills
- maximum 4 strengthen points
- maximum 4 strengths
- maximum 4 recommended roles
- Keep every item short.
- No explanations outside JSON.
- No markdown.

Resume:

{resume_text}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    result = response.text.strip()

    # Remove code fences if Gemini adds them
    if result.startswith("```json"):
        result = result[7:]

    elif result.startswith("```"):
        result = result[3:]

    if result.endswith("```"):
        result = result[:-3]

    result = result.strip()

    try:
        return json.loads(result)

    except Exception as e:

        print("JSON ERROR:", e)
        print("GEMINI RESPONSE:", result)

        return {
            "score": "N/A",
            "missing_technical_skills": [],
            "strengthen": [],
            "strengths": [],
            "recommended_roles": []
        }


    

    
    

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect("/")  # ✅ Safely redirects to home page without BuildError!
        return render_template("login.html", error="Invalid email or password.")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        hashed_password = generate_password_hash(
            password
        )

        try:

            conn = sqlite3.connect("users.db")

            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (
                    name,
                    email,
                    hashed_password
                )
            )

            conn.commit()

            conn.close()

            return redirect(
                url_for("login")
            )

        except sqlite3.IntegrityError:

            return render_template(
                "register.html",
                error="Email already registered."
            )

    return render_template("register.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )
@app.route("/")
def home():
    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "index.html",
        user_name=session.get("user_name")
    )


@app.route("/analyze", methods=["POST"])
def analyze():
    resume = request.files.get("resume")

    if not resume:
        return "Please upload a resume."

    if resume.filename == "":
        return "Please select a resume."

    if not resume.filename.lower().endswith(".pdf"):
        return "Only PDF files are supported."

    try:

        print("STEP 1: File received")

        resume_text = extract_resume_text(resume)

        print("STEP 2: Text extracted")
        print("Characters extracted:", len(resume_text))

        if not resume_text:
            return "Could not extract text from this PDF."

        print("STEP 3: Sending to Gemini")

        result = analyze_resume(resume_text)

        print("STEP 4: Gemini analysis completed")

        return render_template(
            "result.html",
            result=result
        )

    except Exception as e:

        print("ANALYSIS ERROR:", e)

        return f"An error occurred while analyzing the resume: {e}"
    


# =========================
# AI INTERVIEW
# =========================

# =========================
# AI INTERVIEW
# =========================

INTERVIEW_ROUNDS = {
    "technical": {
        "name": "Technical Round",
        "questions": 3,
        "duration": 60 * 60
    },

    "aptitude": {
        "name": "Aptitude Round",
        "questions": 5,
        "duration": 20 * 60
    },

    "hr": {
        "name": "HR Interview",
        "questions": 5,
        "duration": 10 * 60
    }
}


# =============================================================
# EXPANDED QUESTION POOL (Randomized on every interview)
# =============================================================
QUESTION_BANK = {
    "technical": [
        {
            "question": "Coding Challenge: Write a function to check if a string is a palindrome, ignoring non-alphanumeric characters. Provide time and space complexity.",
            "keywords": ["isalnum", "lower", "[::-1]", "reverse", "while", "left", "right"],
            "solution": "Python:\ndef is_palindrome(s):\n    c = [ch.lower() for ch in s if ch.isalnum()]\n    return c == c[::-1]\n# Time: O(n), Space: O(n)"
        },
        {
            "question": "Coding Challenge: Given an array of integers `nums` and a `target`, return indices of two numbers that add up to target in O(n) time.",
            "keywords": ["dict", "hash", "{}", "seen", "complement", "target -", "enumerate"],
            "solution": "Python:\ndef two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i\n    return []"
        },
        {
            "question": "System Design: Explain the difference between SQL and NoSQL databases. When would you choose PostgreSQL over MongoDB?",
            "keywords": ["relational", "acid", "schema", "table", "document", "scale", "nosql", "sql"],
            "solution": "Key Points:\n- SQL (PostgreSQL): Structured, ACID transactions, strict schema. Best for financial, billing, e-commerce orders.\n- NoSQL (MongoDB): Document-based, flexible schema, horizontal scaling. Best for real-time analytics, rapid prototyping, dynamic catalogs."
        },
        {
            "question": "Coding Challenge: Write a function to find the maximum subarray sum (Kadane's Algorithm) from a list of integers.",
            "keywords": ["kadane", "max", "current", "sum", "for", "loop", "subarray"],
            "solution": "Python:\ndef max_subarray(nums):\n    max_so_far = current_max = nums[0]\n    for x in nums[1:]:\n        current_max = max(x, current_max + x)\n        max_so_far = max(max_so_far, current_max)\n    return max_so_far\n# Time: O(n), Space: O(1)"
        },
        {
            "question": "Web Architecture: What happens under the hood when you type a URL (like https://google.com) in your browser and press Enter?",
            "keywords": ["dns", "ip", "tcp", "handshake", "tls", "ssl", "http", "get", "server", "render", "html"],
            "solution": "Key Steps:\n1. DNS Lookup resolves domain to IP address.\n2. TCP 3-way handshake and TLS negotiation for HTTPS.\n3. Browser sends HTTP GET request to web server.\n4. Server responds with HTML, CSS, and JS.\n5. Browser engine parses DOM and CSSOM to render the page."
        },
        {
            "question": "Coding Challenge: Write a function to reverse a singly linked list in-place.",
            "keywords": ["prev", "curr", "next", "none", "while", "head", "pointer"],
            "solution": "Python:\ndef reverse_list(head):\n    prev = None\n    curr = head\n    while curr:\n        nxt = curr.next\n        curr.next = prev\n        prev = curr\n        curr = nxt\n    return prev\n# Time: O(n), Space: O(1)"
        },
        {
            "question": "Core Concept: Explain what a RESTful API is, and what idempotency means with respect to HTTP methods (GET, POST, PUT, DELETE).",
            "keywords": ["stateless", "rest", "idempotent", "get", "put", "delete", "post", "resource"],
            "solution": "Key Points:\n- REST is an architectural style based on stateless, client-server communication using standard HTTP methods.\n- Idempotent means making multiple identical requests has the same effect as making a single request (e.g. GET, PUT, DELETE are idempotent; POST is NOT idempotent)."
        }
    ],
    "aptitude": [
        {
            "question": "A train 180 meters long is traveling at a speed of 54 km/h. How many seconds will it take to pass an electric pole?",
            "expected_answers": ["12", "12s", "12 sec", "12 seconds"],
            "solution": "Speed = 54 * (5/18) = 15 m/s. Time = 180 / 15 = 12 seconds."
        },
        {
            "question": "Find the next number in the series: 3, 7, 15, 31, 63, ?",
            "expected_answers": ["127"],
            "solution": "Pattern: (Current * 2) + 1. 63 * 2 + 1 = 127."
        },
        {
            "question": "A shopkeeper buys an article for $400 and sells it for $500. What is his profit percentage?",
            "expected_answers": ["25", "25%", "25 percent"],
            "solution": "Profit = $500 - $400 = $100. Profit % = (100 / 400) * 100 = 25%."
        },
        {
            "question": "Worker A takes 6 days and Worker B takes 12 days to finish a task. Working together, in how many days can they finish?",
            "expected_answers": ["4", "4 days", "4days"],
            "solution": "1/6 + 1/12 = 3/12 = 1/4. Together = 4 days."
        },
        {
            "question": "A standard six-sided die is rolled. What is the probability of rolling a prime number (2, 3, or 5)?",
            "expected_answers": ["1/2", "0.5", "50%", "3/6", "50 percent"],
            "solution": "Prime numbers are {2, 3, 5} = 3 outcomes. Total = 6. Probability = 3/6 = 1/2 or 50%."
        },
        {
            "question": "If 15 pens cost $75, how much will 24 pens cost?",
            "expected_answers": ["120", "$120", "120 dollars"],
            "solution": "Cost per pen = 75 / 15 = $5. Cost of 24 pens = 24 * 5 = $120."
        },
        {
            "question": "Find the missing number in the sequence: 2, 6, 12, 20, 30, ?",
            "expected_answers": ["42"],
            "solution": "Differences: +4, +6, +8, +10, +12. Next number is 30 + 12 = 42."
        },
        {
            "question": "A car travels 150 km in 3 hours. What is its average speed in meters per second (m/s)? (Round to one decimal place)",
            "expected_answers": ["13.9", "13.88", "13.8", "14"],
            "solution": "Speed = 150 / 3 = 50 km/h. Convert to m/s: 50 * (5/18) = 13.88 m/s (or ~13.9 m/s)."
        }
    ],
    "hr": [
        {
            "question": "Tell me about a challenging situation in a team project and how you resolved disagreements or technical roadblocks.",
            "min_words": 15,
            "solution": "STAR Method:\n- Situation & Task: Describe the technical roadblock.\n- Action: Engaged team members, evaluated options objectively with metrics, and reached consensus.\n- Result: Completed project deliverables on schedule."
        },
        {
            "question": "Why are you interested in this position and where do you see your technical trajectory in the next 3 years?",
            "min_words": 15,
            "solution": "Ideal Approach:\n- Align personal goals with company engineering culture.\n- Express ambition to grow into a senior engineer, lead architecture discussions, and mentor others."
        },
        {
            "question": "Describe a scenario where you made a mistake or delivered a task past its initial deadline. How did you communicate this?",
            "min_words": 15,
            "solution": "Ideal Approach:\n- Took prompt ownership without making excuses.\n- Communicated delays to stakeholders early with clear updated timelines and preventative steps taken."
        },
        {
            "question": "How do you handle receiving critical feedback or a tough code review from a senior developer?",
            "min_words": 15,
            "solution": "Ideal Approach:\n- Keep ego aside and view code reviews as a fast learning opportunity.\n- Ask clarifying questions, implement suggestions gracefully, and verify edge cases."
        },
        {
            "question": "Describe a situation where you had to quickly learn a new technology or framework under tight deadlines.",
            "min_words": 15,
            "solution": "Ideal Approach:\n- Focused on official docs, minimal proof-of-concept projects, and building core features first.\n- Asked targeted questions from experienced teammates to avoid getting stuck."
        }
    ]
}


# =============================================================
# RANDOMIZED QUESTION SELECTION FUNCTION
# =============================================================
def get_questions_for_round(round_type):
    """
    Generates fresh, unique questions using Gemini Flash in one fast batch (<2s).
    If API key is missing or offline, immediately falls back to random bank.
    """
    count_map = {"technical": 3, "aptitude": 5, "hr": 3}
    num_to_generate = count_map.get(round_type.lower(), 3)

    # 1. If Gemini API key is configured, generate with Gemini
    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)

            # Strict prompt instructing Gemini to return clean JSON
            prompt = f"""
            You are an expert interviewer. Generate exactly {num_to_generate} unique, realistic {round_type.upper()} interview questions with detailed reference solutions.
            
            Return ONLY a valid JSON array of objects without markdown formatting or code blocks:
            [
              {{
                "question": "Question text here",
                "solution": "Step by step correct solution / code here",
                "keywords": ["keyword1", "keyword2"],
                "expected_answers": ["exact_answer_if_aptitude"]
              }}
            ]
            """

            # gemini-2.5-flash responds in ~1.5 seconds!
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            cleaned_json = response.text.strip().replace("```json", "").replace("```", "").strip()
            ai_questions = json.loads(cleaned_json)

            if isinstance(ai_questions, list) and len(ai_questions) >= num_to_generate:
                print(f"✅ Generated {len(ai_questions)} fresh questions from Gemini!")
                return ai_questions[:num_to_generate]

        except Exception as e:
            print(f"⚠️ Gemini API fallback to local bank due to: {e}")

    # 2. Instant Fallback if offline or without API key
    pool = QUESTION_BANK.get(round_type.lower(), QUESTION_BANK["technical"])
    sample_count = min(num_to_generate, len(pool))
    return random.sample(pool, sample_count)


# =============================================================
# STRICT EVALUATION (Wrong Answers = 0%)
# =============================================================
def evaluate_user_answer(round_type, question_item, user_answer):
    """Strictly grades answers. Wrong answers receive 0%."""
    ans = user_answer.strip().lower()

    # 1. Blank, trivial, or nonsense answers -> 0%
    if len(ans) < 3 or ans in ["no", "idk", "don't know", "skip", "none", "wrong", "abc", "test"]:
        return {
            "is_correct": False,
            "score": 0,
            "feedback": "Incorrect. No valid attempt or solution was provided."
        }

    # 2. APTITUDE ROUND EVALUATION
    if round_type == "aptitude":
        expected = question_item.get("expected_answers", [])
        # Check if any expected correct answer is present in candidate text
        matched = any(exp.lower() in ans for exp in expected)
        if matched:
            return {
                "is_correct": True,
                "score": 100,
                "feedback": "Correct! Your calculation and answer match the expected result."
            }
        else:
            return {
                "is_correct": False,
                "score": 0,  # <-- Strictly 0 for wrong math/logic
                "feedback": "Incorrect answer. Your final numerical answer does not match the solution."
            }

    # 3. TECHNICAL ROUND EVALUATION
    elif round_type == "technical":
        keywords = question_item.get("keywords", [])
        # Count how many essential code keywords/concepts were included
        matched_keywords = [kw for kw in keywords if kw.lower() in ans]

        # Require meaningful length AND at least 2 relevant technical concepts
        if len(matched_keywords) >= 3:
            return {
                "is_correct": True,
                "score": 100,
                "feedback": f"Excellent! Correct implementation using key concepts ({', '.join(matched_keywords[:3])})."
            }
        elif len(matched_keywords) == 2:
            return {
                "is_correct": True,
                "score": 70,
                "feedback": f"Partially correct. Good attempt utilizing ({', '.join(matched_keywords)}), but lacks complete edge-case handling."
            }
        else:
            return {
                "is_correct": False,
                "score": 0,  # <-- Strictly 0 if key logic/code is missing or wrong
                "feedback": "Incorrect. Your code/explanation does not satisfy the required algorithm or time complexity."
            }

    # 4. HR ROUND EVALUATION
    elif round_type == "hr":
        words = len(ans.split())
        min_words = question_item.get("min_words", 15)

        # Check for HR behavioral relevance keywords
        hr_quality_words = ["team", "project", "challenge", "learned", "communication", "solved", "result", "goal", "responsibility", "work"]
        has_hr_context = any(w in ans for w in hr_quality_words)

        if words >= min_words and has_hr_context:
            return {
                "is_correct": True,
                "score": 100,
                "feedback": "Strong response. Shows structured communication, practical experience, and professional maturity."
            }
        else:
            return {
                "is_correct": False,
                "score": 0,  # <-- Strictly 0 if off-topic, gibberish, or too short
                "feedback": "Unsatisfactory response. Answer was either too brief or lacked professional behavioral examples (STAR method)."
            }

    return {"is_correct": False, "score": 0, "feedback": "Incorrect answer."}

# =============================================================
# 3. INTERVIEW ROUTES (Start, Generate, Submit, Results)
# =============================================================
@app.route("/interview")
def interview():
    return render_template("interview.html")


@app.route("/start-interview", methods=["POST"])
def start_interview():
    data = request.get_json() or {}
    round_type = data.get("type", "technical")

    questions = get_questions_for_round(round_type)
    duration = 3600 if round_type == "technical" else (1200 if round_type == "aptitude" else 600)

    session["interview"] = {
        "type": round_type,
        "questions": questions,
        "current_index": 0,
        "end_time": time.time() + duration,
        "answers": []
    }

    return jsonify({
        "success": True,
        "type": round_type,
        "name": round_type.capitalize() + " Interview",
        "questions": len(questions),
        "end_time": session["interview"]["end_time"]
    })


@app.route("/generate-question", methods=["POST"])
def generate_question():
    interview_data = session.get("interview")
    if not interview_data:
        return jsonify({"error": "No active interview session."}), 400

    idx = interview_data["current_index"]
    questions = interview_data.get("questions", [])

    if idx >= len(questions):
        return jsonify({"completed": True})

    current_item = questions[idx]

    return jsonify({
        "question": current_item.get("question", ""),
        "number": idx + 1,
        "total": len(questions)
    })


@app.route("/submit-answer", methods=["POST"])
def submit_answer():
    interview_data = session.get("interview")
    if not interview_data:
        return jsonify({"error": "No active interview session."}), 400

    data = request.get_json() or {}
    user_answer = data.get("answer", "").strip()
    question_text = data.get("question", "")

    idx = interview_data["current_index"]
    questions = interview_data.get("questions", [])
    current_item = questions[idx] if idx < len(questions) else {}

    # Evaluate the candidate answer
    eval_result = evaluate_user_answer(interview_data.get("type", "technical"), current_item, user_answer)

    # Save answer details with feedback and solution
    interview_data["answers"].append({
        "question": question_text,
        "user_answer": user_answer,
        "is_correct": eval_result["is_correct"],
        "score": eval_result["score"],
        "feedback": eval_result["feedback"],
        "solution": current_item.get("solution", "Solution not available."),
        "correct_solution": current_item.get("solution", "Solution not available.")
    })

    interview_data["current_index"] += 1
    session["interview"] = interview_data

    if interview_data["current_index"] >= len(questions):
        return jsonify({"finished": True})

    return jsonify({"success": True})


@app.route("/interview-result")
def interview_result():
    interview_data = session.get("interview", {})
    answers = interview_data.get("answers", [])
    questions = interview_data.get("questions", [])
    total = len(questions) if len(questions) > 0 else len(answers)

    if answers and total > 0:
        total_earned = sum(item.get("score", 0) for item in answers)
        max_possible = total * 100
        percentage = round((total_earned / max_possible) * 100)
    else:
        percentage = 0

    # ✅ SAVE TO PERFORMANCE HISTORY (only if answers exist and not already recorded)
    if answers and not interview_data.get("recorded"):
        save_history_entry({
            "id": int(time.time()),
            "date": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "round": interview_data.get("type", "technical").capitalize(),
            "score": percentage,
            "total_questions": total,
            "correct_answers": sum(1 for a in answers if a.get("is_correct")),
            "status": "Passed" if percentage >= 70 else ("Average" if percentage >= 40 else "Needs Work")
        })
        interview_data["recorded"] = True
        session["interview"] = interview_data

    return render_template(
        "interview_result.html",
        percentage=percentage,
        score=percentage,
        total=total,
        answers=answers,
        interview_name=interview_data.get("type", "Technical").capitalize() + " Round"
    )

@app.route("/terminate-interview", methods=["POST"])
def terminate_interview():
    session.pop("interview", None)
    return jsonify({"success": True})
def load_history():
    """Loads past interview attempts from history.json."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []
def save_history_entry(entry):
    """Saves a completed interview attempt."""
    history = load_history()
    history.insert(0, entry)  # Most recent first
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
@app.route("/history")
def performance_history():
    """Displays user performance history and overall analytics."""
    history = load_history()

    # Calculate overall analytics
    total_tests = len(history)
    avg_score = round(sum(h["score"] for h in history) / total_tests) if total_tests > 0 else 0
    best_score = max((h["score"] for h in history), default=0)

    return render_template(
        "history.html",
        history=history,
        total_tests=total_tests,
        avg_score=avg_score,
        best_score=best_score
    )


@app.route("/clear-history", methods=["POST"])
def clear_history():
    """Resets performance history."""
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    return redirect(url_for("performance_history"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
