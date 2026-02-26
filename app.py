# app.py
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify
)
import json
import os
import random
import string
from datetime import datetime, timedelta
from collections import defaultdict
from facenet_pytorch import InceptionResnetV1

app = Flask(__name__)
app.secret_key = "unipay_secret_123"

model = InceptionResnetV1(pretrained='vggface2').eval()

# -----------------------------
# Files (absolute path to avoid path issues)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
TRANSACTIONS_FILE = os.path.join(BASE_DIR, "transactions.json")

# -----------------------------
# Ensure JSON files exist
# -----------------------------
for path, default in [(USERS_FILE, []), (TRANSACTIONS_FILE, [])]:
    if not os.path.exists(path):
        with open(path, "w") as fh:
            json.dump(default, fh, indent=4)

# -----------------------------
# Helpers
# -----------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_transactions():
    if not os.path.exists(TRANSACTIONS_FILE):
        return []
    with open(TRANSACTIONS_FILE, "r") as f:
        try:
            data = json.load(f)
            return data
        except json.JSONDecodeError:
            return []
def save_transactions(transactions):
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(transactions, f, indent=4)

def calculate_rewards(transactions, threshold=5, min_amount=50, discount_per_threshold=25):
    merchant_stats = defaultdict(lambda: {'count':0,'total':0,'points':0,'discount':0})
    
    for t in transactions:
        merchant = t['to_name']  # reward applies per merchant
        merchant_stats[merchant]['count'] += 1
        merchant_stats[merchant]['total'] += t['amount']

    for m, stats in merchant_stats.items():
        stats['points'] = stats['count']
        qualifying_tx = sum(1 for t in transactions if t['to_name']==m and t['amount']>=min_amount)
        stats['discount'] = (qualifying_tx // threshold) * discount_per_threshold

    return merchant_stats.items()

def generate_unique_id(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def generate_txn_id(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def random_starting_balance():
    return round(random.uniform(800.0, 1200.0), 2)

def calculate_discount(transactions, merchant_name, threshold=5, min_amount=50, discount_per_threshold=25):
    count = sum(1 for t in transactions if t['merchant_name'] == merchant_name and t['amount'] >= min_amount)
    discount = (count // threshold) * discount_per_threshold
    return discount
def find_user_by_unique(uid):
    users = load_users()
    return next((u for u in users if str(u.get("unique_id")) == str(uid)), None)
from flask import Flask, render_template
from datetime import datetime

@app.template_filter('datetimeformat')
def datetimeformat(value):
    # Convert YYYY-MM-DD to DD/MM/YYYY
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except:
        return value

# -----------------------------
# Ensure consistent user fields
# -----------------------------
def ensure_user_fields():
    users = load_users()
    updated = False
    for u in users:
        if "bank_linked" not in u:
            u["bank_linked"] = False
            updated = True
        if "pin" not in u:
            u["pin"] = ""
            updated = True
        if "balance" not in u:
            u["balance"] = 0.0
            updated = True
    if updated:
        save_users(users)

ensure_user_fields()

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------
# Auth: signup / login / logout
# -----------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()
        user_type = request.form.get("user_type", "user")  # "user" or "merchant"

        if not all([name, email, phone, password, confirm]):
            flash("All fields are required!", "error")
            return render_template("signup.html")
        if password != confirm:
            flash("Passwords do not match!", "error")
            return render_template("signup.html")

        users = load_users()
        if any(str(u.get("email")) == email for u in users):
            flash("Email already exists!", "error")
            return render_template("signup.html")
        if any(str(u.get("phone")) == phone for u in users):
            flash("Phone already exists!", "error")
            return render_template("signup.html")

        # Generate unique ID based on type
        if user_type == "merchant":
            uid = "M" + ''.join(random.choices(string.ascii_letters + string.digits, k=5))
        else:
            # Normal user: ensure it never starts with 'M'
            while True:
                uid = generate_unique_id()  # your existing function
                if not uid.startswith("M"):
                    break

        users.append({
            "name": name,
            "email": email,
            "phone": phone,
            "password": password,
            "unique_id": uid,
            "balance": 0.0,
            "bank_linked": False,
            "pin": "",
            "user_type": user_type  # store type
        })
        save_users(users)
        flash(f"Account created! Your Unique ID: {uid}", "success")
        return render_template("signup.html", success=True, uid=uid)

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.pop('_flashes', None)
    if request.method == "POST":
        unique_id = request.form.get("unique_id", "").strip()
        password = request.form.get("password", "").strip()

        if not unique_id or not password:
            flash("Both fields are required!", "error")
            return render_template("login.html")

        users = load_users()
        user = next((u for u in users if str(u.get("unique_id")) == str(unique_id) and str(u.get("password")) == str(password)), None)

        if user:
            session["user"] = user["name"]
            session["unique_id"] = user["unique_id"]
            flash("Logged in successfully", "success")
            return redirect(url_for("user_dashboard"))

        flash("Invalid Unique ID or password!", "error")
        return render_template("login.html")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Successfully logged out", "success")
    return redirect(url_for("login", logged_out=1))


# -----------------------------
# Dashboard
# -----------------------------
@app.route("/user_dashboard")
def user_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    user_obj = find_user_by_unique(session["unique_id"])
    balance = user_obj.get("balance", 0.0) if user_obj else 0.0
    return render_template("user_dashboard.html",
                           user=session["user"],
                           unique_id=session["unique_id"],
                           balance=balance)


# -----------------------------
# Link Bank flow: consent -> selectbank -> bankdetails
# -----------------------------
@app.route("/consent", methods=["GET", "POST"])
def consent():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        return redirect(url_for("selectbank"))
    user_obj = find_user_by_unique(session["unique_id"])
    balance = user_obj.get("balance", 0.0) if user_obj else 0.0
    return render_template("consent.html", user=session["user"], balance=balance)

@app.route("/selectbank", methods=["GET", "POST"])
def selectbank():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        selected_bank = request.form.get("bank")
        if not selected_bank:
            flash("Please select a bank.", "error")
            return render_template("selectbank.html", user=session["user"])
        session["selected_bank"] = selected_bank
        return redirect(url_for("bankdetails"))

    banks = ["SBI", "HDFC", "ICICI", "Axis", "PNB", "Canara"]
    return render_template("selectbank.html", user=session["user"], banks=banks)

@app.route("/bankdetails", methods=["GET", "POST"])
def bankdetails():
    if "user" not in session:
        return redirect(url_for("login"))

    # Get bank from query param or session
    bank_from_url = request.args.get("bank")
    if bank_from_url:
        session["selected_bank"] = bank_from_url

    selected_bank = session.get("selected_bank")
    if not selected_bank:
        return redirect(url_for("selectbank"))

    # Bank IFSC prefixes only
    bank_prefixes = {
        "SBI": "SBIN",
        "HDFC": "HDFC",
        "ICICI": "ICIC",
        "Axis": "UTIB",
        "PNB": "PUNB",
        "Canara": "CNRB"
    }
    prefix = bank_prefixes.get(selected_bank, "XXXX")

    if request.method == "POST":
        acc_holder = request.form.get("accHolderName", "").strip()
        phone = request.form.get("phoneNumber", "").strip()
        email = request.form.get("emailId", "").strip()
        acc_number = request.form.get("accNumber", "").strip()
        branch = request.form.get("branchName", "").strip()
        ifsc_suffix = request.form.get("ifscSuffix", "").strip()  # last 6 digits entered by user

        # Validation
        if not all([acc_holder, phone, email, acc_number, branch, ifsc_suffix]):
            return {"success": False, "error": "All fields are required."}
        elif not ifsc_suffix.isdigit() or len(ifsc_suffix) != 6:
            return {"success": False, "error": "IFSC last 6 digits must be numeric."}
        elif not acc_number.isdigit() or not (9 <= len(acc_number) <= 12):
            return {"success": False, "error": "Account number must be 9-12 digits."}
        elif not phone.isdigit() or len(phone) != 10:
            return {"success": False, "error": "Phone number must be 10 digits."}

        # Save to users.json
        full_ifsc = prefix + ifsc_suffix
        users = load_users()
        for u in users:
            if u.get("unique_id") == session["unique_id"]:
                u.update({
                    "bank_linked": True,
                    "bank_name": selected_bank,
                    "ifsc": full_ifsc,
                    "account_number": acc_number,
                    "account_holder": acc_holder,
                    "branch": branch,
                    "phone": phone,
                    "email": email
                })
                if not u.get("balance"):
                    u["balance"] = random_starting_balance()
                save_users(users)
                # Tell frontend bank linked successfully
                return {"success": True}

        return {"success": False, "error": "User not found."}

    # Render template with prefix
    return render_template(
        "bankdetails.html",
        user=session["user"],
        bank_name=selected_bank,
        ifsc_prefix=prefix  # send prefix to template
    )

# -----------------------------
# Set PIN (AJAX or form POST)
# -----------------------------
@app.route("/set_pin", methods=["POST"])
def set_pin():
    if "unique_id" not in session:
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    data = request.form if request.form else (request.get_json() or {})
    pin_parts = [data.get(f"pin{i}", "") for i in range(1, 5)]
    pin = "".join(pin_parts)
    if not pin and isinstance(data, dict) and data.get("pin"):
        pin = str(data.get("pin"))

    if len(pin) != 4 or not pin.isdigit():
        flash("Invalid PIN. Must be 4 digits.", "error")
        return redirect(url_for("bankdetails"))

    users = load_users()
    for u in users:
        if u.get("unique_id") == session["unique_id"]:
            u["pin"] = pin
            save_users(users)
            flash("PIN set successfully!", "success")
            return redirect(url_for("user_dashboard"))  # Redirect to home/dashboard

    flash("User not found.", "error")
    return redirect(url_for("login"))


# -----------------------------
# Send Money (pay by unique id) - template: pay_id.html
# -----------------------------
@app.route("/pay_id", methods=["GET", "POST"])
def pay_id():
    if "user" not in session:
        return redirect(url_for("login"))

    sender_uid = session["unique_id"]
    sender_obj = find_user_by_unique(sender_uid)

    if request.method == "POST":
        recipient_id = request.form.get("recipientId")
        amt_raw = request.form.get("amount")
        note = request.form.get("note", "")

        if not recipient_id or not amt_raw:
            flash("Recipient and amount required", "error")
            return redirect(url_for("pay_id"))

        try:
            amount = float(amt_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Invalid amount", "error")
            return redirect(url_for("pay_id"))

        users = load_users()
        sender = next((u for u in users if u.get("unique_id") == sender_uid), None)
        recipient = next((u for u in users if u.get("unique_id") == recipient_id), None)

        if recipient is None:
            flash("Recipient not found (use their Unique ID)", "error")
            return redirect(url_for("pay_id"))

        if sender.get("balance", 0.0) < amount:
            flash("Insufficient balance", "error")
            return redirect(url_for("pay_id"))

        # Deduct and credit
        sender["balance"] = round(sender["balance"] - amount, 2)
        recipient["balance"] = round(recipient.get("balance", 0.0) + amount, 2)
        save_users(users)

        # Transaction ID
        txn_id = generate_txn_id()

        # Reward: 10% chance
        reward_amount = 0
        if random.random() < 0.1:
            reward_amount = round(random.uniform(1, 50), 2)
            sender["balance"] = round(sender["balance"] + reward_amount, 2)
            save_users(users)

        # Save transaction
        transactions = load_transactions()
        transactions.append({
            "id": txn_id,
            "from": sender_uid,
            "to": recipient_id,
            "to_name": recipient.get("name"),
            "amount": round(amount, 2),
            "note": note,
            "reward": reward_amount,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_transactions(transactions)

        flash(f"Sent ₹{amount:.2f} to {recipient.get('name')} | Transaction ID: {txn_id}", "success")
        if reward_amount > 0:
            flash(f"You won a reward of ₹{reward_amount:.2f}!", "success")

        return redirect(url_for("pay_id"))

    balance = sender_obj.get("balance", 0.0) if sender_obj else 0.0
    return render_template("pay_id.html", user=session["user"], balance=balance)


# -----------------------------
# Scan & Pay placeholder (template: scanpay.html)
# -----------------------------
@app.route("/setup_face", methods=["GET", "POST"])
def setup_face():
    if "unique_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    if request.method == "GET":
        # Just render the page
        return render_template("setup_face.html")

    # POST: receive face data
    data = request.get_json() or {}
    face_data = data.get("face_image")
    if not face_data:
        return jsonify({"success": False, "error": "No image provided"}), 400

    # Save base64 string directly to user's JSON
    users = load_users()
    for u in users:
        if u["unique_id"] == session["unique_id"]:
            u["face_embedding"] = face_data  # store base64 for now
            save_users(users)
            return jsonify({"success": True, "message": "Face saved!"})

    return jsonify({"success": False, "error": "User not found"}), 404
    
@app.route("/verify_face_payment", methods=["POST"])
def verify_face_payment():
    if "user" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.get_json()
    face_data = data.get("face_image")
    if not face_data:
        return jsonify({"success": False, "error": "No image provided"})

    # Convert image to tensor
    header, encoded = face_data.split(",", 1)
    img = Image.open(BytesIO(base64.b64decode(encoded))).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((160,160)),
        transforms.ToTensor(),
        transforms.Normalize([0.5]*3, [0.5]*3)
    ])
    img_tensor = transform(img).unsqueeze(0)
    with torch.no_grad():
        live_embedding = model(img_tensor).squeeze().numpy()

    # Compare with all users
    users = load_users()
    from numpy import linalg as LA
    threshold = 0.9  # cosine similarity threshold (you can tweak)
    for u in users:
        stored_emb = u.get("face_embedding")
        if stored_emb:
            stored_emb = np.array(stored_emb)
            cosine_sim = np.dot(live_embedding, stored_emb) / (LA.norm(live_embedding)*LA.norm(stored_emb))
            if cosine_sim > threshold:
                return jsonify({
                    "success": True,
                    "receiver_id": u["unique_id"],
                    "receiver_name": u["name"]
                })

    return jsonify({"success": False, "error": "Face not recognized. Ensure good lighting and angle."})


@app.route("/scanpay")
def scanpay():
    if "user" not in session:
        return redirect(url_for("login"))
    
    user_obj = find_user_by_unique(session["unique_id"])
    balance = user_obj.get("balance", 0.0) if user_obj else 0.0
    return render_template("scanpay.html", user=session["user"], balance=balance)

@app.route("/verify_pin", methods=["POST"])
def verify_pin():
    if "unique_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    data = request.get_json() or {}
    pin = "".join([data.get(f"pin{i}", "") for i in range(1, 5)])

    if len(pin) != 4 or not pin.isdigit():
        return jsonify({"success": False, "error": "Invalid PIN"}), 400

    users = load_users()
    user = next((u for u in users if u.get("unique_id") == session["unique_id"]), None)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    if user.get("pin") != pin:
        return jsonify({"success": False, "error": "Incorrect PIN"}), 400

    return jsonify({"success": True, "balance": user.get("balance", 0.0)})
# -----------------------------
# Transaction history (template: transaction_history.html)
# -----------------------------
@app.route("/transaction_history")
def transaction_history():
    if "user" not in session:
        return redirect(url_for("login"))
    uid = session["unique_id"]
    transactions = load_transactions()
    relevant = [t for t in transactions if t.get("from") == uid or t.get("to") == uid]
    relevant.sort(key=lambda x: x.get("date", ""), reverse=True)
    return render_template("transaction_history.html", user=session["user"], transactions=relevant, uid=uid)


# -----------------------------
# API: process_payment (used by JS)
# -----------------------------
@app.route("/process_payment", methods=["POST"])
def process_payment():
    # 1️⃣ Ensure user is logged in
    if "unique_id" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 403

    data = request.get_json() or {}
    receiver_id = data.get("receiver_id")
    amount_raw = data.get("amount")
    pin_parts = [data.get(f"pin{i}", "") for i in range(1, 5)]
    pin = "".join(pin_parts)

    # 2️⃣ Face ID scenario
    face_image_data = data.get("face_image")  # base64 image string
    if face_image_data:
        # We will check the captured face against stored face_ids
        users = load_users()
        matched_user = None
        for u in users:
            stored_face = u.get("face_id")
            if stored_face and stored_face == face_image_data:
                matched_user = u
                break

        if not matched_user:
            return jsonify({
                "success": False,
                "message": "Face not recognized. Please ensure proper lighting and angle."
            }), 400
        
        # If face matches, set receiver_id to the matched user's unique_id
        receiver_id = matched_user.get("unique_id")

    # 3️⃣ Validate amount
    try:
        amount = float(amount_raw)
        if amount <= 0:
            raise ValueError
    except:
        return jsonify({"success": False, "message": "Invalid amount"}), 400

    # 4️⃣ Load users and find sender/recipient
    users = load_users()
    sender = next((u for u in users if u.get("unique_id") == session["unique_id"]), None)
    recipient = next((u for u in users if u.get("unique_id") == receiver_id), None)

    if not sender:
        return jsonify({"success": False, "message": "Sender not found"}), 404
    if not recipient:
        return jsonify({"success": False, "message": "Recipient not found"}), 404

    # 5️⃣ Check PIN (skip if Face ID)
    if not face_image_data:
        if len(pin) != 4 or not pin.isdigit():
            return jsonify({"success": False, "message": "Invalid PIN"}), 400
        if sender.get("pin") != pin:
            return jsonify({"success": False, "message": "Incorrect PIN"}), 403

    # 6️⃣ Check balance
    if sender.get("balance", 0.0) < amount:
        return jsonify({"success": False, "message": "Insufficient balance"}), 400

    # 7️⃣ Deduct sender, credit recipient
    sender["balance"] = round(sender["balance"] - amount, 2)
    recipient["balance"] = round(recipient.get("balance", 0.0) + amount, 2)

    # 8️⃣ Optional reward
    reward = 0
    if random.random() < 0.1:
        reward = round(random.uniform(1, 50), 2)
        sender["balance"] += reward

    # 9️⃣ Save users and transactions
    save_users(users)
    txn_id = generate_txn_id()
    transactions = load_transactions()
    transactions.append({
        "id": txn_id,
        "from": sender["unique_id"],
        "from_name": sender["name"],
        "to": recipient["unique_id"],
        "to_name": recipient["name"],
        "amount": round(amount, 2),
        "reward": reward,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_transactions(transactions)

    #  🔟 Return JSON response
    return jsonify({
        "success": True,
        "receiver_name": recipient["name"],
        "payment_id": txn_id,
        "balance": sender["balance"],
        "reward": reward
    })

# -----------------------------
# Rewards / Pending summary placeholder (template: pendingsummary.html)
# ----------------------------

# -----------------------------
# Check Balance (with PIN validation and lockout)
# -----------------------------
@app.route("/check_balance", methods=["GET", "POST"])
def check_balance():
    if "user" not in session:
        return redirect(url_for("login"))

    uid = session["unique_id"]
    user = find_user_by_unique(uid)

    if "pin_attempts" not in session:
        session["pin_attempts"] = 0
    if "lockout_time" not in session:
        session["lockout_time"] = None

    if session.get("lockout_time"):
        lock_until = datetime.fromisoformat(session["lockout_time"])
        now = datetime.now()
        if now < lock_until:
            remaining = int((lock_until - now).total_seconds())
            return render_template("lockout.html", remaining=remaining)
        else:
            session["pin_attempts"] = 0
            session["lockout_time"] = None

    balance = None
    if request.method == "POST":
        pin = "".join([
            request.form.get("pin1", ""),
            request.form.get("pin2", ""),
            request.form.get("pin3", ""),
            request.form.get("pin4", "")
        ])
        if pin == user.get("pin"):
            balance = user.get("balance", 0.0)
            session["pin_attempts"] = 0
        else:
            session["pin_attempts"] += 1
            if session["pin_attempts"] >= 3:
                session["lockout_time"] = (datetime.now() + timedelta(minutes=5)).isoformat()
                flash("Too many attempts. Locked for 5 minutes.", "error")
            else:
                flash("Incorrect PIN. Try again.", "error")

    return render_template("check_balance.html", user=session["user"], balance=balance)

@app.route("/spendingsummary")
def spendingsummary():
    user_id = session.get("unique_id")
    if not user_id:
        return redirect(url_for("login"))

    users = load_users()
    transactions = load_transactions()

    user = next((u for u in users if str(u.get("unique_id")) == str(user_id)), None)
    if not user:
        return redirect(url_for("login"))

    # Merchant → category mapping
    merchant_category_map = {
        "Zuzu": "Food",
        "Kepler": "Stationery",
        "BitsnBites": "Food",
        "ViZa": "Stationery",
    }

    # Filter transactions for this user
    user_transactions = [
        t for t in transactions
        if str(t.get("from")) == str(user_id) or str(t.get("to")) == str(user_id)
    ]

    # Calculate income & expense
    total_income = sum(t.get("amount", 0) for t in user_transactions if str(t.get("to")) == str(user_id))
    total_expense = sum(t.get("amount", 0) for t in user_transactions if str(t.get("from")) == str(user_id))

    # Spending categories (based on merchant)
    category_map = {}
    for t in user_transactions:
        if str(t.get("from")) == str(user_id):  # only count outgoing for categories
            merchant_name = t.get("to_name")
            cat = merchant_category_map.get(merchant_name, "Others")
            category_map[cat] = category_map.get(cat, 0) + t.get("amount", 0)

    # Frequent merchants & rewards
    merchant_map = {}
    for t in user_transactions:
        if str(t.get("from")) == str(user_id):  # only outgoing
            merchant = t.get("to_name")
            merchant_map[merchant] = merchant_map.get(merchant, 0) + t.get("reward", 0)

    return render_template(
        "spendingsummary.html",
        current_balance=user.get("balance", 0),
        total_income=total_income,
        total_expense=total_expense,
        transactions=user_transactions,
        category_map=category_map,
        merchant_map=merchant_map
    )
@app.route('/rewards')
def rewards():
    # Example: get logged-in user's ID
    user_id = session.get('user_acc')  # set this at login
    
    # Load all transactions
    with open('transactions.json') as f:
        all_tx = json.load(f)
    
    # Filter transactions where logged-in user is the sender
    user_transactions = [t for t in all_tx if t.get('from') == user_id]

    # Calculate rewards
    user_merchants = calculate_rewards(user_transactions)
    
    return render_template('rewards.html', merchants=user_merchants)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
