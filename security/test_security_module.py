from security_module import sign_evidence, verify_evidence


EVIDENCE_FILE = "evidence.txt"


# -------------------------------------------------
# Step 1: Sign the original evidence
# -------------------------------------------------

evidence_hash, signature = sign_evidence(EVIDENCE_FILE)

print("=== ORIGINAL EVIDENCE ===")
print("SHA-256:", evidence_hash.hex())
print("Signature:", signature.hex())


# -------------------------------------------------
# Step 2: Verify the original evidence
# -------------------------------------------------

valid, current_hash = verify_evidence(
    EVIDENCE_FILE,
    signature
)

print("\n=== VERIFICATION ===")

if valid:
    print("Result: VALID")
else:
    print("Result: INVALID")


# -------------------------------------------------
# Step 3: Modify the evidence
# -------------------------------------------------

with open(EVIDENCE_FILE, "a") as file:
    file.write("\nATTACKER MODIFIED THE EVIDENCE")


# -------------------------------------------------
# Step 4: Verify the modified evidence
# -------------------------------------------------

valid, tampered_hash = verify_evidence(
    EVIDENCE_FILE,
    signature
)

print("\n=== AFTER TAMPERING ===")
print("New SHA-256:", tampered_hash.hex())

if valid:
    print("Result: VALID")
else:
    print("Result: INVALID")
    print("WARNING: Evidence has been modified.")
