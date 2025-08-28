from flask import Flask, render_template, request, jsonify, session
import os, re, ast, operator as op
import cohere
from datetime import datetime

app = Flask(__name__)
# ---------------- Hardcoded secret key ----------------
app.secret_key = "f3a1b2c4d5e6f7890123456789abcdef0123456789abcdef"

# ---------------- Cohere setup ----------------
COHERE_KEY = "OC7WvIc3z7pwMRiQL3VpcRTmsqcHG1oAVgL7jPOA"
co = cohere.Client(COHERE_KEY) if COHERE_KEY else None

# ---------------- In-memory chat memory ----------------
chat_memory = {}  # {session_id: [{"role":"user","msg":"..."},{"role":"bot","msg":"..."}]}

# ------------- Safe math evaluator -------------
_ALLOWED_OPS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg}

def safe_eval(expr):
    def _eval(node):
        if isinstance(node, ast.Num): return node.n
        if isinstance(node, ast.BinOp): return _ALLOWED_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp): return _ALLOWED_OPS[type(node.op)](_eval(node.operand))
        raise ValueError
    return _eval(ast.parse(expr, mode='eval').body)

# ------------- Fallback tutor -------------
def fallback_tutor(q, subj, diff):
    try:
        if re.match(r'^[0-9\.\+\-\*\/\^\(\) ]+$', q.strip()):
            result = safe_eval(q.replace('^','**'))
            return f"The result of the expression is {result}. Please check your calculations and approach the problem step by step."
    except:
        pass
    return f"In {subj}, it is recommended to carefully analyze the problem, identify known variables, and apply relevant concepts step by step. Break complex problems into smaller sections and solve sequentially."

# ------------- Quiz generator -------------
def generate_quiz(subj, diff):
    subj = subj.lower()
    if subj == "math":
        return {"q":"What is 12 multiplied by 12?","choices":["124","144","122","100"],"ans":1}
    if subj == "physics":
        return {"q":"Which of the following is a unit of force?","choices":["Joule","Newton","Pascal","Watt"],"ans":1}
    if subj == "chemistry":
        return {"q":"What is the pH of a neutral solution at room temperature?","choices":["0","7","14","1"],"ans":1}
    if subj == "english":
        return {"q":"Which sentence is grammatically correct?","choices":["She don't like apples.","They has a car.","He runs every morning.","I goes to school."],"ans":2}
    return {"q":"Which study habit is most effective?","choices":["Cramming","Active recall and spaced practice","Skipping exercises","Multitasking"],"ans":1}

# ------------- Flask routes -------------
@app.route("/")
def index():
    # Ensure session ID exists
    if "id" not in session:
        session["id"] = os.urandom(16).hex()
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    q = data.get("question","")
    subj = data.get("subject","Other")
    diff = data.get("difficulty","Medium")
    timestamp = datetime.now().strftime("%H:%M")

    # Get session ID
    session_id = session.get("id")
    if not session_id:
        session["id"] = os.urandom(16).hex()
        session_id = session["id"]

    # Initialize memory for this session
    if session_id not in chat_memory:
        chat_memory[session_id] = []

    # Append user message
    chat_memory[session_id].append({"role":"user","msg":q})

    # Build conversation history
    history_text = ""
    for m in chat_memory[session_id]:
        history_text += f"{m['role']}: {m['msg']}\n"

    # Generate AI reply
    if co:
        try:
            response = co.chat(
                model="command-r-plus",
                message=f"You are a formal, professional tutor. Subject: {subj}, Difficulty: {diff}.\nConversation so far:\n{history_text}\nRespond clearly, with full sentences, no markdown or asterisks."
            )
            reply = response.text.strip()
        except Exception as e:
            reply = fallback_tutor(q, subj, diff) + f" (Error: {e})"
    else:
        reply = fallback_tutor(q, subj, diff)

    # Append bot reply
    chat_memory[session_id].append({"role":"bot","msg":reply})

    return jsonify({"reply": reply, "time": timestamp})

@app.route("/quiz", methods=["POST"])
def quiz():
    data = request.json
    return jsonify(generate_quiz(data.get("subject","Other"), data.get("difficulty","Easy")))

if __name__ == "__main__":
    app.run(debug=True)

