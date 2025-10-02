import re

def check_password_strength(password):
    # Criteria
    length_error = len(password) < 8
    lowercase_error = re.search(r"[a-z]", password) is None
    uppercase_error = re.search(r"[A-Z]", password) is None
    digit_error = re.search(r"\d", password) is None
    special_char_error = re.search(r"[!@#$%^&*(),.?\":{}|<>]", password) is None

    # Calculate strength
    errors = [length_error, lowercase_error, uppercase_error, digit_error, special_char_error]
    score = 5 - sum(errors)

    # Feedback
    feedback = []
    if length_error:
        feedback.append("Password should be at least 8 characters long.")
    if lowercase_error:
        feedback.append("Add at least one lowercase letter.")
    if uppercase_error:
        feedback.append("Add at least one uppercase letter.")
    if digit_error:
        feedback.append("Include at least one number.")
    if special_char_error:
        feedback.append("Include at least one special character (!,@,#,$, etc.).")

    # Strength rating
    if score == 5:
        strength = "Strong ✅"
    elif 3 <= score < 5:
        strength = "Moderate ⚠️"
    else:
        strength = "Weak ❌"

    return strength, feedback

# Example usage
if __name__ == "__main__":
    pwd = input("Enter a password to check: ")
    strength, feedback = check_password_strength(pwd)
    print(f"\nPassword Strength: {strength}")
    if feedback:
        print("Suggestions:")
        for tip in feedback:
            print(f"- {tip}")
