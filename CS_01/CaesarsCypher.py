def caesar_cipher(text, shift, mode='encrypt'):
    result = ""

    # If decrypting, just invert the shift
    if mode == 'decrypt':
        shift = -shift

    for char in text:
        if char.isalpha():
            # Handle uppercase letters
            if char.isupper():
                result += chr((ord(char) - 65 + shift) % 26 + 65)
            # Handle lowercase letters
            else:
                result += chr((ord(char) - 97 + shift) % 26 + 97)
        else:
            # Non-alphabet characters remain unchanged
            result += char

    return result


if __name__ == "__main__":
    print("=== Caesar Cipher Tool ===")
    message = input("Enter your message: ")
    shift = int(input("Enter shift value (e.g. 3): "))

    encrypted = caesar_cipher(message, shift, 'encrypt')
    decrypted = caesar_cipher(encrypted, shift, 'decrypt')

    print("\n--- Results ---")
    print(f"Encrypted Message: {encrypted}")
    print(f"Decrypted Message: {decrypted}")
