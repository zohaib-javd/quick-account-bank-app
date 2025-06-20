from pathlib import Path
import json
import random
import streamlit as st

# --------------------------- CONFIG ---------------------------------
DATABASE = "data.json"
st.set_page_config(
    page_title="Zeejay's Quick Account Bank",
    page_icon="💳",
    layout="centered",
)

# ----------------------- DATA LOAD / SAVE ---------------------------
def load_data():
    if Path(DATABASE).exists():
        try:
            content = Path(DATABASE).read_text().strip()
            return json.loads(content) if content else []
        except json.JSONDecodeError:
            pass
    # file missing or broken → start fresh
    Path(DATABASE).write_text("[]")
    return []

def save_data(records):
    Path(DATABASE).write_text(json.dumps(records, indent=4))

data = load_data()

# ----------------------- HELPERS ------------------------------------
def generate_account_number():
    return "".join(random.choices("0123456789", k=9))

def safe_get(user, field, default=""):
    return user[field] if field in user else default

# ----------------------- SIDEBAR MENU -------------------------------
st.title("💳 Zeejay's Quick Account Bank")
action = st.sidebar.radio(
    "Choose an option",
    (
        "Create Account",
        "Deposit Money",
        "Withdraw Money",
        "Show Account Details",
        "Update Account Info",
        "Delete Account",
    ),
)

# ----------------------- CREATE ACCOUNT -----------------------------
if action == "Create Account":
    st.header("📝 Create a New Account")
    name    = st.text_input("Full Name")
    age     = st.number_input("Age", min_value=0, step=1)
    phone   = st.text_input("Phone Number")
    address = st.text_area("Address")
    email   = st.text_input("Email")
    pin     = st.text_input("4-digit PIN", type="password")

    if st.button("Create Account", key="create_btn"):
        if age < 18:
            st.error("You must be at least 18 years old.")
        elif len(pin) != 4 or not pin.isdigit():
            st.error("PIN must be exactly 4 digits (numbers).")
        else:
            acc_no = generate_account_number()
            data.append(
                {
                    "name": name,
                    "age": age,
                    "phone": phone,
                    "address": address,
                    "email": email,
                    "pin": int(pin),
                    "accountNo.": acc_no,
                    "balance": 0,
                }
            )
            save_data(data)
            st.success(
                f"🎉 Account created! Please save your account number: **{acc_no}**"
            )

# ----------------------- DEPOSIT MONEY ------------------------------
if action == "Deposit Money":
    st.header("💰 Deposit Funds")
    acc = st.text_input("Account Number")
    pin = st.text_input("PIN", type="password")
    amt = st.number_input("Amount to Deposit", min_value=0.0, step=1.0)

    if st.button("Deposit", key="deposit_btn"):
        if not pin.isdigit():
            st.error("PIN must be numeric.")
        else:
            user = next(
                (u for u in data if u["accountNo."] == acc and u["pin"] == int(pin)),
                None,
            )
            if not user:
                st.error("Invalid account or PIN.")
            else:
                user["balance"] += amt
                save_data(data)
                st.success("Deposit successful ✔️")

# ----------------------- WITHDRAW MONEY -----------------------------
if action == "Withdraw Money":
    st.header("💸 Withdraw Funds (max 10,000)")
    acc = st.text_input("Account Number")
    pin = st.text_input("PIN", type="password")
    amt = st.number_input("Amount to Withdraw", min_value=0.0, step=1.0)

    if st.button("Withdraw", key="withdraw_btn"):
        if not pin.isdigit():
            st.error("PIN must be numeric.")
        else:
            user = next(
                (u for u in data if u["accountNo."] == acc and u["pin"] == int(pin)),
                None,
            )
            if not user:
                st.error("Invalid account or PIN.")
            elif amt > 10_000:
                st.error("Withdrawal limit is 10 000.")
            elif user["balance"] < amt:
                st.error("Insufficient balance.")
            else:
                user["balance"] -= amt
                save_data(data)
                st.success("Withdrawal successful ✔️")

# ----------------------- SHOW DETAILS -------------------------------
if action == "Show Account Details":
    st.header("📋 Account Details")
    acc = st.text_input("Account Number")
    pin = st.text_input("PIN", type="password")

    if st.button("Show Details", key="details_btn"):
        if not pin.isdigit():
            st.error("PIN must be numeric.")
        else:
            user = next(
                (u for u in data if u["accountNo."] == acc and u["pin"] == int(pin)),
                None,
            )
            if user:
                st.json(user)
            else:
                st.error("Invalid credentials.")

# ----------------------- UPDATE ACCOUNT INFO ------------------------
if action == "Update Account Info":
    st.header("🔄 Update Account Information")

    # Session flags to persist verification state
    if "upd_verified" not in st.session_state:
        st.session_state.upd_verified = False
    if "upd_idx" not in st.session_state:
        st.session_state.upd_idx = None

    acc = st.text_input("Account Number", key="upd_acc")
    pin = st.text_input("Current PIN", type="password", key="upd_pin_orig")

    if st.button("Verify", key="verify_update_btn"):
        if not pin.isdigit():
            st.error("PIN must be numeric.")
            st.session_state.upd_verified = False
        else:
            idx = next(
                (
                    i
                    for i, u in enumerate(data)
                    if u["accountNo."] == acc and u["pin"] == int(pin)
                ),
                None,
            )
            if idx is None:
                st.error("Invalid credentials.")
                st.session_state.upd_verified = False
            else:
                st.session_state.upd_verified = True
                st.session_state.upd_idx = idx
                st.success("Verified! Edit your info below 👇")

    if st.session_state.upd_verified and st.session_state.upd_idx is not None:
        user = data[st.session_state.upd_idx]

        phone   = st.text_input(
            "Phone Number", value=safe_get(user, "phone"), key="new_phone"
        )
        address = st.text_area(
            "Address", value=safe_get(user, "address"), key="new_address"
        )
        email = st.text_input(
            "Email Address", value=user["email"], key="new_email"
        )
        new_pin = st.text_input(
            "New 4-digit PIN (required)", type="password", key="new_pin"
        )

        if st.button("Save Changes", key="save_update_btn"):
            if len(new_pin) != 4 or not new_pin.isdigit():
                st.error("New PIN must be exactly 4 digits.")
            else:
                user["phone"] = phone
                user["address"] = address
                user["email"] = email
                user["pin"] = int(new_pin)
                save_data(data)
                st.success("Account information updated ✅")

                # Reset state so form closes
                st.session_state.upd_verified = False
                st.session_state.upd_idx = None

# ----------------------- DELETE ACCOUNT -----------------------------
if action == "Delete Account":
    st.header("🗑️ Delete Account")
    acc = st.text_input("Account Number")
    pin = st.text_input("PIN", type="password")

    if st.button("Delete Account ❌", key="delete_btn"):
        if not pin.isdigit():
            st.error("PIN must be numeric.")
        else:
            user = next(
                (u for u in data if u["accountNo."] == acc and u["pin"] == int(pin)),
                None,
            )
            if not user:
                st.error("Invalid credentials.")
            else:
                data.remove(user)
                save_data(data)
                st.success("Account deleted.")
